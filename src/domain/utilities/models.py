from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Text
from datetime import datetime

from src.infra.database import Base
from src.domain.common.types import Money


class UtilityOrder(Base):
    __tablename__ = "utility_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    utility_type = Column(String, nullable=False)  # RECHARGE, TV, INTERNET, BILLS
    provider = Column(String, nullable=True)
    amount = Column(Money, nullable=False)
    status = Column(String, default="COMPLETED")
    created_at = Column(DateTime, default=datetime.utcnow)


class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    organization = Column(String, nullable=False)
    amount = Column(Money, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class FxOrder(Base):
    __tablename__ = "fx_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    currency = Column(String, nullable=False)
    amount = Column(Money, nullable=False)
    rate = Column(Float, nullable=False)
    status = Column(String, default="COMPLETED")
    created_at = Column(DateTime, default=datetime.utcnow)
