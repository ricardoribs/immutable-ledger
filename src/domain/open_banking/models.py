from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from datetime import datetime

from src.infra.database import Base
from src.domain.common.types import Money


class Consent(Base):
    __tablename__ = "open_banking_consents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    institution = Column(String, nullable=False)
    scope = Column(Text, nullable=True)
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)


class ExternalAccount(Base):
    __tablename__ = "external_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    institution = Column(String, nullable=False)
    account_ref = Column(String, nullable=False)
    balance = Column(Money, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class OpenBankingPayment(Base):
    __tablename__ = "open_banking_payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    amount = Column(Money, nullable=False)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
