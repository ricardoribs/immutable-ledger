from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BoletoCreate(BaseModel):
    amount: float
    description: Optional[str] = None
    due_date: datetime


class BoletoResponse(BoletoCreate):
    id: int
    status: str
    barcode: str
    digitable_line: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentLinkCreate(BaseModel):
    amount: float


class PaymentLinkResponse(PaymentLinkCreate):
    id: int
    status: str
    url: str
    created_at: datetime

    class Config:
        from_attributes = True


class PosSaleCreate(BaseModel):
    amount: float


class PosSaleResponse(PosSaleCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SplitRuleCreate(BaseModel):
    name: str
    percentage: float


class SplitRuleResponse(SplitRuleCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BoletoPay(BaseModel):
    boleto_id: int
