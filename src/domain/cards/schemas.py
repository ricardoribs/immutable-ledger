from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CardCreate(BaseModel):
    account_id: int
    card_type: str
    limit_total: float = 0.0
    due_day: int = 10
    parent_card_id: Optional[int] = None


class CardResponse(CardCreate):
    id: int
    last4: str
    card_token: Optional[str] = None
    status: str
    limit_available: float
    cashback_balance: float
    points_balance: int
    international_enabled: bool
    online_enabled: bool
    contactless_enabled: bool
    created_at: datetime
    parent_card_id: Optional[int] = None

    class Config:
        from_attributes = True


class CardControlUpdate(BaseModel):
    international_enabled: bool
    online_enabled: bool
    contactless_enabled: bool


class CardTransactionCreate(BaseModel):
    card_id: int
    amount: float
    merchant: Optional[str] = None
    channel: str  # ONLINE, IN_PERSON, CONTACTLESS
    description: Optional[str] = None


class CardTransactionResponse(BaseModel):
    id: int
    card_id: int
    amount: float
    merchant: Optional[str] = None
    currency: str
    status: str
    posted_at: datetime
    description: Optional[str] = None

    class Config:
        from_attributes = True


class CardInvoiceResponse(BaseModel):
    id: int
    card_id: int
    total: float
    status: str
    due_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
