from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BusinessCreate(BaseModel):
    name: str
    cnpj: str


class BusinessResponse(BusinessCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BatchPaymentCreate(BaseModel):
    business_id: int
    total_amount: float


class BatchPaymentResponse(BatchPaymentCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PayrollItemCreate(BaseModel):
    employee_name: str
    employee_document: str
    amount: float


class PayrollRunCreate(BaseModel):
    business_id: int
    total_amount: float
    items: List[PayrollItemCreate] = []


class PayrollRunResponse(BaseModel):
    id: int
    business_id: int
    total_amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
