import pyotp
from types import SimpleNamespace
import pytest
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.domain.ledger import models, schemas, services
from src.domain.regulatory import models as regulatory_models
from src.domain.security import models as security_models
from src.domain.settings import models as settings_models
from src.infra.database import async_session
from src.infra import cache as cache_module


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
        regulatory_models.AmlAlert,
        regulatory_models.KycProfile,
        settings_models.LimitConfig,
        security_models.TokenVault,
        models.User,
    ]:
        await db.execute(delete(table))
    await db.commit()


def _account_payload(suffix: str):
    return schemas.AccountCreate(
        name=f"User {suffix}",
        cpf=f"12345678{suffix}",
        email=f"user-{suffix}@example.com",
        password="SenhaForte123",
        account_type="CHECKING",
    )


@pytest.mark.asyncio
async def test_service_helpers_and_kyc(db_session: AsyncSession):
    await _cleanup(db_session)

    assert await services.LedgerService._get_accounts_for_update(db_session, []) == {}
    with pytest.raises(HTTPException):
        services.LedgerService._ensure_account_active(None)

    account = await services.LedgerService.create_account(db_session, _account_payload("101"))
    with pytest.raises(HTTPException) as exc:
        await services.LedgerService._ensure_kyc_for_outbound(
            db_session,
            account.user_id,
            settings.KYC_REQUIRED_THRESHOLD,
        )
    assert exc.value.status_code == 403

    limits = await services.LedgerService._get_user_limits(db_session, account.user_id)
    assert limits.user_id == account.user_id


