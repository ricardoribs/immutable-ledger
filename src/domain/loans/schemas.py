from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class LoanSimulateRequest(BaseModel):
    principal: float
    rate_monthly: float
    term_months: int
    amortization_type: str = "PRICE"


class LoanSimulateResponse(BaseModel):
    principal: float
    rate_monthly: float
    term_months: int
    installment_amount: float
    total_payable: float
    amortization_type: str


class LoanCreate(BaseModel):
    account_id: int
    loan_type: str
    principal: float
    rate_monthly: float
    term_months: int
    amortization_type: str = "PRICE"


class LoanResponse(LoanCreate):
    id: int
    status: str
    credit_score: int
    iof_amount: float
    fees_amount: float
    created_at: datetime

    class Config:
        from_attributes = True


class LoanInstallmentResponse(BaseModel):
    id: int
    loan_id: int
    due_date: datetime
    amount: float
    paid: bool

    class Config:
        from_attributes = True
