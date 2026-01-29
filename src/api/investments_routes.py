from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.api import deps
from src.domain.investments import schemas, services

router = APIRouter(prefix="/investments", tags=["Investments"])


@router.post("/products", response_model=schemas.InvestmentProductResponse)
async def create_product(
    data: schemas.InvestmentProductCreate,
    db: AsyncSession = Depends(get_db),
):
    return await services.InvestmentService.create_product(db, data)


@router.get("/products", response_model=list[schemas.InvestmentProductResponse])
async def list_products(db: AsyncSession = Depends(get_db)):
    return await services.InvestmentService.list_products(db)


@router.post("/orders", response_model=schemas.InvestmentOrderResponse)
async def create_order(
    data: schemas.InvestmentOrderCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.InvestmentService.create_order(db, current_account.owner.id, data)


@router.get("/holdings", response_model=list[schemas.InvestmentHoldingResponse])
async def list_holdings(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.InvestmentService.list_holdings(db, current_account.owner.id)


@router.post("/auto", response_model=schemas.AutoInvestResponse)
async def set_auto_invest(
    data: schemas.AutoInvestCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.InvestmentService.set_auto_invest(db, current_account.owner.id, data)


@router.get("/auto", response_model=schemas.AutoInvestResponse)
async def get_auto_invest(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    cfg = await services.InvestmentService.get_auto_invest(db, current_account.owner.id)
    if not cfg:
        return None
    return cfg
