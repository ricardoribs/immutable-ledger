from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.api import deps
from src.domain.pj import schemas, services

router = APIRouter(prefix="/pj", tags=["PJ"])


@router.post("/businesses", response_model=schemas.BusinessResponse)
async def create_business(
    data: schemas.BusinessCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.PjService.create_business(db, current_account.owner.id, data)


@router.get("/businesses", response_model=list[schemas.BusinessResponse])
async def list_businesses(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.PjService.list_businesses(db, current_account.owner.id)


@router.post("/batch-payments", response_model=schemas.BatchPaymentResponse)
async def create_batch_payment(
    data: schemas.BatchPaymentCreate,
    db: AsyncSession = Depends(get_db),
):
    return await services.PjService.create_batch_payment(db, data)


@router.post("/payroll", response_model=schemas.PayrollRunResponse)
async def create_payroll(
    data: schemas.PayrollRunCreate,
    db: AsyncSession = Depends(get_db),
):
    return await services.PjService.create_payroll_run(db, data)
