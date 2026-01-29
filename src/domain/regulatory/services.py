from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.domain.regulatory import models, schemas
from src.domain.ledger import models as ledger_models


class RegulatoryService:
    @staticmethod
    async def create_kyc(db: AsyncSession, user_id: int, data: schemas.KycCreate):
        stmt = select(models.KycProfile).where(models.KycProfile.user_id == user_id)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            existing.document_id = data.document_id
            existing.status = "PENDING"
            await db.commit()
            return existing

        status = "VERIFIED" if data.document_id and len(data.document_id) >= 6 else "PENDING"
        profile = models.KycProfile(
            user_id=user_id,
            document_id=data.document_id,
            status=status,
            risk_level="LOW" if status == "VERIFIED" else "MEDIUM",
        )
        db.add(profile)
        await db.commit()
        return profile

    @staticmethod
    async def list_aml_alerts(db: AsyncSession, user_id: int):
        stmt = select(models.AmlAlert).where(models.AmlAlert.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_aml_alert(db: AsyncSession, user_id: int, rule: str, details: str):
        alert = models.AmlAlert(
            user_id=user_id,
            rule=rule,
            details=details,
        )
        db.add(alert)
        await db.commit()
        return alert

    @staticmethod
    async def generate_scr_report(db: AsyncSession, period: str):
        stmt = select(func.count(ledger_models.Transaction.id))
        res = await db.execute(stmt)
        count = int(res.scalar() or 0)
        content = f"SCR Report {period}: total_transactions={count}"
        report = models.ScrReport(period=period, content=content)
        db.add(report)
        await db.commit()
        return report

    @staticmethod
    async def generate_coaf_report(db: AsyncSession, period: str):
        stmt = select(func.count(ledger_models.Transaction.id)).where(
            ledger_models.Transaction.amount >= 10000
        )
        res = await db.execute(stmt)
        high_value = int(res.scalar() or 0)
        content = f"COAF Report {period}: high_value_transactions={high_value}"
        report = models.CoafReport(period=period, content=content)
        db.add(report)
        await db.commit()
        return report
