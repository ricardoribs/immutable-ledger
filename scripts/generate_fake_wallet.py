import argparse
import asyncio
import csv
import random
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from src.infra.database import async_session
from src.domain.ledger import schemas as ledger_schemas
from src.domain.ledger import services as ledger_services
from src.domain.ledger import models as ledger_models
from src.domain.pix import services as pix_services
from src.domain.pix import schemas as pix_schemas
from src.domain.regulatory import models as regulatory_models
from src.domain.settings import models as settings_models
from src.core.money import to_decimal


FIRST_NAMES = [
    "Ana", "Bruno", "Carla", "Diego", "Eduarda", "Felipe", "Giovana", "Henrique",
    "Isabela", "Joao", "Karen", "Luiz", "Mariana", "Nicolas", "Olivia", "Paulo",
    "Rafaela", "Samuel", "Thiago", "Vivian",
]

LAST_NAMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Pereira", "Lima", "Gomes", "Costa",
    "Ribeiro", "Almeida", "Carvalho", "Rocha", "Barbosa", "Martins", "Dias",
]


def _cpf_for_index(idx: int) -> str:
    base = f"{idx:09d}"[-9:]
    return f"{base}{random.randint(10, 99)}"


def _email_for_name(name: str, idx: int) -> str:
    slug = name.lower().replace(" ", ".")
    return f"{slug}.{idx}@luisbank.fake"


def _random_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def _random_amount(min_value: float, max_value: float) -> Decimal:
    return to_decimal(str(random.uniform(min_value, max_value)))


async def _ensure_kyc(db, user_id: int, verified: bool):
    stmt = select(regulatory_models.KycProfile).where(regulatory_models.KycProfile.user_id == user_id)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    if not profile:
        profile = regulatory_models.KycProfile(user_id=user_id, status="PENDING", risk_level="MEDIUM")
        db.add(profile)
        await db.commit()
    if verified:
        profile.status = "VERIFIED"
        profile.updated_at = datetime.utcnow()
        await db.commit()


async def _ensure_limits(db, user_id: int):
    stmt = select(settings_models.LimitConfig).where(settings_models.LimitConfig.user_id == user_id)
    res = await db.execute(stmt)
    cfg = res.scalar_one_or_none()
    if not cfg:
        cfg = settings_models.LimitConfig(user_id=user_id, ted_limit=to_decimal("50000.00"))
        db.add(cfg)
        await db.commit()
    return cfg


