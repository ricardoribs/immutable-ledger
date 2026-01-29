from fastapi import FastAPI, Request
import logging
import httpx
from aiosmtplib import SMTP
from src.core.config import settings

app = FastAPI(title="Alert Router")

logger = logging.getLogger("alert_router")
logging.basicConfig(level=logging.INFO)


@app.post("/alert")
async def receive_alert(request: Request):
    payload = await request.json()
    logger.info("ALERT_RECEIVED %s", payload)
    try:
        smtp = SMTP(hostname=settings.SMTP_HOST, port=settings.SMTP_PORT)
        await smtp.connect()
        await smtp.sendmail(
            "no-reply@luisbank.local",
            ["alerts@luisbank.local"],
            "Subject: Alert\n\nAlert received",
        )
        await smtp.quit()
    except Exception:
        pass
    async with httpx.AsyncClient() as client:
        await client.post(settings.SMS_GATEWAY_URL, json={"to": "0000000000", "message": "ALERT"})
        await client.post(settings.WHATSAPP_GATEWAY_URL, json={"to": "0000000000", "message": "ALERT"})
        await client.post(settings.PUSH_GATEWAY_URL, json={"title": "ALERT", "message": "ALERT"})
        await client.post(settings.SLACK_WEBHOOK_URL, json={"text": "ALERT"})
        await client.post(settings.PAGERDUTY_WEBHOOK_URL, json={"event": "ALERT"})
    return {"status": "ok"}
