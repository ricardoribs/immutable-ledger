from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.api import deps
from src.domain.loans import schemas, services

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post("/simulate", response_model=schemas.LoanSimulateResponse)
async def simulate_loan(data: schemas.LoanSimulateRequest):
    return services.LoanService.simulate(data)


@router.post("/", response_model=schemas.LoanResponse)
async def create_loan(
    data: schemas.LoanCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.LoanService.create_loan(db, current_account.owner.id, data)


@router.get("/", response_model=list[schemas.LoanResponse])
async def list_loans(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.LoanService.list_loans(db, current_account.owner.id)


@router.get("/{loan_id}/installments", response_model=list[schemas.LoanInstallmentResponse])
async def list_installments(
    loan_id: int,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.LoanService.list_installments(db, loan_id, current_account.owner.id)
