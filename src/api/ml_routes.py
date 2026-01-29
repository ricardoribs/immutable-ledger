from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.api.dependencies import get_db
from src.api import deps
from src.domain.ml import schemas, services, models

router = APIRouter(prefix="/ml", tags=["ML"])


@router.post("/churn", response_model=schemas.ChurnPredictionResponse)
async def predict_churn(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.MlService.predict_churn(db, current_account.owner.id)


@router.post("/recommendations", response_model=list[schemas.RecommendationResponse])
async def generate_recommendations(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    await services.MlService.generate_recommendations(db, current_account.owner.id)
    stmt = select(models.Recommendation).where(models.Recommendation.user_id == current_account.owner.id)
    res = await db.execute(stmt)
    return res.scalars().all()
