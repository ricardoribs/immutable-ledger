from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.api import deps
from src.domain.regulatory import schemas, services

router = APIRouter(prefix="/regulatory", tags=["Regulatory"])


@router.post("/kyc", response_model=schemas.KycResponse)
async def submit_kyc(
    data: schemas.KycCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.RegulatoryService.create_kyc(db, current_account.owner.id, data)


@router.get("/aml/alerts", response_model=list[schemas.AmlAlertResponse])
async def list_aml_alerts(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.RegulatoryService.list_aml_alerts(db, current_account.owner.id)


@router.get("/scr", response_model=schemas.ReportResponse)
async def generate_scr(
    period: str,
    db: AsyncSession = Depends(get_db),
):
    return await services.RegulatoryService.generate_scr_report(db, period)


@router.get("/coaf", response_model=schemas.ReportResponse)
async def generate_coaf(
    period: str,
    db: AsyncSession = Depends(get_db),
):
    return await services.RegulatoryService.generate_coaf_report(db, period)