@pytest.mark.asyncio
async def test_create_account_duplicate_cpf(db_session: AsyncSession):
    await _cleanup(db_session)

    data = _account_payload("102")
    await services.LedgerService.create_account(db_session, data)
    data_dup = schemas.AccountCreate(
        name="User Dup",
        cpf=data.cpf,
        email="dup-102@example.com",
        password="SenhaForte123",
        account_type="CHECKING",
    )
    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.create_account(db_session, data_dup)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_account_integrity_error(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    async def boom(*args, **kwargs):
        raise IntegrityError("stmt", {}, Exception("boom"))

    async def fake_tokenize(*args, **kwargs):
        return "tok"

    monkeypatch.setattr("src.domain.security.tokenization.TokenizationService.tokenize", fake_tokenize)
    monkeypatch.setattr(db_session, "flush", boom)
    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.create_account(db_session, _account_payload("103"))
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_account_number_generation_failure(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    account = await services.LedgerService.create_account(db_session, _account_payload("104"))
    account.account_number = "1234-1234"
    await db_session.commit()

    monkeypatch.setattr(services.random, "randint", lambda *args, **kwargs: 1234)
    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.create_account(db_session, _account_payload("105"))
    assert exc.value.status_code == 500


@pytest.mark.asyncio
async def test_create_account_kyc_add_failure(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    original_add = db_session.add

    def add_wrapper(obj):
        if isinstance(obj, regulatory_models.KycProfile):
            raise RuntimeError("boom")
        return original_add(obj)

    monkeypatch.setattr(db_session, "add", add_wrapper)
    account = await services.LedgerService.create_account(db_session, _account_payload("106"))
    assert account.id is not None


@pytest.mark.asyncio
async def test_authenticate_account_paths(db_session: AsyncSession):
    await _cleanup(db_session)

    account = await services.LedgerService.create_account(db_session, _account_payload("107"))
    by_id = await services.LedgerService.authenticate_account(
        db_session, str(account.id), "SenhaForte123"
    )
    assert by_id is not False

    wrong = await services.LedgerService.authenticate_account(
        db_session, account.owner.email, "SenhaErrada"
    )
    assert wrong is False

    account.status = "BLOCKED"
    await db_session.commit()
    blocked = await services.LedgerService.authenticate_account(
        db_session, account.owner.email, "SenhaForte123"
    )
    assert blocked is False


@pytest.mark.asyncio
async def test_get_transaction_and_list_accounts(db_session: AsyncSession):
    await _cleanup(db_session)

    account = await services.LedgerService.create_account(db_session, _account_payload("108"))
    deposit = schemas.TransactionCreate(
        account_id=account.id,
        amount=100.0,
        type="DEPOSIT",
        idempotency_key="idem-gt-108",
    )
    tx = await services.LedgerService.create_transaction(db_session, deposit, otp=None)

    found = await services.LedgerService.get_transaction_by_id(db_session, tx.id)
    assert found is not None

    accounts = await services.LedgerService.list_accounts(db_session, account.owner.id)
    assert accounts


@pytest.mark.asyncio
async def test_enable_mfa_errors_and_uri(db_session: AsyncSession):
    await _cleanup(db_session)

    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.enable_mfa(db_session, 999, "123456")
    assert exc.value.status_code == 404

    account = await services.LedgerService.create_account(db_session, _account_payload("109"))
    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.enable_mfa(db_session, account.id, "000000")
    assert exc.value.status_code == 400

    uri = services.LedgerService.get_mfa_uri("user@example.com", pyotp.random_base32())
    assert "otpauth://" in uri


@pytest.mark.asyncio
async def test_validate_second_factor_branches(db_session: AsyncSession):
    await _cleanup(db_session)

    ok = await services.LedgerService.validate_second_factor(db_session, 999, "123456")
    assert ok is True

    account = await services.LedgerService.create_account(db_session, _account_payload("110"))
    account.owner.mfa_enabled = True
    account.owner.mfa_secret = pyotp.random_base32()
    await db_session.commit()

    invalid = await services.LedgerService.validate_second_factor(db_session, account.owner.id, "000000")
    assert invalid is False


@pytest.mark.asyncio
async def test_step_up_auth_requires_mfa_and_invalid(db_session: AsyncSession):
    await _cleanup(db_session)

    account = await services.LedgerService.create_account(db_session, _account_payload("111"))
    account.owner.mfa_enabled = True
    account.owner.mfa_secret = pyotp.random_base32()
    await db_session.commit()

    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.validate_step_up_auth(
            db_session, account.id, services.MFA_THRESHOLD_UNITS + 1, otp_code=None
        )
    assert exc.value.status_code == 401

    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.validate_step_up_auth(
            db_session, account.id, services.MFA_THRESHOLD_UNITS + 1, otp_code="000000"
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_idempotency_and_balance_cache(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    async def fake_get_value(key: str):
        return "cached"

    async def fake_set_value(key: str, value: str, expire_in_seconds: int = 60):
        return None

    monkeypatch.setattr(cache_module.cache, "get_value", fake_get_value)
    monkeypatch.setattr(cache_module.cache, "set_value", fake_set_value)

    hit = await services.LedgerService.check_idempotency("a", "b")
    assert hit is True

    async def fake_get_balance(key: str):
        return "42.5"

    monkeypatch.setattr(cache_module.cache, "get_value", fake_get_balance)
    account = await services.LedgerService.create_account(db_session, _account_payload("112"))
    bal = await services.LedgerService.get_balance(db_session, account.id, use_cache=True)
    assert bal == 42.5


@pytest.mark.asyncio
async def test_create_transaction_idempotency_existing(db_session: AsyncSession):
    await _cleanup(db_session)

    account = await services.LedgerService.create_account(db_session, _account_payload("113"))
    deposit = schemas.TransactionCreate(
        account_id=account.id,
        amount=100.0,
        type="DEPOSIT",
        idempotency_key="idem-ct-113",
    )
    await services.LedgerService.create_transaction(db_session, deposit, otp=None)
    existing = await services.LedgerService.create_transaction(db_session, deposit, otp=None)
    assert getattr(existing, "idempotency_hit", False) is True


@pytest.mark.asyncio
async def test_create_transaction_check_idempotency_exception(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    async def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(services.LedgerService, "check_idempotency", boom)
    account = await services.LedgerService.create_account(db_session, _account_payload("114"))
    deposit = schemas.TransactionCreate(
        account_id=account.id,
        amount=100.0,
        type="DEPOSIT",
        idempotency_key="idem-ct-114",
    )
    tx = await services.LedgerService.create_transaction(db_session, deposit, otp=None)
    assert tx.id is not None


@pytest.mark.asyncio
async def test_create_transaction_idem_hit_without_existing(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    async def always_true(*args, **kwargs):
        return True

    async def no_existing(*args, **kwargs):
        return None

    monkeypatch.setattr(services.LedgerService, "check_idempotency", always_true)
    monkeypatch.setattr(services.LedgerService, "_find_transaction_by_idempotency", no_existing)

    account = await services.LedgerService.create_account(db_session, _account_payload("115"))
    deposit = schemas.TransactionCreate(
        account_id=account.id,
        amount=100.0,
        type="DEPOSIT",
        idempotency_key="idem-ct-115",
    )
    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.create_transaction(db_session, deposit, otp=None)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_create_transaction_idem_hit_with_existing(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    calls = {"n": 0}
    existing = models.Transaction(id=1)

    async def always_true(*args, **kwargs):
        return True

    async def fake_find(*args, **kwargs):
        calls["n"] += 1
        return None if calls["n"] == 1 else existing

    monkeypatch.setattr(services.LedgerService, "check_idempotency", always_true)
    monkeypatch.setattr(services.LedgerService, "_find_transaction_by_idempotency", fake_find)

    account = await services.LedgerService.create_account(db_session, _account_payload("135"))
    deposit = schemas.TransactionCreate(
        account_id=account.id,
        amount=100.0,
        type="DEPOSIT",
        idempotency_key="idem-ct-115b",
    )
    tx = await services.LedgerService.create_transaction(db_session, deposit, otp=None)
    assert tx is existing
    assert getattr(tx, "idempotency_hit", False) is True


@pytest.mark.asyncio
async def test_create_transaction_fraud_context_requires_otp(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    class FakeFraudEngine:
        @staticmethod
        async def evaluate(*args, **kwargs):
            return {"action": "VERIFY"}

    monkeypatch.setattr("src.domain.fraud.engine.FraudEngine", FakeFraudEngine)
    account = await services.LedgerService.create_account(db_session, _account_payload("116"))
    deposit = schemas.TransactionCreate(
        account_id=account.id,
        amount=100.0,
        type="DEPOSIT",
        idempotency_key="idem-ct-116",
    )
    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.create_transaction(
            db_session,
            deposit,
            otp=None,
            fraud_context={"ip": "1.1.1.1", "user_agent": "ua", "device_fingerprint": "x"},
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_create_transaction_withdraw_paths(db_session: AsyncSession):
    await _cleanup(db_session)

    account = await services.LedgerService.create_account(db_session, _account_payload("117"))
    withdraw = schemas.TransactionCreate(
        account_id=account.id,
        amount=10.0,
        type="WITHDRAW",
        idempotency_key="idem-ct-117",
    )
    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.create_transaction(db_session, withdraw, otp=None)
    assert exc.value.status_code == 422

    deposit = schemas.TransactionCreate(
        account_id=account.id,
        amount=500.0,
        type="DEPOSIT",
        idempotency_key="idem-ct-117-dep",
    )
    await services.LedgerService.create_transaction(db_session, deposit, otp=None)
    withdraw_ok = schemas.TransactionCreate(
        account_id=account.id,
        amount=100.0,
        type="WITHDRAW",
        idempotency_key="idem-ct-117-wd",
    )
    tx = await services.LedgerService.create_transaction(db_session, withdraw_ok, otp=None)
    assert tx.id is not None


@pytest.mark.asyncio
async def test_create_transaction_integrity_error(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    account = await services.LedgerService.create_account(db_session, _account_payload("118"))
    deposit = schemas.TransactionCreate(
        account_id=account.id,
        amount=100.0,
        type="DEPOSIT",
        idempotency_key="idem-ct-118",
    )

    async def boom():
        raise IntegrityError("stmt", {}, Exception("boom"))

    calls = {"n": 0}

    async def fake_find(*args, **kwargs):
        calls["n"] += 1
        return None if calls["n"] == 1 else models.Transaction(id=1)

    monkeypatch.setattr(db_session, "commit", boom)
    monkeypatch.setattr(services.LedgerService, "_find_transaction_by_idempotency", fake_find)

    tx = await services.LedgerService.create_transaction(db_session, deposit, otp=None)
    assert getattr(tx, "idempotency_hit", False) is True


@pytest.mark.asyncio
async def test_create_transaction_integrity_error_raises(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    account = await services.LedgerService.create_account(db_session, _account_payload("118b"))
    deposit = schemas.TransactionCreate(
        account_id=account.id,
        amount=100.0,
        type="DEPOSIT",
        idempotency_key="idem-ct-118b",
    )

    async def boom():
        raise IntegrityError("stmt", {}, Exception("boom"))

    async def fake_find(*args, **kwargs):
        return None

    monkeypatch.setattr(db_session, "commit", boom)
    monkeypatch.setattr(services.LedgerService, "_find_transaction_by_idempotency", fake_find)

    with pytest.raises(IntegrityError):
        await services.LedgerService.create_transaction(db_session, deposit, otp=None)


@pytest.mark.asyncio
async def test_create_transaction_aml_alert(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    called = {"ok": False}

    async def fake_alert(*args, **kwargs):
        called["ok"] = True

    monkeypatch.setattr("src.domain.regulatory.services.RegulatoryService.create_aml_alert", fake_alert)
    account = await services.LedgerService.create_account(db_session, _account_payload("119"))
    account.owner.mfa_enabled = True
    account.owner.mfa_secret = pyotp.random_base32()
    await db_session.commit()

    otp = pyotp.TOTP(account.owner.mfa_secret).now()
    deposit = schemas.TransactionCreate(
        account_id=account.id,
        amount=settings.AML_LARGE_TX_THRESHOLD,
        type="DEPOSIT",
        idempotency_key="idem-ct-119",
    )
    await services.LedgerService.create_transaction(db_session, deposit, otp=otp)
    assert called["ok"] is True


@pytest.mark.asyncio
async def test_process_transfer_branches(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    acc_from = await services.LedgerService.create_account(db_session, _account_payload("120"))
    acc_to = await services.LedgerService.create_account(db_session, _account_payload("121"))

    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.process_transfer(
            db_session,
            SimpleNamespace(
                from_account_id=acc_from.id,
                to_account_id=acc_from.id,
                amount=10.0,
                idempotency_key="idem-pt-120",
            ),
            otp=None,
        )
    assert exc.value.status_code == 400

    async def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(services.LedgerService, "check_idempotency", boom)
    deposit = schemas.TransactionCreate(
        account_id=acc_from.id,
        amount=200.0,
        type="DEPOSIT",
        idempotency_key="idem-pt-120-dep",
    )
    await services.LedgerService.create_transaction(db_session, deposit, otp=None)

    transfer = schemas.TransferCreate(
        from_account_id=acc_from.id,
        to_account_id=acc_to.id,
        amount=10.0,
        idempotency_key="idem-pt-120-ok",
    )
    tx = await services.LedgerService.process_transfer(db_session, transfer, otp=None)
    assert tx.id is not None


@pytest.mark.asyncio
async def test_process_transfer_idem_hit_without_existing(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    async def always_true(*args, **kwargs):
        return True

    async def no_existing(*args, **kwargs):
        return None

    monkeypatch.setattr(services.LedgerService, "check_idempotency", always_true)
    monkeypatch.setattr(services.LedgerService, "_find_transaction_by_idempotency", no_existing)

    acc_from = await services.LedgerService.create_account(db_session, _account_payload("122"))
    acc_to = await services.LedgerService.create_account(db_session, _account_payload("123"))
    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.process_transfer(
            db_session,
            schemas.TransferCreate(
                from_account_id=acc_from.id,
                to_account_id=acc_to.id,
                amount=10.0,
                idempotency_key="idem-pt-122",
            ),
            otp=None,
        )
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_process_transfer_idem_hit_with_existing(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    calls = {"n": 0}
    existing = models.Transaction(id=1)

    async def always_true(*args, **kwargs):
        return True

    async def fake_find(*args, **kwargs):
        calls["n"] += 1
        return None if calls["n"] == 1 else existing

    monkeypatch.setattr(services.LedgerService, "check_idempotency", always_true)
    monkeypatch.setattr(services.LedgerService, "_find_transaction_by_idempotency", fake_find)

    acc_from = await services.LedgerService.create_account(db_session, _account_payload("136"))
    acc_to = await services.LedgerService.create_account(db_session, _account_payload("137"))
    transfer = schemas.TransferCreate(
        from_account_id=acc_from.id,
        to_account_id=acc_to.id,
        amount=10.0,
        idempotency_key="idem-pt-122b",
    )
    tx = await services.LedgerService.process_transfer(db_session, transfer, otp=None)
    assert tx is existing
    assert getattr(tx, "idempotency_hit", False) is True


@pytest.mark.asyncio
async def test_process_transfer_fraud_and_limits(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    acc_from = await services.LedgerService.create_account(db_session, _account_payload("124"))
    acc_to = await services.LedgerService.create_account(db_session, _account_payload("125"))

    class FakeFraudEngine:
        @staticmethod
        async def evaluate(*args, **kwargs):
            return {"action": "VERIFY"}

    monkeypatch.setattr("src.domain.fraud.engine.FraudEngine", FakeFraudEngine)
    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.process_transfer(
            db_session,
            schemas.TransferCreate(
                from_account_id=acc_from.id,
                to_account_id=acc_to.id,
                amount=10.0,
                idempotency_key="idem-pt-124",
            ),
            otp=None,
            fraud_context={"ip": "1.1.1.1", "user_agent": "ua", "device_fingerprint": "x"},
        )
    assert exc.value.status_code == 401

    limit = settings_models.LimitConfig(user_id=acc_from.user_id, ted_limit=1.0)
    db_session.add(limit)
    await db_session.commit()
    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.process_transfer(
            db_session,
            schemas.TransferCreate(
                from_account_id=acc_from.id,
                to_account_id=acc_to.id,
                amount=10.0,
                idempotency_key="idem-pt-124-lim",
            ),
            otp=None,
        )
    assert exc.value.status_code == 422

    limit.ted_limit = 1000.0
    await db_session.commit()
    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.process_transfer(
            db_session,
            schemas.TransferCreate(
                from_account_id=acc_from.id,
                to_account_id=acc_to.id,
                amount=500,
                idempotency_key="idem-pt-124-bal",
            ),
            otp=None,
        )
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_process_transfer_integrity_and_aml(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    acc_from = await services.LedgerService.create_account(db_session, _account_payload("126"))
    acc_to = await services.LedgerService.create_account(db_session, _account_payload("127"))

    deposit = schemas.TransactionCreate(
        account_id=acc_from.id,
        amount=200.0,
        type="DEPOSIT",
        idempotency_key="idem-pt-126-dep",
    )
    await services.LedgerService.create_transaction(db_session, deposit, otp=None)

    limits = await services.LedgerService._get_user_limits(db_session, acc_from.user_id)
    limits.ted_limit = 1000.0
    await db_session.commit()

    async def boom():
        raise IntegrityError("stmt", {}, Exception("boom"))

    calls = {"n": 0}

    async def fake_find(*args, **kwargs):
        calls["n"] += 1
        return None if calls["n"] == 1 else models.Transaction(id=1)

    monkeypatch.setattr(db_session, "commit", boom)
    monkeypatch.setattr(services.LedgerService, "_find_transaction_by_idempotency", fake_find)

    tx = await services.LedgerService.process_transfer(
        db_session,
        schemas.TransferCreate(
            from_account_id=acc_from.id,
            to_account_id=acc_to.id,
            amount=10.0,
            idempotency_key="idem-pt-126",
        ),
        otp=None,
    )
    assert getattr(tx, "idempotency_hit", False) is True


@pytest.mark.asyncio
async def test_process_transfer_integrity_error_raises(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    acc_from = await services.LedgerService.create_account(db_session, _account_payload("126b"))
    acc_to = await services.LedgerService.create_account(db_session, _account_payload("127b"))
    deposit = schemas.TransactionCreate(
        account_id=acc_from.id,
        amount=200.0,
        type="DEPOSIT",
        idempotency_key="idem-pt-126b-dep",
    )
    await services.LedgerService.create_transaction(db_session, deposit, otp=None)

    limits = await services.LedgerService._get_user_limits(db_session, acc_from.user_id)
    limits.ted_limit = 1000.0
    await db_session.commit()

    async def boom():
        raise IntegrityError("stmt", {}, Exception("boom"))

    async def fake_find(*args, **kwargs):
        return None

    monkeypatch.setattr(db_session, "commit", boom)
    monkeypatch.setattr(services.LedgerService, "_find_transaction_by_idempotency", fake_find)

    with pytest.raises(IntegrityError):
        await services.LedgerService.process_transfer(
            db_session,
            schemas.TransferCreate(
                from_account_id=acc_from.id,
                to_account_id=acc_to.id,
                amount=10.0,
                idempotency_key="idem-pt-126b",
            ),
            otp=None,
        )


@pytest.mark.asyncio
async def test_process_transfer_aml_alert(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    called = {"ok": False}

    async def fake_alert(*args, **kwargs):
        called["ok"] = True

    monkeypatch.setattr("src.domain.regulatory.services.RegulatoryService.create_aml_alert", fake_alert)

    acc_from = await services.LedgerService.create_account(db_session, _account_payload("128"))
    acc_to = await services.LedgerService.create_account(db_session, _account_payload("129"))
    acc_from.owner.mfa_enabled = True
    acc_from.owner.mfa_secret = pyotp.random_base32()
    await db_session.commit()

    stmt = select(regulatory_models.KycProfile).where(regulatory_models.KycProfile.user_id == acc_from.user_id)
    res = await db_session.execute(stmt)
    profile = res.scalar_one_or_none()
    profile.status = "VERIFIED"
    await db_session.commit()

    deposit = schemas.TransactionCreate(
        account_id=acc_from.id,
        amount=settings.AML_LARGE_TX_THRESHOLD,
        type="DEPOSIT",
        idempotency_key="idem-pt-128-dep",
    )
    otp = pyotp.TOTP(acc_from.owner.mfa_secret).now()
    await services.LedgerService.create_transaction(db_session, deposit, otp=otp)

    called["ok"] = False

    limit = await services.LedgerService._get_user_limits(db_session, acc_from.user_id)
    limit.ted_limit = settings.AML_LARGE_TX_THRESHOLD * 2
    await db_session.commit()

    transfer = schemas.TransferCreate(
        from_account_id=acc_from.id,
        to_account_id=acc_to.id,
        amount=settings.AML_LARGE_TX_THRESHOLD,
        idempotency_key="idem-pt-128",
    )
    otp = pyotp.TOTP(acc_from.owner.mfa_secret).now()
    await services.LedgerService.process_transfer(db_session, transfer, otp=otp)
    assert called["ok"] is True


@pytest.mark.asyncio
async def test_get_statement_filters(db_session: AsyncSession):
    await _cleanup(db_session)

    account = await services.LedgerService.create_account(db_session, _account_payload("130"))
    deposit = schemas.TransactionCreate(
        account_id=account.id,
        amount=100.0,
        type="DEPOSIT",
        idempotency_key="idem-st-130",
    )
    await services.LedgerService.create_transaction(db_session, deposit, otp=None)

    start = (datetime.utcnow() - timedelta(days=1)).isoformat()
    end = (datetime.utcnow() + timedelta(days=1)).isoformat()
    statement = await services.LedgerService.get_statement(
        db_session,
        account.id,
        start_date=start,
        end_date=end,
        tx_type="DEPOSIT",
    )
    assert statement["transactions"]


@pytest.mark.asyncio
async def test_pix_key_duplicate_and_transfer_paths(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    acc_from = await services.LedgerService.create_account(db_session, _account_payload("131"))
    acc_to = await services.LedgerService.create_account(db_session, _account_payload("132"))

    pix_key = schemas.PixKeyCreate(key="user-132@example.com", key_type="EMAIL")
    await services.LedgerService.create_pix_key(db_session, acc_to.id, pix_key)
    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.create_pix_key(db_session, acc_to.id, pix_key)
    assert exc.value.status_code == 400

    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.process_pix_transfer(
            db_session,
            schemas.PixTransferCreate(pix_key="missing@example.com", amount=10.0, idempotency_key="idem-px-131"),
            acc_from.id,
            otp=None,
        )
    assert exc.value.status_code == 404

    class FakeFraudEngine:
        @staticmethod
        async def evaluate(*args, **kwargs):
            return {"action": "VERIFY"}

    monkeypatch.setattr("src.domain.fraud.engine.FraudEngine", FakeFraudEngine)
    with pytest.raises(HTTPException) as exc:
        await services.LedgerService.process_pix_transfer(
            db_session,
            schemas.PixTransferCreate(pix_key=pix_key.key, amount=10.0, idempotency_key="idem-px-131-f"),
            acc_from.id,
            otp=None,
            fraud_context={"ip": "1.1.1.1", "user_agent": "ua", "device_fingerprint": "x"},
        )
    assert exc.value.status_code == 401

    deposit = schemas.TransactionCreate(
        account_id=acc_from.id,
        amount=200.0,
        type="DEPOSIT",
        idempotency_key="idem-px-131-dep",
    )
    await services.LedgerService.create_transaction(db_session, deposit, otp=None)
    tx = await services.LedgerService.process_pix_transfer(
        db_session,
        schemas.PixTransferCreate(pix_key=pix_key.key, amount=10.0, idempotency_key="idem-px-131-ok"),
        acc_from.id,
        otp=None,
    )
    assert tx.id is not None


@pytest.mark.asyncio
async def test_process_pix_transfer_success_coverage(db_session: AsyncSession, monkeypatch):
    await _cleanup(db_session)

    acc_from = await services.LedgerService.create_account(db_session, _account_payload("134"))
    acc_to = await services.LedgerService.create_account(db_session, _account_payload("135"))
    pix_key = schemas.PixKeyCreate(key="user-135@example.com", key_type="EMAIL")
    await services.LedgerService.create_pix_key(db_session, acc_to.id, pix_key)

    called = {"ok": False}

    async def fake_transfer(*args, **kwargs):
        called["ok"] = True
        return models.Transaction(id=1)

    async def fake_enforce_limits(*args, **kwargs):
        return None

    monkeypatch.setattr(services.LedgerService, "process_transfer", fake_transfer)
    monkeypatch.setattr("src.domain.pix.services.PixService._enforce_limits", fake_enforce_limits)

    tx = await services.LedgerService.process_pix_transfer(
        db_session,
        schemas.PixTransferCreate(pix_key=pix_key.key, amount=10.0, idempotency_key="idem-px-134"),
        acc_from.id,
        otp=None,
    )
    assert called["ok"] is True
    assert tx.id == 1


def test_schema_validation_edges():
    with pytest.raises(ValueError):
        schemas.AccountCreate(
            name="User",
            cpf="12345678901",
            email="user@example.com",
            password="x" * 100,
            account_type="CHECKING",
        )
    with pytest.raises(ValueError):
        schemas.AccountCreate(
            name="User",
            cpf="12345678901",
            email="user2@example.com",
            password="SenhaForte123",
            account_type="UNKNOWN",
        )
    with pytest.raises(ValueError):
        schemas.TransactionCreate(account_id=1, amount=1, type="DEPOSIT", idempotency_key=" ")
    with pytest.raises(ValueError):
        schemas.TransferCreate(from_account_id=1, to_account_id=2, amount=1, idempotency_key=" ")
    with pytest.raises(ValueError):
        schemas.TransferCreate(from_account_id=1, to_account_id=2, amount=0, idempotency_key="x")
    with pytest.raises(ValueError):
        schemas.PixTransferCreate(pix_key="x", amount=1, idempotency_key=" ")
    with pytest.raises(ValueError):
        schemas.PixTransferCreate(pix_key="x", amount=0, idempotency_key="x")


@pytest.mark.asyncio
async def test_ledger_append_only(db_session: AsyncSession):
    await _cleanup(db_session)

    account = await services.LedgerService.create_account(db_session, _account_payload("133"))
    deposit = schemas.TransactionCreate(
        account_id=account.id,
        amount=100.0,
        type="DEPOSIT",
        idempotency_key="idem-ao-133",
    )
    tx = await services.LedgerService.create_transaction(db_session, deposit, otp=None)

    tx.amount = 1.0
    with pytest.raises(RuntimeError):
        await db_session.commit()
