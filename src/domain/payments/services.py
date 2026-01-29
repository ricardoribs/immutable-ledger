from datetime import datetime
import secrets

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.payments import models, schemas
from src.domain.ledger import services as ledger_services
from src.domain.ledger import schemas as ledger_schemas
from src.domain.payments.spb import SpbGateway
from src.domain.settings import services as settings_services
from src.core.money import to_decimal


class PaymentService:
    @staticmethod
    async def _execute_payment(db: AsyncSession, payment: models.Payment) -> models.Payment:
        fee = to_decimal("0.00")
        spb_protocol = None
        if payment.payment_type.upper() in {"TED", "DOC"}:
            if not payment.beneficiary_id:
                raise ValueError("Beneficiario obrigatorio")
            beneficiary = await db.get(models.Beneficiary, payment.beneficiary_id)
            if not beneficiary or not SpbGateway.validate_destination(
                beneficiary.bank_code, beneficiary.agency, beneficiary.account
            ):
                raise ValueError("Destino invalido")
            fee = to_decimal(SpbGateway.calculate_fee(payment.payment_type, payment.amount))
            spb_protocol = SpbGateway.send(payment.payment_type)

        total = to_decimal(payment.amount) + fee
        tx = ledger_schemas.TransactionCreate(
            account_id=payment.account_id,
            amount=total,
            type="WITHDRAW",
            idempotency_key=secrets.token_urlsafe(16),
        )
        await ledger_services.LedgerService.create_transaction(db, tx, otp=None)
        payment.status = "COMPLETED"
        payment.executed_at = datetime.utcnow()
        payment.fee_amount = fee
        payment.spb_protocol = spb_protocol
        await db.commit()
        return payment
    @staticmethod
    async def create_beneficiary(db: AsyncSession, user_id: int, data: schemas.BeneficiaryCreate):
        b = models.Beneficiary(
            user_id=user_id,
            name=data.name,
            bank_code=data.bank_code,
            agency=data.agency,
            account=data.account,
            cpf_cnpj=data.cpf_cnpj,
            pix_key=data.pix_key,
            favorite=data.favorite,
        )
        db.add(b)
        await db.commit()
        return b

    @staticmethod
    async def list_beneficiaries(db: AsyncSession, user_id: int):
        stmt = select(models.Beneficiary).where(models.Beneficiary.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_payment(db: AsyncSession, user_id: int, data: schemas.PaymentCreate):
        if data.payment_type.upper() in {"TED", "DOC"}:
            limits = await settings_services.SettingsService.get_or_create_limits(db, user_id)
            if data.payment_type.upper() == "TED" and data.amount > limits.ted_limit:
                raise ValueError("Limite TED excedido")
            if data.payment_type.upper() == "DOC" and data.amount > limits.doc_limit:
                raise ValueError("Limite DOC excedido")
        payment = models.Payment(
            user_id=user_id,
            account_id=data.account_id,
            beneficiary_id=data.beneficiary_id,
            payment_type=data.payment_type,
            amount=data.amount,
            description=data.description,
            scheduled_for=data.scheduled_for,
            to_account_id=data.to_account_id,
            status="PENDING",
        )
        db.add(payment)
        await db.flush()

        if not data.scheduled_for:
            await PaymentService._execute_payment(db, payment)

        await db.commit()
        return payment

    @staticmethod
    async def list_payments(db: AsyncSession, user_id: int):
        stmt = select(models.Payment).where(models.Payment.user_id == user_id).order_by(models.Payment.created_at.desc())
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_recurring(db: AsyncSession, user_id: int, data: schemas.RecurringPaymentCreate):
        rec = models.RecurringPayment(
            user_id=user_id,
            account_id=data.account_id,
            beneficiary_id=data.beneficiary_id,
            payment_type=data.payment_type,
            amount=data.amount,
            interval_days=data.interval_days,
            next_run_at=data.next_run_at,
        )
        db.add(rec)
        await db.commit()
        return rec

    @staticmethod
    async def list_recurring(db: AsyncSession, user_id: int):
        stmt = select(models.RecurringPayment).where(models.RecurringPayment.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()
