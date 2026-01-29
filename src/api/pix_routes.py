from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.api import deps
from src.domain.pix import schemas, services

router = APIRouter(prefix="/pix", tags=["Pix"])


@router.post("/charges", response_model=schemas.PixChargeResponse)
async def create_charge(
    data: schemas.PixChargeCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.PixService.create_charge(db, current_account.id, data)


@router.get("/charges", response_model=list[schemas.PixChargeResponse])
async def list_charges(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.PixService.list_charges(db, current_account.id)


@router.post("/refunds", response_model=schemas.PixRefundResponse)
async def create_refund(
    data: schemas.PixRefundCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await services.PixService.create_refund(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/charges/pay", response_model=schemas.PixChargeResponse)
async def pay_charge(
    data: schemas.PixChargePay,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await services.PixService.pay_charge(db, current_account.id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/limits", response_model=schemas.PixLimitResponse)
async def get_limits(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.PixService.get_limits(db, current_account.id)


@router.post("/limits", response_model=schemas.PixLimitResponse)
async def update_limits(
    data: schemas.PixLimitUpdate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.PixService.update_limits(db, current_account.id, data)


@router.post("/schedules", response_model=schemas.PixScheduleResponse)
async def create_schedule(
    data: schemas.PixScheduleCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await services.PixService.create_schedule(db, current_account.id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/schedules", response_model=list[schemas.PixScheduleResponse])
async def list_schedules(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.PixService.list_schedules(db, current_account.id)
