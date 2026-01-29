from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from datetime import datetime

from src.infra.database import Base


class ChurnModel(Base):
    __tablename__ = "churn_models"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, nullable=False)
    metrics = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChurnPrediction(Base):
    __tablename__ = "churn_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
