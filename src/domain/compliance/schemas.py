from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ConsentCreate(BaseModel):
    consent_type: str
    details: Optional[str] = None


class ConsentResponse(BaseModel):
    id: int
    consent_type: str
    details: Optional[str] = None
    given_at: datetime
    revoked: bool
    revoked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ForgetRequestResponse(BaseModel):
    id: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DataReportResponse(BaseModel):
    user_id: int
    name: str
    email: str
    cpf_last4: Optional[str] = None
    consents: List[ConsentResponse] = []
