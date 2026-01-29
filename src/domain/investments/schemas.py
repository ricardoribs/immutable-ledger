from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class InvestmentProductCreate(BaseModel):
    name: str
    product_type: str
    rate: float = 0.0
    liquidity: str = "D+0"


class InvestmentProductResponse(InvestmentProductCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class InvestmentOrderCreate(BaseModel):
    account_id: int
    product_id: int
    order_type: str
    amount: float


class InvestmentOrderResponse(InvestmentOrderCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class InvestmentHoldingResponse(BaseModel):
    id: int
    account_id: int
    product_id: int
    quantity: float
    average_price: float
    created_at: datetime

    class Config:
        from_attributes = True


class AutoInvestCreate(BaseModel):
    account_id: int
    product_id: int
    min_balance: float = 1000.0
    enabled: bool = True


class AutoInvestResponse(AutoInvestCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
