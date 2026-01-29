from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from datetime import datetime

from src.infra.database import Base
from src.domain.common.types import Money


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String, nullable=False)
    cnpj = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BatchPayment(Base):
    __tablename__ = "batch_payments"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), index=True)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Money, default=0)


class PayrollRun(Base):
    __tablename__ = "payroll_runs"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), index=True)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Money, default=0)


class PayrollItem(Base):
    __tablename__ = "payroll_items"

    id = Column(Integer, primary_key=True, index=True)
    payroll_id = Column(Integer, ForeignKey("payroll_runs.id"), index=True)
    employee_name = Column(String, nullable=False)
    employee_document = Column(String, nullable=False)
    amount = Column(Money, nullable=False)
