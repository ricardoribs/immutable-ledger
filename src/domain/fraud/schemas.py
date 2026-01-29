from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FraudScoreResponse(BaseModel):
    id: int
    account_id: int
    transaction_id: Optional[int] = None
    score: float
    action: Optional[str] = None
    rules: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
