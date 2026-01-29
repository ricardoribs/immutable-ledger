import hashlib
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.encryption import CryptoService
from src.domain.security import models


class TokenizationService:
    @staticmethod
    async def tokenize(
        db: AsyncSession,
        value: str,
        token_type: str,
        user_id: int | None = None,
        last4: str | None = None,
    ) -> str:
        value_hash = hashlib.sha256(value.encode("utf-8")).hexdigest()
        stmt = select(models.TokenVault).where(
            models.TokenVault.value_hash == value_hash,
            models.TokenVault.token_type == token_type,
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing.token

        token = f"tok_{secrets.token_urlsafe(16)}"
        encrypted = CryptoService.encrypt(value)
        record = models.TokenVault(
            user_id=user_id,
            token=token,
            token_type=token_type,
            value_encrypted=encrypted,
            value_hash=value_hash,
            last4=last4,
        )
        db.add(record)
        await db.flush()
        return token

    @staticmethod
    async def detokenize(db: AsyncSession, token: str) -> str | None:
        stmt = select(models.TokenVault).where(models.TokenVault.token == token)
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            return None
        return CryptoService.decrypt(record.value_encrypted)
