from datetime import datetime, timedelta
import secrets
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.ledger import models as ledger_models
from src.domain.security import models
from src.core import security as core_security


class SecurityService:
    @staticmethod
    async def upsert_device(
        db: AsyncSession,
        user_id: int,
        user_agent: str,
        ip_address: str,
        fingerprint: str,
    ) -> tuple[models.Device, bool]:
        stmt = select(models.Device).where(
            models.Device.user_id == user_id,
            models.Device.fingerprint == fingerprint,
        )
        res = await db.execute(stmt)
        device = res.scalar_one_or_none()
        is_new = False
        if not device:
            device = models.Device(
                user_id=user_id,
                name="Browser",
                user_agent=user_agent,
                ip_address=ip_address,
                fingerprint=fingerprint,
                trusted=False,
            )
            db.add(device)
            is_new = True
        device.last_seen_at = datetime.utcnow()
        device.ip_address = ip_address
        device.user_agent = user_agent
        await db.commit()
        return device, is_new

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: int,
        jti: str,
        user_agent: str,
        ip_address: str,
        device_fingerprint: str | None = None,
        expires_at: datetime | None = None,
    ) -> models.Session:
        session = models.Session(
            user_id=user_id,
            jti=jti,
            user_agent=user_agent,
            ip_address=ip_address,
            device_fingerprint=device_fingerprint,
            expires_at=expires_at,
        )
        db.add(session)
        await db.commit()
        return session

    @staticmethod
    async def revoke_session(db: AsyncSession, session_id: int, user_id: int) -> None:
        stmt = select(models.Session).where(
            models.Session.id == session_id,
            models.Session.user_id == user_id,
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            return
        session.revoked = True
        await db.commit()

    @staticmethod
    async def revoke_device(db: AsyncSession, device_id: int, user_id: int) -> None:
        stmt = select(models.Device).where(
            models.Device.id == device_id,
            models.Device.user_id == user_id,
        )
        res = await db.execute(stmt)
        device = res.scalar_one_or_none()
        if not device:
            return
        device.trusted = False
        await db.commit()

    @staticmethod
    async def create_alert(db: AsyncSession, user_id: int, alert_type: str, details: str | None = None) -> None:
        alert = models.SecurityAlert(
            user_id=user_id,
            alert_type=alert_type,
            details=details,
        )
        db.add(alert)
        await db.commit()

    @staticmethod
    async def request_password_reset(db: AsyncSession, email: str) -> str:
        stmt = select(ledger_models.User).where(ledger_models.User.email == email)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            return "noop"

        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=2)
        pr = models.PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
        )
        db.add(pr)
        await db.commit()
        return token

    @staticmethod
    async def confirm_password_reset(db: AsyncSession, token: str, new_password: str) -> bool:
        stmt = select(models.PasswordResetToken).where(models.PasswordResetToken.token == token)
        res = await db.execute(stmt)
        reset = res.scalar_one_or_none()
        if not reset or reset.used or reset.expires_at < datetime.utcnow():
            return False

        user = await db.get(ledger_models.User, reset.user_id)
        if not user:
            return False
        user.hashed_password = core_security.get_password_hash(new_password)
        reset.used = True
        await db.commit()
        return True

    @staticmethod
    async def request_otp(db: AsyncSession, user_id: int, channel: str) -> str:
        code = str(secrets.randbelow(1000000)).zfill(6)
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        otp = models.OtpChallenge(
            user_id=user_id,
            channel=channel,
            code=code,
            expires_at=expires_at,
        )
        db.add(otp)
        await db.commit()
        return code

    @staticmethod
    async def verify_otp(db: AsyncSession, user_id: int, channel: str, code: str) -> bool:
        stmt = select(models.OtpChallenge).where(
            models.OtpChallenge.user_id == user_id,
            models.OtpChallenge.channel == channel,
            models.OtpChallenge.code == code,
            models.OtpChallenge.used == False,  # noqa: E712
        )
        res = await db.execute(stmt)
        otp = res.scalar_one_or_none()
        if not otp or otp.expires_at < datetime.utcnow():
            return False
        otp.used = True
        await db.commit()
        return True

    @staticmethod
    async def add_security_question(db: AsyncSession, user_id: int, question: str, answer: str) -> None:
        answer_hash = core_security.get_password_hash(answer)
        record = models.SecurityQuestion(
            user_id=user_id,
            question=question,
            answer_hash=answer_hash,
        )
        db.add(record)
        await db.commit()

    @staticmethod
    def compute_device_fingerprint(user_agent: str, accept_language: str, client_ip: str) -> str:
        raw = f"{user_agent}|{accept_language}|{client_ip}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
