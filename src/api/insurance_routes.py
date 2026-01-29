from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.api import deps
from src.domain.insurance import schemas, services

router = APIRouter(prefix="/insurance", tags=["Insurance"])


@router.post("/policies", response_model=schemas.InsurancePolicyResponse)
async def create_policy(
    data: schemas.InsurancePolicyCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.InsuranceService.create_policy(db, current_account.owner.id, data)


@router.get("/policies", response_model=list[schemas.InsurancePolicyResponse])
async def list_policies(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.InsuranceService.list_policies(db, current_account.owner.id)


@router.post("/claims", response_model=schemas.InsuranceClaimResponse)
async def create_claim(
    data: schemas.InsuranceClaimCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    claim = await services.InsuranceService.create_claim(db, current_account.owner.id, data)
    if not claim:
        raise HTTPException(status_code=404, detail="Apolice nao encontrada")
    return claim


@router.get("/claims", response_model=list[schemas.InsuranceClaimResponse])
async def list_claims(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.InsuranceService.list_claims(db, current_account.owner.id)
