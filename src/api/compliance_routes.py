from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.api import deps
from src.domain.compliance import schemas, services
from src.domain.ledger import models as ledger_models

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.post("/consents", response_model=schemas.ConsentResponse)
async def record_consent(
    data: schemas.ConsentCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.ComplianceService.record_consent(db, current_account.owner.id, data)


@router.get("/consents", response_model=list[schemas.ConsentResponse])
async def list_consents(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.ComplianceService.list_consents(db, current_account.owner.id)


@router.post("/forget", response_model=schemas.ForgetRequestResponse)
async def request_forget(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.ComplianceService.request_forget(db, current_account.owner.id)


@router.post("/forget/{request_id}/complete", response_model=schemas.ForgetRequestResponse)
async def complete_forget(
    request_id: int,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    req = await services.ComplianceService.complete_forget_request(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Requisicao nao encontrada")
    return req


@router.get("/report", response_model=schemas.DataReportResponse)
async def data_report(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(ledger_models.User, current_account.owner.id)
    consents = await services.ComplianceService.list_consents(db, current_account.owner.id)
    return {
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "cpf_last4": user.cpf_last4,
        "consents": consents,
    }
