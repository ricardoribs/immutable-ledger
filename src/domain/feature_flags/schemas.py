from pydantic import BaseModel
from datetime import datetime


class FeatureFlagCreate(BaseModel):
    name: str
    enabled: bool = False


class FeatureFlagResponse(FeatureFlagCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
