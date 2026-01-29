from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.insurance import models, schemas


class InsuranceService:
    @staticmethod
    async def create_policy(db: AsyncSession, user_id: int, data: schemas.InsurancePolicyCreate):
        policy = models.InsurancePolicy(
            user_id=user_id,
            policy_type=data.policy_type,
            premium=data.premium,
            details=data.details,
        )
        db.add(policy)
        await db.commit()
        return policy

    @staticmethod
    async def list_policies(db: AsyncSession, user_id: int):
        stmt = select(models.InsurancePolicy).where(models.InsurancePolicy.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_claim(db: AsyncSession, user_id: int, data: schemas.InsuranceClaimCreate):
        policy = await db.get(models.InsurancePolicy, data.policy_id)
        if not policy or policy.user_id != user_id:
            return None
        claim = models.InsuranceClaim(
            policy_id=data.policy_id,
            description=data.description,
        )
        db.add(claim)
        await db.commit()
        return claim

    @staticmethod
    async def list_claims(db: AsyncSession, user_id: int):
        stmt = select(models.InsuranceClaim).join(
            models.InsurancePolicy, models.InsurancePolicy.id == models.InsuranceClaim.policy_id
        ).where(models.InsurancePolicy.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()
