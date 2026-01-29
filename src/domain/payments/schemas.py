from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BeneficiaryCreate(BaseModel):
    name: str
    bank_code: Optional[str] = None
    agency: Optional[str] = None
    account: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    pix_key: Optional[str] = None
    favorite: bool = False


class BeneficiaryResponse(BeneficiaryCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    account_id: int
    payment_type: str
    amount: float
    description: Optional[str] = None
    beneficiary_id: Optional[int] = None
    scheduled_for: Optional[datetime] = None
    to_account_id: Optional[int] = None


class PaymentResponse(PaymentCreate):
    id: int
    status: str
    fee_amount: float = 0.0
    spb_protocol: Optional[str] = None
    executed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RecurringPaymentCreate(BaseModel):
    account_id: int
    beneficiary_id: Optional[int] = None
    payment_type: str
    amount: float
    interval_days: int = 30
    next_run_at: Optional[datetime] = None


class RecurringPaymentResponse(RecurringPaymentCreate):
    id: int
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True
