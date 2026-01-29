from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TicketCreate(BaseModel):
    subject: str
    message: str


class TicketResponse(BaseModel):
    id: int
    subject: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TicketMessageCreate(BaseModel):
    ticket_id: int
    message: str


class TicketMessageResponse(BaseModel):
    id: int
    ticket_id: int
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class FaqResponse(BaseModel):
    id: int
    question: str
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatbotRequest(BaseModel):
    message: str


class ChatbotResponse(BaseModel):
    answer: str
    from_faq: bool
    ticket_id: Optional[int] = None
