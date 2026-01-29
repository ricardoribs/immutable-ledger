from celery import Celery
from src.core.config import settings

celery_app = Celery(
    "ledger",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    beat_schedule={},
)

try:
    import src.domain.tasks  # noqa: F401
except Exception:
    pass
