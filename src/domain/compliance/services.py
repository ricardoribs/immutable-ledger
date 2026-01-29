from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.compliance import models, schemas
from src.domain.ledger import models as ledger_models
from src.domain.security import models as security_models


class ComplianceService:
    @staticmethod
    async def record_consent(db: AsyncSession, user_id: int, data: schemas.ConsentCreate) -> models.ConsentRecord:
        consent = models.ConsentRecord(
            user_id=user_id,
            consent_type=data.consent_type,
            details=data.details,
        )
        db.add(consent)
        await db.commit()
        return consent

    @staticmethod
    async def list_consents(db: AsyncSession, user_id: int):
        stmt = select(models.ConsentRecord).where(models.ConsentRecord.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def request_forget(db: AsyncSession, user_id: int) -> models.ForgetRequest:
        req = models.ForgetRequest(user_id=user_id)
        db.add(req)
        await db.commit()
        return req

    @staticmethod
    async def anonymize_user(db: AsyncSession, user_id: int) -> None:
        user = await db.get(ledger_models.User, user_id)
        if not user:
            return
        user.name = "ANONYMIZED"
        user.email = f"anon_{user_id}@example.local"
        user.cpf = ""
        user.cpf_hash = f"anon_{user_id}"
        user.cpf_token = None
        user.cpf_last4 = None
        user.is_anonymized = True
        user.anonymized_at = datetime.utcnow()

        # Revoga sessions
        stmt_sess = select(security_models.Session).where(security_models.Session.user_id == user_id)
        res = await db.execute(stmt_sess)
        for sess in res.scalars().all():
            sess.revoked = True

        await db.commit()

    @staticmethod
    async def complete_forget_request(db: AsyncSession, request_id: int) -> models.ForgetRequest | None:
        req = await db.get(models.ForgetRequest, request_id)
        if not req or req.status == "COMPLETED":
            return req
        await ComplianceService.anonymize_user(db, req.user_id)
        req.status = "COMPLETED"
        req.completed_at = datetime.utcnow()
        await db.commit()
        return req
