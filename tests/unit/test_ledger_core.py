import asyncio
import hashlib
import pyotp
import pytest

from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.ledger import schemas, services, models
from src.domain.regulatory import models as regulatory_models
from src.infra.database import async_session


@pytest.fixture()
async def db_session():
    async with async_session() as session:
        yield session
        await session.rollback()


async def _cleanup(db: AsyncSession):
    for table in [
        models.Posting,
        models.Transaction,
        models.PixKey,
        models.Account,
        models.BackupCode,
        models.User,
    ]:
        await db.execute(delete(table))
    await db.execute(delete(regulatory_models.KycProfile))
    await db.commit()


def _account_payload(suffix: str):
    return schemas.AccountCreate(
        name=f"User {suffix}",
        cpf=f"12345678{suffix[:3]}",
        email=f"user-{suffix}@example.com",
        password="SenhaForte123",
        account_type="CHECKING",
    )


@pytest.mark.asyncio
async def test_account_create_and_authenticate(db_session: AsyncSession):
    await _cleanup(db_session)
    data = _account_payload("001")
    account = await services.LedgerService.create_account(db_session, data)
    assert account.id is not None

    by_email = await services.LedgerService.authenticate_account(db_session, data.email, data.password)
    assert by_email is not False

    cpf_hash = hashlib.sha256(data.cpf.encode()).hexdigest()
    stmt = select(models.User).where(models.User.cpf_hash == cpf_hash)
    res = await db_session.execute(stmt)
    user = res.scalar_one_or_none()
    assert user is not None

    by_cpf = await services.LedgerService.authenticate_account(db_session, data.cpf, data.password)
    assert by_cpf is not False


@pytest.mark.asyncio
async def test_duplicate_email_rejected(db_session: AsyncSession):
    await _cleanup(db_session)
    data = _account_payload("002")
    await services.LedgerService.create_account(db_session, data)
    with pytest.raises(Exception):
        await services.LedgerService.create_account(db_session, data)


@pytest.mark.asyncio
async def test_transaction_deposit_and_limits(db_session: AsyncSession):
    await _cleanup(db_session)
    data = _account_payload("003")
    account = await services.LedgerService.create_account(db_session, data)

    deposit = schemas.TransactionCreate(
        account_id=account.id,
        amount=100.0,
        type="DEPOSIT",
        idempotency_key="idem-dep-003",
    )
    tx = await services.LedgerService.create_transaction(db_session, deposit, otp=None)
    assert float(tx.amount) == 100.0

    withdraw = schemas.TransactionCreate(
        account_id=account.id,
        amount=2000.0,
        type="WITHDRAW",
        idempotency_key="idem-wd-003",
    )
    with pytest.raises(Exception):
        await services.LedgerService.create_transaction(db_session, withdraw, otp=None)


@pytest.mark.asyncio
async def test_get_balance_fallback_and_statement_filters(db_session: AsyncSession):
    await _cleanup(db_session)
    acc = await services.LedgerService.create_account(db_session, _account_payload("010"))

    acc.balance = 50.0
    await db_session.commit()

    bal = await services.LedgerService.get_balance(db_session, acc.id, use_cache=False)
    assert float(bal) == 50.0

    deposit = schemas.TransactionCreate(
        account_id=acc.id,
        amount=150.0,
        type="DEPOSIT",
        idempotency_key="idem-dep-010",
    )
    await services.LedgerService.create_transaction(db_session, deposit, otp=None)

    statement = await services.LedgerService.get_statement(
        db_session,
        acc.id,
        search="Transacao",
        min_amount=1.0,
        max_amount=200.0,
    )
    assert statement["account_id"] == acc.id
    assert statement["transactions"]


@pytest.mark.asyncio
async def test_validate_step_up_requires_mfa(db_session: AsyncSession):
    await _cleanup(db_session)
    acc = await services.LedgerService.create_account(db_session, _account_payload("011"))
    with pytest.raises(Exception):
        await services.LedgerService.validate_step_up_auth(db_session, acc.id, services.MFA_THRESHOLD_UNITS + 10, otp_code=None)


