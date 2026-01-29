from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.pj import models, schemas


class PjService:
    @staticmethod
    async def create_business(db: AsyncSession, user_id: int, data: schemas.BusinessCreate):
        business = models.Business(
            user_id=user_id,
            name=data.name,
            cnpj=data.cnpj,
        )
        db.add(business)
        await db.commit()
        return business

    @staticmethod
    async def list_businesses(db: AsyncSession, user_id: int):
        stmt = select(models.Business).where(models.Business.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_batch_payment(db: AsyncSession, data: schemas.BatchPaymentCreate):
        batch = models.BatchPayment(
            business_id=data.business_id,
            total_amount=data.total_amount,
            status="RECEIVED",
        )
        db.add(batch)
        await db.commit()
        return batch

    @staticmethod
    async def create_payroll_run(db: AsyncSession, data: schemas.PayrollRunCreate):
        payroll = models.PayrollRun(
            business_id=data.business_id,
            total_amount=data.total_amount,
            status="RECEIVED",
        )
        db.add(payroll)
        await db.flush()

        for item in data.items:
            db_item = models.PayrollItem(
                payroll_id=payroll.id,
                employee_name=item.employee_name,
                employee_document=item.employee_document,
                amount=item.amount,
            )
            db.add(db_item)

        await db.commit()
        return payroll
