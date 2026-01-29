import secrets
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.cards import models, schemas
from src.domain.security.tokenization import TokenizationService


class CardService:
    @staticmethod
    async def create_card(db: AsyncSession, user_id: int, data: schemas.CardCreate):
        pan = "4" + str(secrets.randbelow(10**15)).zfill(15)
        last4 = pan[-4:]
        token = await TokenizationService.tokenize(
            db, pan, token_type="CARD", user_id=user_id, last4=last4
        )
        card = models.Card(
            user_id=user_id,
            account_id=data.account_id,
            card_type=data.card_type,
            last4=last4,
            card_token=token,
            limit_total=data.limit_total,
            limit_available=data.limit_total,
            due_day=data.due_day,
            parent_card_id=data.parent_card_id,
        )
        db.add(card)
        await db.commit()
        return card

    @staticmethod
    async def list_cards(db: AsyncSession, user_id: int):
        stmt = select(models.Card).where(models.Card.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def set_card_status(db: AsyncSession, card_id: int, user_id: int, status: str):
        card = await db.get(models.Card, card_id)
        if not card or card.user_id != user_id:
            return None
        card.status = status
        await db.commit()
        return card

    @staticmethod
    async def update_controls(db: AsyncSession, card_id: int, user_id: int, data: schemas.CardControlUpdate):
        card = await db.get(models.Card, card_id)
        if not card or card.user_id != user_id:
            return None
        card.international_enabled = data.international_enabled
        card.online_enabled = data.online_enabled
        card.contactless_enabled = data.contactless_enabled
        await db.commit()
        return card

    @staticmethod
    async def list_transactions(db: AsyncSession, card_id: int, user_id: int):
        stmt = select(models.CardTransaction).where(models.CardTransaction.card_id == card_id)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def list_invoices(db: AsyncSession, card_id: int, user_id: int):
        stmt = select(models.CardInvoice).where(models.CardInvoice.card_id == card_id)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def create_transaction(db: AsyncSession, user_id: int, data: schemas.CardTransactionCreate):
        card = await db.get(models.Card, data.card_id)
        if not card or card.user_id != user_id:
            return None
        if card.status != "ACTIVE":
            raise ValueError("Cartao bloqueado")

        channel = data.channel.upper()
        if channel == "ONLINE" and not card.online_enabled:
            raise ValueError("Transacao online bloqueada")
        if channel == "IN_PERSON" and not card.international_enabled:
            raise ValueError("Transacao presencial bloqueada")
        if channel == "CONTACTLESS" and not card.contactless_enabled:
            raise ValueError("Transacao por aproximacao bloqueada")

        if data.amount > card.limit_available:
            raise ValueError("Limite insuficiente")

        tx = models.CardTransaction(
            card_id=card.id,
            amount=data.amount,
            merchant=data.merchant,
            description=data.description,
            status="POSTED",
        )
        db.add(tx)
        card.limit_available -= data.amount
        await db.commit()
        return tx
