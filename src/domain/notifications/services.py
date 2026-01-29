from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from src.core.config import settings
from src.domain.settings import services as settings_services

from src.domain.notifications import models, schemas


class NotificationService:
    @staticmethod
    async def send(db: AsyncSession, user_id: int, data: schemas.NotificationCreate) -> models.Notification:
        prefs = await settings_services.SettingsService.get_or_create_notifications(db, user_id)
        channel = data.channel.upper()
        if channel == "EMAIL" and not prefs.email_enabled:
            notif = models.Notification(
                user_id=user_id, channel=channel, subject=data.subject, message=data.message, status="SKIPPED"
            )
            db.add(notif)
            await db.commit()
            return notif
        if channel == "SMS" and not prefs.sms_enabled:
            notif = models.Notification(
                user_id=user_id, channel=channel, subject=data.subject, message=data.message, status="SKIPPED"
            )
            db.add(notif)
            await db.commit()
            return notif
        if channel == "PUSH" and not prefs.push_enabled:
            notif = models.Notification(
                user_id=user_id, channel=channel, subject=data.subject, message=data.message, status="SKIPPED"
            )
            db.add(notif)
            await db.commit()
            return notif
        if channel == "WHATSAPP" and not prefs.whatsapp_enabled:
            notif = models.Notification(
                user_id=user_id, channel=channel, subject=data.subject, message=data.message, status="SKIPPED"
            )
            db.add(notif)
            await db.commit()
            return notif

        status = "SENT"
        try:
            if channel == "EMAIL":
                from aiosmtplib import SMTP
                smtp = SMTP(hostname=settings.SMTP_HOST, port=settings.SMTP_PORT)
                await smtp.connect()
                await smtp.sendmail(
                    "no-reply@luisbank.local",
                    ["user@local.test"],
                    f"Subject: {data.subject or 'Notificacao'}\n\n{data.message}",
                )
                await smtp.quit()
            elif channel == "SMS":
                async with httpx.AsyncClient() as client:
                    await client.post(settings.SMS_GATEWAY_URL, json={"to": "0000000000", "message": data.message})
            elif channel == "WHATSAPP":
                async with httpx.AsyncClient() as client:
                    await client.post(settings.WHATSAPP_GATEWAY_URL, json={"to": "0000000000", "message": data.message})
            elif channel == "PUSH":
                async with httpx.AsyncClient() as client:
                    await client.post(settings.PUSH_GATEWAY_URL, json={"title": data.subject or "Notificacao", "message": data.message})
        except Exception:
            status = "FAILED"

        notif = models.Notification(
            user_id=user_id,
            channel=data.channel.upper(),
            subject=data.subject,
            message=data.message,
            status=status,
        )
        db.add(notif)
        await db.commit()
        return notif

    @staticmethod
    async def list_user(db: AsyncSession, user_id: int):
        stmt = select(models.Notification).where(models.Notification.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()
