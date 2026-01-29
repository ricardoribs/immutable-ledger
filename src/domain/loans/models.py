from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Boolean
from datetime import datetime

from src.infra.database import Base
from src.domain.common.types import Money


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    loan_type = Column(String, nullable=False)  # PERSONAL, CONSIGNADO, VEHICLE, HOME
    principal = Column(Money, nullable=False)
    rate_monthly = Column(Float, nullable=False)
    term_months = Column(Integer, nullable=False)
    amortization_type = Column(String, default="PRICE")  # PRICE, SAC
    credit_score = Column(Integer, default=0)
    iof_amount = Column(Money, default=0)
    fees_amount = Column(Money, default=0)
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)


class LoanInstallment(Base):
    __tablename__ = "loan_installments"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), index=True)
    due_date = Column(DateTime, nullable=False)
    amount = Column(Money, nullable=False)
    paid = Column(Boolean, default=False)


class LoanCharge(Base):
    __tablename__ = "loan_charges"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), index=True)
    charge_type = Column(String, nullable=False)  # IOF, PENALTY, INTEREST
    amount = Column(Money, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
