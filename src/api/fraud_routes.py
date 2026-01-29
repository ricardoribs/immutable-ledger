from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.api.dependencies import get_db
from src.api import deps
from src.domain.fraud import schemas, models

router = APIRouter(prefix="/fraud", tags=["Fraud"])


@router.get("/scores", response_model=list[schemas.FraudScoreResponse])
async def list_scores(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(models.FraudScore).where(models.FraudScore.account_id == current_account.id)
    res = await db.execute(stmt)
    return res.scalars().all()
