from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.api import deps
from src.domain.open_banking import schemas, services

router = APIRouter(prefix="/open-banking", tags=["Open Banking"])


@router.post("/consents", response_model=schemas.ConsentResponse)
async def create_consent(
    data: schemas.ConsentCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.OpenBankingService.create_consent(db, current_account.owner.id, data)


@router.get("/consents", response_model=list[schemas.ConsentResponse])
async def list_consents(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.OpenBankingService.list_consents(db, current_account.owner.id)


@router.post("/external-accounts", response_model=schemas.ExternalAccountResponse)
async def create_external_account(
    data: schemas.ExternalAccountCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.OpenBankingService.create_external_account(db, current_account.owner.id, data)


@router.get("/external-accounts", response_model=list[schemas.ExternalAccountResponse])
async def list_external_accounts(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.OpenBankingService.list_external_accounts(db, current_account.owner.id)


@router.post("/payments", response_model=schemas.OpenBankingPaymentResponse)
async def create_payment(
    data: schemas.OpenBankingPaymentCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.OpenBankingService.create_payment(db, current_account.owner.id, data)


@router.get("/payments", response_model=list[schemas.OpenBankingPaymentResponse])
async def list_payments(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.OpenBankingService.list_payments(db, current_account.owner.id)
