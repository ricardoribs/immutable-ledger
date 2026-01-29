from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from datetime import datetime

from src.infra.database import Base


class FraudScore(Base):
    __tablename__ = "fraud_scores"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    score = Column(Float, default=0.0)
    action = Column(String, nullable=True)  # ALLOW, VERIFY, BLOCK
    rules = Column(Text, nullable=True)
    features = Column(Text, nullable=True)
    model_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FraudModelMeta(Base):
    __tablename__ = "fraud_models"

    id = Column(Integer, primary_key=True, index=True)
    model_type = Column(String, nullable=False)  # IF, XGB
    version = Column(String, nullable=False)
    trained_at = Column(DateTime, default=datetime.utcnow)
    metrics = Column(Text, nullable=True)


class FraudTeamAlert(Base):
    __tablename__ = "fraud_team_alerts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    severity = Column(String, default="HIGH")
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
