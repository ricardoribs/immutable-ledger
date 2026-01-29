from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NotificationCreate(BaseModel):
    channel: str
    subject: Optional[str] = None
    message: str


class NotificationResponse(NotificationCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
