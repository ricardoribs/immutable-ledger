from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime

from src.infra.database import Base
from src.domain.common.types import Money


class ReconciliationReport(Base):
    __tablename__ = "reconciliation_reports"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="COMPLETED")
    total_accounts = Column(Integer, default=0)
    discrepancies = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ReconciliationDiscrepancy(Base):
    __tablename__ = "reconciliation_discrepancies"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reconciliation_reports.id"), index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    expected_balance = Column(Money, nullable=False)
    actual_balance = Column(Money, nullable=False)
    delta = Column(Money, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
