from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.open_banking import models, schemas


class OpenBankingService:
    @staticmethod
    async def create_consent(db: AsyncSession, user_id: int, data: schemas.ConsentCreate):
        consent = models.Consent(
            user_id=user_id,
            institution=data.institution,
            scope=data.scope,
        )
        db.add(consent)
        await db.commit()
        return consent

    @staticmethod
    async def list_consents(db: AsyncSession, user_id: int):
        res = await db.execute(select(models.Consent).where(models.Consent.user_id == user_id))
        return res.scalars().all()

    @staticmethod
    async def create_external_account(db: AsyncSession, user_id: int, data: schemas.ExternalAccountCreate):
        account = models.ExternalAccount(
            user_id=user_id,
            institution=data.institution,
            account_ref=data.account_ref,
            balance=data.balance,
        )
        db.add(account)
        await db.commit()
        return account

    @staticmethod
    async def list_external_accounts(db: AsyncSession, user_id: int):
        res = await db.execute(select(models.ExternalAccount).where(models.ExternalAccount.user_id == user_id))
        return res.scalars().all()

    @staticmethod
    async def create_payment(db: AsyncSession, user_id: int, data: schemas.OpenBankingPaymentCreate):
        payment = models.OpenBankingPayment(
            user_id=user_id,
            amount=data.amount,
            status="COMPLETED",
        )
        db.add(payment)
        await db.commit()
        return payment

    @staticmethod
    async def list_payments(db: AsyncSession, user_id: int):
        res = await db.execute(select(models.OpenBankingPayment).where(models.OpenBankingPayment.user_id == user_id))
        return res.scalars().all()
