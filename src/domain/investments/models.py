from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime

from src.infra.database import Base
from src.domain.common.types import Money


class InvestmentProduct(Base):
    __tablename__ = "investment_products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    product_type = Column(String, nullable=False)  # CDB, LCI, LCA, TESOURO, FUND, STOCK
    rate = Column(Float, default=0.0)
    liquidity = Column(String, default="D+0")
    created_at = Column(DateTime, default=datetime.utcnow)


class InvestmentHolding(Base):
    __tablename__ = "investment_holdings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    product_id = Column(Integer, ForeignKey("investment_products.id"), index=True)
    quantity = Column(Float, default=0.0)
    average_price = Column(Money, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class InvestmentOrder(Base):
    __tablename__ = "investment_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    product_id = Column(Integer, ForeignKey("investment_products.id"), index=True)
    order_type = Column(String, nullable=False)  # BUY, SELL
    amount = Column(Money, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AutoInvestConfig(Base):
    __tablename__ = "auto_invest_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, unique=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    product_id = Column(Integer, ForeignKey("investment_products.id"), index=True)
    min_balance = Column(Money, default=1000)
    enabled = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
