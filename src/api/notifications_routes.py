from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.api import deps
from src.domain.notifications import schemas, services

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/", response_model=schemas.NotificationResponse)
async def send_notification(
    data: schemas.NotificationCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.NotificationService.send(db, current_account.owner.id, data)


@router.get("/", response_model=list[schemas.NotificationResponse])
async def list_notifications(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.NotificationService.list_user(db, current_account.owner.id)
