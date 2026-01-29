from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.api import deps
from src.domain.billing import schemas, services

router = APIRouter(prefix="/billing", tags=["Billing"])


@router.post("/boletos", response_model=schemas.BoletoResponse)
async def create_boleto(
    data: schemas.BoletoCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.BillingService.create_boleto(db, current_account.owner.id, data)


@router.get("/boletos", response_model=list[schemas.BoletoResponse])
async def list_boletos(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.BillingService.list_boletos(db, current_account.owner.id)


@router.post("/boletos/pay", response_model=schemas.BoletoResponse)
async def pay_boleto(
    data: schemas.BoletoPay,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await services.BillingService.pay_boleto(db, current_account.id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/links", response_model=schemas.PaymentLinkResponse)
async def create_link(
    data: schemas.PaymentLinkCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.BillingService.create_payment_link(db, current_account.owner.id, data)


@router.get("/links", response_model=list[schemas.PaymentLinkResponse])
async def list_links(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.BillingService.list_payment_links(db, current_account.owner.id)


@router.post("/pos", response_model=schemas.PosSaleResponse)
async def create_pos_sale(
    data: schemas.PosSaleCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.BillingService.create_pos_sale(db, current_account.owner.id, data)


@router.get("/pos", response_model=list[schemas.PosSaleResponse])
async def list_pos_sales(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.BillingService.list_pos_sales(db, current_account.owner.id)


@router.post("/split", response_model=schemas.SplitRuleResponse)
async def create_split(
    data: schemas.SplitRuleCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.BillingService.create_split_rule(db, current_account.owner.id, data)


@router.get("/split", response_model=list[schemas.SplitRuleResponse])
async def list_splits(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.BillingService.list_split_rules(db, current_account.owner.id)