async def generate_fake_wallet(
    users: int,
    days: int,
    max_daily_txs: int,
    export_dir: Path,
    seed: int | None,
):
    if seed is not None:
        random.seed(seed)

    async with async_session() as db:
        accounts = []

        for idx in range(1, users + 1):
            name = _random_name()
            cpf = _cpf_for_index(idx)
            email = _email_for_name(name, idx)

            account = await ledger_services.LedgerService.create_account(
                db,
                ledger_schemas.AccountCreate(
                    name=name,
                    cpf=cpf,
                    email=email,
                    password="SenhaForte123",
                    account_type=random.choice(["CHECKING", "SAVINGS", "DIGITAL"]),
                ),
            )
            accounts.append(account)

            await _ensure_kyc(db, account.user_id, verified=random.random() < 0.85)
            await _ensure_limits(db, account.user_id)

            if random.random() < 0.6:
                pix_key = pix_schemas.PixKeyCreate(
                    key=email,
                    key_type="EMAIL",
                )
                try:
                    await ledger_services.LedgerService.create_pix_key(db, account.id, pix_key)
                except Exception:
                    pass

            opening_deposit = ledger_schemas.TransactionCreate(
                account_id=account.id,
                amount=_random_amount(50, 2000),
                type="DEPOSIT",
                idempotency_key=f"seed:{secrets.token_urlsafe(8)}",
            )
            await ledger_services.LedgerService.create_transaction(db, opening_deposit, otp=None)

        start_date = datetime.utcnow() - timedelta(days=days)

        for day in range(days):
            current = start_date + timedelta(days=day)
            for account in accounts:
                txs_today = random.randint(0, max_daily_txs)
                for _ in range(txs_today):
                    amount = _random_amount(5, 1500)
                    choice = random.random()

                    if choice < 0.5:
                        tx = ledger_schemas.TransactionCreate(
                            account_id=account.id,
                            amount=amount,
                            type="DEPOSIT",
                            idempotency_key=f"dep:{secrets.token_urlsafe(8)}",
                        )
                        await ledger_services.LedgerService.create_transaction(db, tx, otp=None)
                    elif choice < 0.75:
                        tx = ledger_schemas.TransactionCreate(
                            account_id=account.id,
                            amount=amount,
                            type="WITHDRAW",
                            idempotency_key=f"wd:{secrets.token_urlsafe(8)}",
                        )
                        try:
                            await ledger_services.LedgerService.create_transaction(db, tx, otp=None)
                        except Exception:
                            pass
                    elif choice < 0.9:
                        target = random.choice(accounts)
                        if target.id == account.id:
                            continue
                        transfer = ledger_schemas.TransferCreate(
                            from_account_id=account.id,
                            to_account_id=target.id,
                            amount=amount,
                            idempotency_key=f"tr:{secrets.token_urlsafe(8)}",
                            description="Transferencia simulada",
                        )
                        try:
                            await ledger_services.LedgerService.process_transfer(db, transfer, otp=None)
                        except Exception:
                            pass
                    else:
                        target = random.choice(accounts)
                        if target.id == account.id:
                            continue
                        try:
                            stmt = select(ledger_models.PixKey).where(ledger_models.PixKey.account_id == target.id)
                            res = await db.execute(stmt)
                            pix_keys = res.scalars().all()
                        except Exception:
                            pix_keys = []
                        if pix_keys:
                            pix_key = random.choice(pix_keys)
                            pix_transfer = ledger_schemas.PixTransferCreate(
                                pix_key=pix_key.key,
                                amount=amount,
                                idempotency_key=f"px:{secrets.token_urlsafe(8)}",
                            )
                            try:
                                await ledger_services.LedgerService.process_pix_transfer(
                                    db, pix_transfer, account.id, otp=None
                                )
                            except Exception:
                                pass

        await db.commit()

        export_dir.mkdir(parents=True, exist_ok=True)
        await _export_csv(db, export_dir)


async def _export_csv(db, export_dir: Path):
    users = (await db.execute(select(ledger_models.User))).scalars().all()
    accounts = (await db.execute(select(ledger_models.Account))).scalars().all()
    transactions = (await db.execute(select(ledger_models.Transaction))).scalars().all()
    postings = (await db.execute(select(ledger_models.Posting))).scalars().all()

    _write_csv(export_dir / "users.csv", ["id", "name", "email", "cpf_last4", "created_at"], [
        [u.id, u.name, u.email, u.cpf_last4, u.created_at.isoformat()] for u in users
    ])
    _write_csv(export_dir / "accounts.csv", ["id", "user_id", "account_number", "balance", "type", "status"], [
        [a.id, a.user_id, a.account_number, str(a.balance), a.account_type, a.status] for a in accounts
    ])
    _write_csv(export_dir / "transactions.csv", ["id", "account_id", "amount", "type", "timestamp", "sequence"], [
        [t.id, t.account_id, str(t.amount), t.operation_type, t.timestamp.isoformat(), t.sequence] for t in transactions
    ])
    _write_csv(export_dir / "postings.csv", ["id", "transaction_id", "account_id", "amount", "timestamp"], [
        [p.id, p.transaction_id, p.account_id, str(p.amount), p.timestamp.isoformat()] for p in postings
    ])


def _write_csv(path: Path, header: list[str], rows: list[list]):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Gera carteira fake LuisBank para engenharia de dados.")
    parser.add_argument("--users", type=int, default=200)
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--max-daily-txs", type=int, default=3)
    parser.add_argument("--export-dir", type=str, default="analytics/exports")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    asyncio.run(
        generate_fake_wallet(
            users=args.users,
            days=args.days,
            max_daily_txs=args.max_daily_txs,
            export_dir=Path(args.export_dir),
            seed=args.seed,
        )
    )


if __name__ == "__main__":
    main()
