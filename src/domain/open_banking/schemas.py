from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ConsentCreate(BaseModel):
    institution: str
    scope: Optional[str] = None


class ConsentResponse(ConsentCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ExternalAccountCreate(BaseModel):
    institution: str
    account_ref: str
    balance: float = 0.0


class ExternalAccountResponse(ExternalAccountCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class OpenBankingPaymentCreate(BaseModel):
    amount: float


class OpenBankingPaymentResponse(OpenBankingPaymentCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