@pytest.mark.asyncio
async def test_transfer_idempotency(db_session: AsyncSession):
    await _cleanup(db_session)
    acc_from = await services.LedgerService.create_account(db_session, _account_payload("004"))
    acc_to = await services.LedgerService.create_account(db_session, _account_payload("005"))

    deposit = schemas.TransactionCreate(
        account_id=acc_from.id,
        amount=900.0,
        type="DEPOSIT",
        idempotency_key="idem-dep-004",
    )
    await services.LedgerService.create_transaction(db_session, deposit, otp=None)

    transfer = schemas.TransferCreate(
        from_account_id=acc_from.id,
        to_account_id=acc_to.id,
        amount=100.0,
        idempotency_key="idem-tr-004",
        description="Teste",
    )
    first = await services.LedgerService.process_transfer(db_session, transfer, otp=None)
    assert first.id is not None

    second = await services.LedgerService.process_transfer(db_session, transfer, otp=None)
    assert getattr(second, "idempotency_hit", False) is True


@pytest.mark.asyncio
async def test_verify_integrity(db_session: AsyncSession):
    await _cleanup(db_session)
    acc = await services.LedgerService.create_account(db_session, _account_payload("006"))

    deposit = schemas.TransactionCreate(
        account_id=acc.id,
        amount=200.0,
        type="DEPOSIT",
        idempotency_key="idem-dep-006",
    )
    await services.LedgerService.create_transaction(db_session, deposit, otp=None)

    res = await services.LedgerService.verify_integrity(db_session)
    assert res["ok"] is True
    assert res["count"] >= 1


@pytest.mark.asyncio
async def test_mfa_enable_and_validate(db_session: AsyncSession):
    await _cleanup(db_session)
    acc = await services.LedgerService.create_account(db_session, _account_payload("007"))

    totp = pyotp.TOTP(acc.owner.mfa_secret)
    codes = await services.LedgerService.enable_mfa(db_session, acc.id, totp.now())
    assert len(codes) == 5

    is_valid = await services.LedgerService.validate_second_factor(db_session, acc.owner.id, totp.now())
    assert is_valid is True

    backup_ok = await services.LedgerService.validate_second_factor(db_session, acc.owner.id, codes[0])
    assert backup_ok is True


@pytest.mark.asyncio
async def test_pix_key_and_transfer(db_session: AsyncSession):
    await _cleanup(db_session)
    acc_from = await services.LedgerService.create_account(db_session, _account_payload("008"))
    acc_to = await services.LedgerService.create_account(db_session, _account_payload("009"))

    deposit = schemas.TransactionCreate(
        account_id=acc_from.id,
        amount=300.0,
        type="DEPOSIT",
        idempotency_key="idem-dep-008",
    )
    await services.LedgerService.create_transaction(db_session, deposit, otp=None)

    pix_key = schemas.PixKeyCreate(key="user-009@example.com", key_type="EMAIL")
    await services.LedgerService.create_pix_key(db_session, acc_to.id, pix_key)

    pix_transfer = schemas.PixTransferCreate(
        pix_key=pix_key.key,
        amount=50.0,
        idempotency_key="idem-pix-008",
    )
    tx = await services.LedgerService.process_pix_transfer(db_session, pix_transfer, acc_from.id, otp=None)
    assert float(tx.amount) == 50.0


@pytest.mark.asyncio
async def test_integrity_failure_detected(db_session: AsyncSession):
    await _cleanup(db_session)
    acc = await services.LedgerService.create_account(db_session, _account_payload("012"))

    deposit = schemas.TransactionCreate(
        account_id=acc.id,
        amount=100.0,
        type="DEPOSIT",
        idempotency_key="idem-dep-012",
    )
    tx = await services.LedgerService.create_transaction(db_session, deposit, otp=None)
    await db_session.execute(
        text("UPDATE transactions SET record_hash = 'bad' WHERE id = :id"),
        {"id": tx.id},
    )
    await db_session.commit()
    db_session.expire_all()

    res = await services.LedgerService.verify_integrity(db_session)
    assert res["ok"] is False


