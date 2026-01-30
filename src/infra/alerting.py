import httpx
from src.core.config import settings


async def send_alert(event: str, severity: str, details: str | None = None) -> None:
    payload = {
        "event": event,
        "severity": severity,
        "details": details or "",
        "service": "ledger-api",
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(settings.ALERT_ROUTER_URL, json=payload)
    except Exception:
        return None
