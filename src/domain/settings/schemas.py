from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserProfileUpdate(BaseModel):
    phone: Optional[str] = None
    address: Optional[str] = None


class UserProfileResponse(UserProfileUpdate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferenceUpdate(BaseModel):
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    whatsapp_enabled: bool
    quiet_hours: Optional[str] = None


class NotificationPreferenceResponse(NotificationPreferenceUpdate):
    id: int
    user_id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class LimitConfigUpdate(BaseModel):
    pix_limit: float
    ted_limit: float
    doc_limit: float
    withdrawal_limit: float


class LimitConfigResponse(LimitConfigUpdate):
    id: int
    user_id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class AccessibilityPreferenceUpdate(BaseModel):
    dark_mode: bool
    font_scale: float
    high_contrast: bool


class AccessibilityPreferenceResponse(AccessibilityPreferenceUpdate):
    id: int
    user_id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class PrivacyPreferenceUpdate(BaseModel):
    share_data: bool
    marketing_emails: bool


class PrivacyPreferenceResponse(PrivacyPreferenceUpdate):
    id: int
    user_id: int
    updated_at: datetime

    class Config:
        from_attributes = True
