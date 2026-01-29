from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.investments import models, schemas


class InvestmentService:
    @staticmethod
    async def create_product(db: AsyncSession, data: schemas.InvestmentProductCreate):
        product = models.InvestmentProduct(
            name=data.name,
            product_type=data.product_type,
            rate=data.rate,
            liquidity=data.liquidity,
        )
        db.add(product)
        await db.commit()
        return product

    @staticmethod
    async def list_products(db: AsyncSession):
        res = await db.execute(select(models.InvestmentProduct))
        return res.scalars().all()

    @staticmethod
    async def create_order(db: AsyncSession, user_id: int, data: schemas.InvestmentOrderCreate):
        order = models.InvestmentOrder(
            user_id=user_id,
            account_id=data.account_id,
            product_id=data.product_id,
            order_type=data.order_type,
            amount=data.amount,
        )
        db.add(order)
        await db.flush()

        stmt = select(models.InvestmentHolding).where(
            models.InvestmentHolding.user_id == user_id,
            models.InvestmentHolding.account_id == data.account_id,
            models.InvestmentHolding.product_id == data.product_id,
        )
        res = await db.execute(stmt)
        holding = res.scalar_one_or_none()
        if not holding:
            holding = models.InvestmentHolding(
                user_id=user_id,
                account_id=data.account_id,
                product_id=data.product_id,
                quantity=0.0,
                average_price=0.0,
            )
            db.add(holding)

        if data.order_type.upper() == "BUY":
            holding.quantity += data.amount
        else:
            holding.quantity -= data.amount

        await db.commit()
        return order

    @staticmethod
    async def list_holdings(db: AsyncSession, user_id: int):
        stmt = select(models.InvestmentHolding).where(models.InvestmentHolding.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def set_auto_invest(db: AsyncSession, user_id: int, data: schemas.AutoInvestCreate):
        stmt = select(models.AutoInvestConfig).where(models.AutoInvestConfig.user_id == user_id)
        res = await db.execute(stmt)
        cfg = res.scalar_one_or_none()
        if not cfg:
            cfg = models.AutoInvestConfig(
                user_id=user_id,
                account_id=data.account_id,
                product_id=data.product_id,
                min_balance=data.min_balance,
                enabled=1 if data.enabled else 0,
            )
            db.add(cfg)
        else:
            cfg.account_id = data.account_id
            cfg.product_id = data.product_id
            cfg.min_balance = data.min_balance
            cfg.enabled = 1 if data.enabled else 0
        await db.commit()
        return cfg

    @staticmethod
    async def get_auto_invest(db: AsyncSession, user_id: int):
        stmt = select(models.AutoInvestConfig).where(models.AutoInvestConfig.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()
