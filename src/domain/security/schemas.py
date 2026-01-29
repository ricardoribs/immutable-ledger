from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class DeviceResponse(BaseModel):
    id: int
    name: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    fingerprint: Optional[str] = None
    trusted: bool
    last_seen_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: int
    jti: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    revoked: bool

    class Config:
        from_attributes = True


class SecurityAlertResponse(BaseModel):
    id: int
    alert_type: str
    details: Optional[str] = None
    created_at: datetime
    resolved: bool

    class Config:
        from_attributes = True


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class OtpRequest(BaseModel):
    channel: str


class OtpVerify(BaseModel):
    channel: str
    code: str


class SecurityQuestionCreate(BaseModel):
    question: str
    answer: str


class SecurityQuestionResponse(BaseModel):
    id: int
    question: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    action: str
    method: Optional[str] = None
    path: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    record_hash: Optional[str] = None

    class Config:
        from_attributes = True
