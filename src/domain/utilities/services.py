from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.utilities import models, schemas


class UtilitiesService:
    @staticmethod
    async def create_utility(db: AsyncSession, user_id: int, data: schemas.UtilityOrderCreate):
        order = models.UtilityOrder(
            user_id=user_id,
            utility_type=data.utility_type,
            provider=data.provider,
            amount=data.amount,
        )
        db.add(order)
        await db.commit()
        return order

    @staticmethod
    async def list_utilities(db: AsyncSession, user_id: int):
        res = await db.execute(select(models.UtilityOrder).where(models.UtilityOrder.user_id == user_id))
        return res.scalars().all()

    @staticmethod
    async def create_donation(db: AsyncSession, user_id: int, data: schemas.DonationCreate):
        donation = models.Donation(
            user_id=user_id,
            organization=data.organization,
            amount=data.amount,
        )
        db.add(donation)
        await db.commit()
        return donation

    @staticmethod
    async def list_donations(db: AsyncSession, user_id: int):
        res = await db.execute(select(models.Donation).where(models.Donation.user_id == user_id))
        return res.scalars().all()

    @staticmethod
    async def create_fx_order(db: AsyncSession, user_id: int, data: schemas.FxOrderCreate):
        order = models.FxOrder(
            user_id=user_id,
            currency=data.currency,
            amount=data.amount,
            rate=data.rate,
        )
        db.add(order)
        await db.commit()
        return order

    @staticmethod
    async def list_fx_orders(db: AsyncSession, user_id: int):
        res = await db.execute(select(models.FxOrder).where(models.FxOrder.user_id == user_id))
        return res.scalars().all()
