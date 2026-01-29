from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.feature_flags import models, schemas


class FeatureFlagService:
    @staticmethod
    async def set_flag(db: AsyncSession, data: schemas.FeatureFlagCreate) -> models.FeatureFlag:
        stmt = select(models.FeatureFlag).where(models.FeatureFlag.name == data.name)
        res = await db.execute(stmt)
        flag = res.scalar_one_or_none()
        if not flag:
            flag = models.FeatureFlag(name=data.name, enabled=data.enabled)
            db.add(flag)
        else:
            flag.enabled = data.enabled
        await db.commit()
        return flag

    @staticmethod
    async def list_flags(db: AsyncSession):
        res = await db.execute(select(models.FeatureFlag))
        return res.scalars().all()
