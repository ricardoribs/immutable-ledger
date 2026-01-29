from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.settings import models, schemas


class SettingsService:
    @staticmethod
    async def get_or_create_profile(db: AsyncSession, user_id: int):
        stmt = select(models.UserProfile).where(models.UserProfile.user_id == user_id)
        res = await db.execute(stmt)
        profile = res.scalar_one_or_none()
        if not profile:
            profile = models.UserProfile(user_id=user_id)
            db.add(profile)
            await db.commit()
        return profile

    @staticmethod
    async def update_profile(db: AsyncSession, user_id: int, data: schemas.UserProfileUpdate):
        profile = await SettingsService.get_or_create_profile(db, user_id)
        profile.phone = data.phone
        profile.address = data.address
        await db.commit()
        return profile

    @staticmethod
    async def get_or_create_notifications(db: AsyncSession, user_id: int):
        stmt = select(models.NotificationPreference).where(models.NotificationPreference.user_id == user_id)
        res = await db.execute(stmt)
        pref = res.scalar_one_or_none()
        if not pref:
            pref = models.NotificationPreference(user_id=user_id)
            db.add(pref)
            await db.commit()
        return pref

    @staticmethod
    async def update_notifications(db: AsyncSession, user_id: int, data: schemas.NotificationPreferenceUpdate):
        pref = await SettingsService.get_or_create_notifications(db, user_id)
        pref.email_enabled = data.email_enabled
        pref.sms_enabled = data.sms_enabled
        pref.push_enabled = data.push_enabled
        pref.whatsapp_enabled = data.whatsapp_enabled
        pref.quiet_hours = data.quiet_hours
        pref.updated_at = datetime.utcnow()
        await db.commit()
        return pref

    @staticmethod
    async def get_or_create_limits(db: AsyncSession, user_id: int):
        stmt = select(models.LimitConfig).where(models.LimitConfig.user_id == user_id)
        res = await db.execute(stmt)
        cfg = res.scalar_one_or_none()
        if not cfg:
            cfg = models.LimitConfig(user_id=user_id)
            db.add(cfg)
            await db.commit()
        return cfg

    @staticmethod
    async def update_limits(db: AsyncSession, user_id: int, data: schemas.LimitConfigUpdate):
        cfg = await SettingsService.get_or_create_limits(db, user_id)
        cfg.pix_limit = data.pix_limit
        cfg.ted_limit = data.ted_limit
        cfg.doc_limit = data.doc_limit
        cfg.withdrawal_limit = data.withdrawal_limit
        cfg.updated_at = datetime.utcnow()
        await db.commit()
        return cfg

    @staticmethod
    async def get_or_create_accessibility(db: AsyncSession, user_id: int):
        stmt = select(models.AccessibilityPreference).where(models.AccessibilityPreference.user_id == user_id)
        res = await db.execute(stmt)
        pref = res.scalar_one_or_none()
        if not pref:
            pref = models.AccessibilityPreference(user_id=user_id)
            db.add(pref)
            await db.commit()
        return pref

    @staticmethod
    async def update_accessibility(db: AsyncSession, user_id: int, data: schemas.AccessibilityPreferenceUpdate):
        pref = await SettingsService.get_or_create_accessibility(db, user_id)
        pref.dark_mode = data.dark_mode
        pref.font_scale = data.font_scale
        pref.high_contrast = data.high_contrast
        pref.updated_at = datetime.utcnow()
        await db.commit()
        return pref

    @staticmethod
    async def get_or_create_privacy(db: AsyncSession, user_id: int):
        stmt = select(models.PrivacyPreference).where(models.PrivacyPreference.user_id == user_id)
        res = await db.execute(stmt)
        pref = res.scalar_one_or_none()
        if not pref:
            pref = models.PrivacyPreference(user_id=user_id)
            db.add(pref)
            await db.commit()
        return pref

    @staticmethod
    async def update_privacy(db: AsyncSession, user_id: int, data: schemas.PrivacyPreferenceUpdate):
        pref = await SettingsService.get_or_create_privacy(db, user_id)
        pref.share_data = data.share_data
        pref.marketing_emails = data.marketing_emails
        pref.updated_at = datetime.utcnow()
        await db.commit()
        return pref
