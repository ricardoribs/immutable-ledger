import asyncio
import pytest

from sqlalchemy import delete, select
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
        models.Account,
        models.User,
    ]:
        await db.execute(delete(table))
    await db.execute(delete(regulatory_models.KycProfile))
    await db.commit()


def _account_payload(suffix: str):
    return schemas.AccountCreate(
        name=f"User {suffix}",
        cpf=f"98765432{suffix[:3]}",
        email=f"concurrency-{suffix}@example.com",
        password="SenhaForte123",
        account_type="CHECKING",
    )


@pytest.mark.asyncio
async def test_concurrent_transfers_respect_balance(db_session: AsyncSession):
    await _cleanup(db_session)
    acc_from = await services.LedgerService.create_account(db_session, _account_payload("201"))
    acc_to = await services.LedgerService.create_account(db_session, _account_payload("202"))

    deposit = schemas.TransactionCreate(
        account_id=acc_from.id,
        amount=100.0,
        type="DEPOSIT",
        idempotency_key="idem-dep-201",
    )
    await services.LedgerService.create_transaction(db_session, deposit, otp=None)

    transfer_a = schemas.TransferCreate(
        from_account_id=acc_from.id,
        to_account_id=acc_to.id,
        amount=80.0,
        idempotency_key="idem-tr-201a",
        description="A",
    )
    transfer_b = schemas.TransferCreate(
        from_account_id=acc_from.id,
        to_account_id=acc_to.id,
        amount=80.0,
        idempotency_key="idem-tr-201b",
        description="B",
    )

    async def run_transfer(data):
        async with async_session() as session:
            return await services.LedgerService.process_transfer(session, data, otp=None)

    results = await asyncio.gather(
        run_transfer(transfer_a),
        run_transfer(transfer_b),
        return_exceptions=True,
    )

    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(successes) == 1

    async with async_session() as check_session:
        bal = await services.LedgerService.get_balance(check_session, acc_from.id, use_cache=False)
        assert float(bal) == pytest.approx(20.0)


@pytest.mark.asyncio
async def test_concurrent_sequence_unique(db_session: AsyncSession):
    await _cleanup(db_session)
    acc = await services.LedgerService.create_account(db_session, _account_payload("203"))

    deposit = schemas.TransactionCreate(
        account_id=acc.id,
        amount=500.0,
        type="DEPOSIT",
        idempotency_key="idem-dep-203",
    )
    await services.LedgerService.create_transaction(db_session, deposit, otp=None)

    async def run_deposit(idx: int):
        async with async_session() as session:
            tx = schemas.TransactionCreate(
                account_id=acc.id,
                amount=10.0,
                type="DEPOSIT",
                idempotency_key=f"idem-dep-203-{idx}",
            )
            return await services.LedgerService.create_transaction(session, tx, otp=None)

    await asyncio.gather(*[run_deposit(i) for i in range(5)])

    stmt = select(models.Transaction.sequence).where(models.Transaction.account_id == acc.id)
    res = await db_session.execute(stmt)
    sequences = [row[0] for row in res.all() if row[0] is not None]
    assert len(sequences) == len(set(sequences))
