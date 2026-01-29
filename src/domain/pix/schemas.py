from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PixChargeCreate(BaseModel):
    amount: Optional[float] = None
    description: Optional[str] = None
    expires_at: Optional[datetime] = None


class PixChargePay(BaseModel):
    charge_id: int
    amount: Optional[float] = None


class PixChargeResponse(PixChargeCreate):
    id: int
    status: str
    created_at: datetime
    paid_at: Optional[datetime] = None
    payer_account_id: Optional[int] = None
    tx_id: str
    payload: Optional[str] = None
    qr_code_base64: Optional[str] = None

    class Config:
        from_attributes = True


class PixRefundCreate(BaseModel):
    charge_id: int
    amount: float
    reason: Optional[str] = None


class PixRefundResponse(PixRefundCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PixLimitUpdate(BaseModel):
    day_limit: float
    night_limit: float
    per_tx_limit: float
    monthly_limit: float


class PixLimitResponse(PixLimitUpdate):
    id: int
    account_id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class PixScheduleCreate(BaseModel):
    pix_key: str
    amount: float
    scheduled_for: datetime


class PixScheduleResponse(PixScheduleCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
