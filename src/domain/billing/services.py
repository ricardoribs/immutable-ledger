import secrets
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.billing import models, schemas
from src.domain.ledger import services as ledger_services
from src.domain.ledger import schemas as ledger_schemas


def _mod10(num: str) -> int:
    total = 0
    factor = 2
    for n in reversed(num):
        add = int(n) * factor
        add = (add // 10) + (add % 10)
        total += add
        factor = 1 if factor == 2 else 2
    return (10 - (total % 10)) % 10


def _mod11(num: str) -> int:
    total = 0
    factor = 2
    for n in reversed(num):
        total += int(n) * factor
        factor = 2 if factor == 9 else factor + 1
    remainder = total % 11
    dv = 11 - remainder
    if dv in (0, 10, 11):
        return 1
    return dv


def _generate_boleto_barcode(amount: float, due_date: datetime) -> tuple[str, str]:
    bank_code = "341"  # exemplo
    currency = "9"
    days = (due_date.date() - datetime(1997, 10, 7).date()).days
    fator = f"{days:04d}"
    valor = f"{int(round(amount * 100)):010d}"
    free_field = f"{secrets.randbelow(10**10):010d}{secrets.randbelow(10**9):09d}"
    base = f"{bank_code}{currency}{fator}{valor}{free_field}"
    dv = _mod11(base)
    barcode = f"{bank_code}{currency}{dv}{fator}{valor}{free_field}"
    # Linha digitavel (simples)
    campo1 = barcode[0:9] + str(_mod10(barcode[0:9]))
    campo2 = barcode[9:19] + str(_mod10(barcode[9:19]))
    campo3 = barcode[19:29] + str(_mod10(barcode[19:29]))
    campo4 = barcode[29]
    campo5 = barcode[30:44]
    digitable = f"{campo1}.{campo2}.{campo3} {campo4} {campo5}"
    return barcode, digitable


class BillingService:
    @staticmethod
    async def create_boleto(db: AsyncSession, user_id: int, data: schemas.BoletoCreate):
        barcode, digitable = _generate_boleto_barcode(data.amount, data.due_date)
        boleto = models.Boleto(
            user_id=user_id,
            amount=data.amount,
            description=data.description,
            due_date=data.due_date,
            barcode=barcode,
            digitable_line=digitable,
        )
        db.add(boleto)
        await db.commit()
        return boleto

    @staticmethod
    async def list_boletos(db: AsyncSession, user_id: int):
        stmt = select(models.Boleto).where(models.Boleto.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def pay_boleto(db: AsyncSession, payer_account_id: int, data: schemas.BoletoPay):
        boleto = await db.get(models.Boleto, data.boleto_id)
        if not boleto:
            raise ValueError("Boleto nao encontrado")
        if boleto.status != "OPEN":
            raise ValueError("Boleto indisponivel")

        tx = ledger_schemas.TransactionCreate(
            account_id=payer_account_id,
            amount=boleto.amount,
            type="WITHDRAW",
            idempotency_key=secrets.token_urlsafe(16),
        )
        await ledger_services.LedgerService.create_transaction(db, tx, otp=None)
        boleto.status = "PAID"
        boleto.paid_at = datetime.utcnow()
        boleto.payer_account_id = payer_account_id
        await db.commit()
        return boleto

    @staticmethod
    async def create_payment_link(db: AsyncSession, user_id: int, data: schemas.PaymentLinkCreate):
        url = f"https://pay.luisbank.local/{secrets.token_urlsafe(8)}"
        link = models.PaymentLink(
            user_id=user_id,
            amount=data.amount,
            url=url,
        )
        db.add(link)
        await db.commit()
        return link

    @staticmethod
    async def list_payment_links(db: AsyncSession, user_id: int):
        stmt = select(models.PaymentLink).where(models.PaymentLink.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_pos_sale(db: AsyncSession, user_id: int, data: schemas.PosSaleCreate):
        sale = models.PosSale(
            user_id=user_id,
            amount=data.amount,
            status="RECEIVED",
        )
        db.add(sale)
        await db.commit()
        return sale

    @staticmethod
    async def list_pos_sales(db: AsyncSession, user_id: int):
        stmt = select(models.PosSale).where(models.PosSale.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_split_rule(db: AsyncSession, user_id: int, data: schemas.SplitRuleCreate):
        rule = models.SplitRule(
            user_id=user_id,
            name=data.name,
            percentage=data.percentage,
        )
        db.add(rule)
        await db.commit()
        return rule

    @staticmethod
    async def list_split_rules(db: AsyncSession, user_id: int):
        stmt = select(models.SplitRule).where(models.SplitRule.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()
