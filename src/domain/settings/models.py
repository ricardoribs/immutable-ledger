from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Float, Text
from datetime import datetime

from src.infra.database import Base
from src.domain.common.types import Money


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, unique=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, unique=True)
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    whatsapp_enabled = Column(Boolean, default=False)
    quiet_hours = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


class LimitConfig(Base):
    __tablename__ = "limit_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, unique=True)
    pix_limit = Column(Money, default=1000)
    ted_limit = Column(Money, default=5000)
    doc_limit = Column(Money, default=5000)
    withdrawal_limit = Column(Money, default=1000)
    updated_at = Column(DateTime, default=datetime.utcnow)


class AccessibilityPreference(Base):
    __tablename__ = "accessibility_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, unique=True)
    dark_mode = Column(Boolean, default=False)
    font_scale = Column(Float, default=1.0)
    high_contrast = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow)


class PrivacyPreference(Base):
    __tablename__ = "privacy_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, unique=True)
    share_data = Column(Boolean, default=False)
    marketing_emails = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow)
