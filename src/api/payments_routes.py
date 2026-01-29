from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.api import deps
from src.domain.payments import schemas, services

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/beneficiaries", response_model=schemas.BeneficiaryResponse)
async def create_beneficiary(
    data: schemas.BeneficiaryCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.PaymentService.create_beneficiary(db, current_account.owner.id, data)


@router.get("/beneficiaries", response_model=list[schemas.BeneficiaryResponse])
async def list_beneficiaries(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.PaymentService.list_beneficiaries(db, current_account.owner.id)


@router.post("/", response_model=schemas.PaymentResponse)
async def create_payment(
    data: schemas.PaymentCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await services.PaymentService.create_payment(db, current_account.owner.id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[schemas.PaymentResponse])
async def list_payments(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.PaymentService.list_payments(db, current_account.owner.id)


@router.post("/recurring", response_model=schemas.RecurringPaymentResponse)
async def create_recurring(
    data: schemas.RecurringPaymentCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.PaymentService.create_recurring(db, current_account.owner.id, data)


@router.get("/recurring", response_model=list[schemas.RecurringPaymentResponse])
async def list_recurring(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.PaymentService.list_recurring(db, current_account.owner.id)
