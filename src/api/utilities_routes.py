from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.api import deps
from src.domain.utilities import schemas, services

router = APIRouter(prefix="/utilities", tags=["Utilities"])


@router.post("/", response_model=schemas.UtilityOrderResponse)
async def create_utility(
    data: schemas.UtilityOrderCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.UtilitiesService.create_utility(db, current_account.owner.id, data)


@router.get("/", response_model=list[schemas.UtilityOrderResponse])
async def list_utilities(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.UtilitiesService.list_utilities(db, current_account.owner.id)


@router.post("/donations", response_model=schemas.DonationResponse)
async def create_donation(
    data: schemas.DonationCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.UtilitiesService.create_donation(db, current_account.owner.id, data)


@router.get("/donations", response_model=list[schemas.DonationResponse])
async def list_donations(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.UtilitiesService.list_donations(db, current_account.owner.id)


@router.post("/fx", response_model=schemas.FxOrderResponse)
async def create_fx(
    data: schemas.FxOrderCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.UtilitiesService.create_fx_order(db, current_account.owner.id, data)


@router.get("/fx", response_model=list[schemas.FxOrderResponse])
async def list_fx(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.UtilitiesService.list_fx_orders(db, current_account.owner.id)
