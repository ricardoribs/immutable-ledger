from pydantic import BaseModel
from datetime import datetime


class UtilityOrderCreate(BaseModel):
    utility_type: str
    provider: str | None = None
    amount: float


class UtilityOrderResponse(UtilityOrderCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DonationCreate(BaseModel):
    organization: str
    amount: float


class DonationResponse(DonationCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FxOrderCreate(BaseModel):
    currency: str
    amount: float
    rate: float


class FxOrderResponse(FxOrderCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
