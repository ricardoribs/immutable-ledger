import secrets
from datetime import datetime
import base64
from io import BytesIO

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.pix import models, schemas
from src.infra.cache import cache
import qrcode
from src.domain.ledger import services as ledger_services
from src.domain.ledger import schemas as ledger_schemas
from src.core.money import to_decimal


class PixService:
    @staticmethod
    def _build_payload(tx_id: str, amount: float | None) -> str:
        if amount is None:
            return f"PIX|TXID={tx_id}"
        return f"PIX|TXID={tx_id}|AMOUNT={amount:.2f}"

    @staticmethod
    def _qr_base64(payload: str) -> str:
        img = qrcode.make(payload)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii")

    @staticmethod
    async def _enforce_limits(db: AsyncSession, account_id: int, amount: float):
        stmt = select(models.PixLimit).where(models.PixLimit.account_id == account_id)
        res = await db.execute(stmt)
        limit = res.scalar_one_or_none()
        if not limit:
            limit = models.PixLimit(account_id=account_id)
            db.add(limit)
            await db.commit()

        amount_value = to_decimal(amount)
        if amount_value > to_decimal(limit.per_tx_limit):
            raise ValueError("Limite por transacao excedido")

        day_key = f"pix:day:{account_id}:{datetime.utcnow().date().isoformat()}"
        day_total = await cache.incr_money_with_expire(day_key, amount_value, ttl_seconds=86400)
        if day_total > to_decimal(limit.day_limit):
            raise ValueError("Limite diario excedido")

    @staticmethod
    async def create_charge(db: AsyncSession, account_id: int, data: schemas.PixChargeCreate):
        tx_id = secrets.token_urlsafe(8)
        payload = PixService._build_payload(tx_id, data.amount)
        qr_code = PixService._qr_base64(payload)
        charge = models.PixCharge(
            account_id=account_id,
            amount=data.amount,
            description=data.description,
            expires_at=data.expires_at,
            tx_id=tx_id,
            payload=payload,
            qr_code_base64=qr_code,
        )
        db.add(charge)
        await db.commit()
        return charge

    @staticmethod
    async def list_charges(db: AsyncSession, account_id: int):
        stmt = select(models.PixCharge).where(models.PixCharge.account_id == account_id).order_by(models.PixCharge.created_at.desc())
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_refund(db: AsyncSession, data: schemas.PixRefundCreate):
        charge = await db.get(models.PixCharge, data.charge_id)
        if not charge:
            raise ValueError("Cobranca nao encontrada")
        if charge.amount is not None and data.amount > charge.amount:
            raise ValueError("Valor de devolucao invalido")
        if charge.payer_account_id and data.amount > 0:
            tx = ledger_schemas.TransferCreate(
                from_account_id=charge.account_id,
                to_account_id=charge.payer_account_id,
                amount=data.amount,
                idempotency_key=secrets.token_urlsafe(16),
            )
            await ledger_services.LedgerService.process_transfer(db, tx, otp=None)
        refund = models.PixRefund(
            charge_id=data.charge_id,
            amount=data.amount,
            reason=data.reason,
            status="COMPLETED",
        )
        db.add(refund)
        await db.commit()
        return refund

    @staticmethod
    async def pay_charge(db: AsyncSession, payer_account_id: int, data: schemas.PixChargePay):
        charge = await db.get(models.PixCharge, data.charge_id)
        if not charge:
            raise ValueError("Cobranca nao encontrada")
        if charge.status != "PENDING":
            raise ValueError("Cobranca indisponivel")
        amount = charge.amount if charge.amount is not None else data.amount
        if not amount or amount <= 0:
            raise ValueError("Valor invalido")
        await PixService._enforce_limits(db, payer_account_id, amount)

        tx = ledger_schemas.TransferCreate(
            from_account_id=payer_account_id,
            to_account_id=charge.account_id,
            amount=amount,
            idempotency_key=secrets.token_urlsafe(16),
        )
        await ledger_services.LedgerService.process_transfer(db, tx, otp=None)
        charge.status = "PAID"
        charge.paid_at = datetime.utcnow()
        charge.payer_account_id = payer_account_id
        await db.commit()
        return charge

    @staticmethod
    async def get_limits(db: AsyncSession, account_id: int):
        stmt = select(models.PixLimit).where(models.PixLimit.account_id == account_id)
        res = await db.execute(stmt)
        limit = res.scalar_one_or_none()
        if not limit:
            limit = models.PixLimit(account_id=account_id)
            db.add(limit)
            await db.commit()
        return limit

    @staticmethod
    async def update_limits(db: AsyncSession, account_id: int, data: schemas.PixLimitUpdate):
        limit = await PixService.get_limits(db, account_id)
        limit.day_limit = data.day_limit
        limit.night_limit = data.night_limit
        limit.per_tx_limit = data.per_tx_limit
        limit.monthly_limit = data.monthly_limit
        limit.updated_at = datetime.utcnow()
        await db.commit()
        return limit

    @staticmethod
    async def create_schedule(db: AsyncSession, account_id: int, data: schemas.PixScheduleCreate):
        await PixService._enforce_limits(db, account_id, data.amount)
        sched = models.PixSchedule(
            from_account_id=account_id,
            pix_key=data.pix_key,
            amount=data.amount,
            scheduled_for=data.scheduled_for,
        )
        db.add(sched)
        await db.commit()
        return sched

    @staticmethod
    async def list_schedules(db: AsyncSession, account_id: int):
        stmt = select(models.PixSchedule).where(models.PixSchedule.from_account_id == account_id)
        res = await db.execute(stmt)
        return res.scalars().all()
