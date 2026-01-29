from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.api import deps
from src.domain.settings import schemas, services

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/profile", response_model=schemas.UserProfileResponse)
async def get_profile(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.SettingsService.get_or_create_profile(db, current_account.owner.id)


@router.post("/profile", response_model=schemas.UserProfileResponse)
async def update_profile(
    data: schemas.UserProfileUpdate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.SettingsService.update_profile(db, current_account.owner.id, data)


@router.get("/notifications", response_model=schemas.NotificationPreferenceResponse)
async def get_notifications(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.SettingsService.get_or_create_notifications(db, current_account.owner.id)


@router.post("/notifications", response_model=schemas.NotificationPreferenceResponse)
async def update_notifications(
    data: schemas.NotificationPreferenceUpdate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.SettingsService.update_notifications(db, current_account.owner.id, data)


@router.get("/limits", response_model=schemas.LimitConfigResponse)
async def get_limits(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.SettingsService.get_or_create_limits(db, current_account.owner.id)


@router.post("/limits", response_model=schemas.LimitConfigResponse)
async def update_limits(
    data: schemas.LimitConfigUpdate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.SettingsService.update_limits(db, current_account.owner.id, data)


@router.get("/accessibility", response_model=schemas.AccessibilityPreferenceResponse)
async def get_accessibility(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.SettingsService.get_or_create_accessibility(db, current_account.owner.id)


@router.post("/accessibility", response_model=schemas.AccessibilityPreferenceResponse)
async def update_accessibility(
    data: schemas.AccessibilityPreferenceUpdate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.SettingsService.update_accessibility(db, current_account.owner.id, data)


@router.get("/privacy", response_model=schemas.PrivacyPreferenceResponse)
async def get_privacy(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.SettingsService.get_or_create_privacy(db, current_account.owner.id)


@router.post("/privacy", response_model=schemas.PrivacyPreferenceResponse)
async def update_privacy(
    data: schemas.PrivacyPreferenceUpdate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.SettingsService.update_privacy(db, current_account.owner.id, data)
