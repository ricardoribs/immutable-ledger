from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class InsurancePolicyCreate(BaseModel):
    policy_type: str
    premium: float
    details: Optional[str] = None


class InsurancePolicyResponse(InsurancePolicyCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class InsuranceClaimCreate(BaseModel):
    policy_id: int
    description: Optional[str] = None


class InsuranceClaimResponse(InsuranceClaimCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
