from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.domain.feature_flags import schemas, services

router = APIRouter(prefix="/feature-flags", tags=["FeatureFlags"])


@router.post("/", response_model=schemas.FeatureFlagResponse)
async def set_flag(
    data: schemas.FeatureFlagCreate,
    db: AsyncSession = Depends(get_db),
):
    return await services.FeatureFlagService.set_flag(db, data)


@router.get("/", response_model=list[schemas.FeatureFlagResponse])
async def list_flags(db: AsyncSession = Depends(get_db)):
    return await services.FeatureFlagService.list_flags(db)
