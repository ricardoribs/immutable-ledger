from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from datetime import datetime

from src.infra.database import Base
from src.domain.common.types import Money


class PixCharge(Base):
    __tablename__ = "pix_charges"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    amount = Column(Money, nullable=True)  # None = charge without fixed amount
    description = Column(Text, nullable=True)
    status = Column(String, default="PENDING")  # PENDING, PAID, CANCELED
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    payer_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    tx_id = Column(String, unique=True, index=True)
    payload = Column(Text, nullable=True)
    qr_code_base64 = Column(Text, nullable=True)


class PixRefund(Base):
    __tablename__ = "pix_refunds"

    id = Column(Integer, primary_key=True, index=True)
    charge_id = Column(Integer, ForeignKey("pix_charges.id"), index=True)
    amount = Column(Money, nullable=False)
    reason = Column(String, nullable=True)
    status = Column(String, default="PENDING")  # PENDING, COMPLETED
    created_at = Column(DateTime, default=datetime.utcnow)


class PixLimit(Base):
    __tablename__ = "pix_limits"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True, unique=True)
    day_limit = Column(Money, default=10000)
    night_limit = Column(Money, default=1000)
    per_tx_limit = Column(Money, default=1000)
    monthly_limit = Column(Money, default=50000)
    updated_at = Column(DateTime, default=datetime.utcnow)


class PixSchedule(Base):
    __tablename__ = "pix_schedules"

    id = Column(Integer, primary_key=True, index=True)
    from_account_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    pix_key = Column(String, nullable=False)
    amount = Column(Money, nullable=False)
    scheduled_for = Column(DateTime, nullable=False)
    status = Column(String, default="SCHEDULED")  # SCHEDULED, CANCELED, EXECUTED
    created_at = Column(DateTime, default=datetime.utcnow)
