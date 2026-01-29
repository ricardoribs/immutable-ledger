from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from datetime import datetime

from src.infra.database import Base
from src.domain.common.types import Money


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    card_type = Column(String, nullable=False)  # DEBIT, CREDIT, VIRTUAL
    last4 = Column(String, nullable=False)
    card_token = Column(String, unique=True, index=True, nullable=True)
    status = Column(String, default="ACTIVE")  # ACTIVE, BLOCKED
    limit_total = Column(Money, default=0)
    limit_available = Column(Money, default=0)
    cashback_balance = Column(Money, default=0)
    points_balance = Column(Integer, default=0)
    due_day = Column(Integer, default=10)
    international_enabled = Column(Boolean, default=True)
    online_enabled = Column(Boolean, default=True)
    contactless_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    parent_card_id = Column(Integer, nullable=True)


class CardTransaction(Base):
    __tablename__ = "card_transactions"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"), index=True)
    amount = Column(Money, nullable=False)
    merchant = Column(String, nullable=True)
    currency = Column(String, default="BRL")
    status = Column(String, default="POSTED")
    posted_at = Column(DateTime, default=datetime.utcnow)
    description = Column(String, nullable=True)


class CardInvoice(Base):
    __tablename__ = "card_invoices"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"), index=True)
    total = Column(Money, default=0)
    status = Column(String, default="OPEN")  # OPEN, CLOSED, PAID
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
