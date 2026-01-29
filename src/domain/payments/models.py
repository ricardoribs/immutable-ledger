from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from datetime import datetime

from src.infra.database import Base
from src.domain.common.types import Money


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String, nullable=False)
    bank_code = Column(String, nullable=True)
    agency = Column(String, nullable=True)
    account = Column(String, nullable=True)
    cpf_cnpj = Column(String, nullable=True)
    pix_key = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    favorite = Column(Boolean, default=False)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    beneficiary_id = Column(Integer, ForeignKey("beneficiaries.id"), nullable=True)
    payment_type = Column(String, nullable=False)  # TED, DOC, INTERNAL, BOLETO, UTILITY, TAX, RECHARGE
    amount = Column(Money, nullable=False)
    fee_amount = Column(Money, default=0)
    description = Column(Text, nullable=True)
    status = Column(String, default="PENDING")
    scheduled_for = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    to_account_id = Column(Integer, nullable=True)
    spb_protocol = Column(String, nullable=True)


class RecurringPayment(Base):
    __tablename__ = "recurring_payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    beneficiary_id = Column(Integer, ForeignKey("beneficiaries.id"), nullable=True)
    payment_type = Column(String, nullable=False)
    amount = Column(Money, nullable=False)
    interval_days = Column(Integer, default=30)
    next_run_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