@pytest.mark.asyncio
async def test_integrity_postings_imbalance_detected(db_session: AsyncSession):
    await _cleanup(db_session)
    acc = await services.LedgerService.create_account(db_session, _account_payload("015"))

    deposit = schemas.TransactionCreate(
        account_id=acc.id,
        amount=50.0,
        type="DEPOSIT",
        idempotency_key="idem-dep-015",
    )
    tx = await services.LedgerService.create_transaction(db_session, deposit, otp=None)

    db_session.add(models.Posting(transaction_id=tx.id, account_id=acc.id, amount=1.0))
    await db_session.commit()
    db_session.expire_all()

    res = await services.LedgerService.verify_integrity(db_session)
    assert res["ok"] is False
    assert res.get("reason") == "POSTINGS_IMBALANCE"


@pytest.mark.asyncio
async def test_partial_failure_rolls_back(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)
    acc = await services.LedgerService.create_account(db_session, _account_payload("016"))

    deposit = schemas.TransactionCreate(
        account_id=acc.id,
        amount=75.0,
        type="DEPOSIT",
        idempotency_key="idem-dep-016",
    )

    original_commit = db_session.commit
    calls = {"n": 0}

    async def boom_commit():
        calls["n"] += 1
        if calls["n"] == 1:
            raise IntegrityError("stmt", {}, Exception("boom"))
        return await original_commit()

    monkeypatch.setattr(db_session, "commit", boom_commit)

    with pytest.raises(IntegrityError):
        await services.LedgerService.create_transaction(db_session, deposit, otp=None)

    res_tx = await db_session.execute(select(models.Transaction))
    res_post = await db_session.execute(select(models.Posting))
    assert res_tx.scalars().all() == []
    assert res_post.scalars().all() == []


@pytest.mark.asyncio
async def test_blocked_account_rejected(db_session: AsyncSession):
    await _cleanup(db_session)
    acc = await services.LedgerService.create_account(db_session, _account_payload("013"))
    acc.status = "BLOCKED"
    await db_session.commit()

    deposit = schemas.TransactionCreate(
        account_id=acc.id,
        amount=10.0,
        type="DEPOSIT",
        idempotency_key="idem-dep-013",
    )
    with pytest.raises(Exception):
        await services.LedgerService.create_transaction(db_session, deposit, otp=None)


@pytest.mark.asyncio
async def test_pix_key_invalid_type(db_session: AsyncSession):
    await _cleanup(db_session)
    acc = await services.LedgerService.create_account(db_session, _account_payload("014"))
    data = schemas.PixKeyCreate(key="chave-invalida", key_type="INVALID")
    with pytest.raises(Exception):
        await services.LedgerService.create_pix_key(db_session, acc.id, data)


def test_schema_validations():
    schemas.AccountCreate(
        name="Teste",
        cpf="12345678901",
        email="teste@example.com",
        password="SenhaForte123",
        account_type="CHECKING",
    )
    with pytest.raises(ValueError):
        schemas.AccountCreate(
            name="Teste",
            cpf="123",
            email="teste2@example.com",
            password="SenhaForte123",
            account_type="CHECKING",
        )
    with pytest.raises(ValueError):
        schemas.AccountCreate(
            name="Teste",
            cpf="12345678901",
            email="teste3@example.com",
            password="123",
            account_type="CHECKING",
        )
    with pytest.raises(ValueError):
        schemas.TransactionCreate(account_id=1, amount=0, type="DEPOSIT", idempotency_key="x")
    with pytest.raises(ValueError):
        schemas.TransactionCreate(account_id=1, amount=100, type="PIX", idempotency_key="x")
    with pytest.raises(ValueError):
        schemas.TransferCreate(from_account_id=1, to_account_id=1, amount=100, idempotency_key="x")


@pytest.mark.asyncio
async def test_idempotency_handler(monkeypatch):
    from src.domain.ledger import idempotency

    class FakeRedis:
        def __init__(self):
            self.store = {}

        async def get(self, key):
            return self.store.get(key)

        async def setex(self, name, time, value):
            self.store[name] = value

    fake = FakeRedis()

    def fake_get_redis():
        return fake

    monkeypatch.setattr(idempotency, "get_redis", fake_get_redis)

    res = await idempotency.IdempotencyHandler.get_cached_response("k1")
    assert res is None

    await idempotency.IdempotencyHandler.save_response("k1", {"ok": True})
    res = await idempotency.IdempotencyHandler.get_cached_response("k1")
    assert res["ok"] is True
