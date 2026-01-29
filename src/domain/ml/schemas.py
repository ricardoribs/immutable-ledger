from pydantic import BaseModel
from datetime import datetime


class ChurnPredictionResponse(BaseModel):
    id: int
    user_id: int
    score: float
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    id: int
    user_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
