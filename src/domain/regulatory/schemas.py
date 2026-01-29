from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class KycCreate(BaseModel):
    document_id: str


class KycResponse(BaseModel):
    id: int
    status: str
    risk_level: str
    document_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AmlAlertResponse(BaseModel):
    id: int
    rule: str
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    id: int
    period: str
    content: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
