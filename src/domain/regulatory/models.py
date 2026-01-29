from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from datetime import datetime

from src.infra.database import Base


class KycProfile(Base):
    __tablename__ = "kyc_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, unique=True)
    status = Column(String, default="PENDING")  # PENDING, VERIFIED, REJECTED
    risk_level = Column(String, default="MEDIUM")
    document_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AmlAlert(Base):
    __tablename__ = "aml_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    rule = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CoafReport(Base):
    __tablename__ = "coaf_reports"

    id = Column(Integer, primary_key=True, index=True)
    period = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScrReport(Base):
    __tablename__ = "scr_reports"

    id = Column(Integer, primary_key=True, index=True)
    period = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
