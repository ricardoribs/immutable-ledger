from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.api import deps
from src.domain.cards import schemas, services

router = APIRouter(prefix="/cards", tags=["Cards"])


@router.post("/", response_model=schemas.CardResponse)
async def create_card(
    data: schemas.CardCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.CardService.create_card(db, current_account.owner.id, data)


@router.get("/", response_model=list[schemas.CardResponse])
async def list_cards(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.CardService.list_cards(db, current_account.owner.id)


@router.post("/{card_id}/block", response_model=schemas.CardResponse)
async def block_card(
    card_id: int,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    card = await services.CardService.set_card_status(db, card_id, current_account.owner.id, "BLOCKED")
    if not card:
        raise HTTPException(status_code=404, detail="Cartao nao encontrado")
    return card


@router.post("/{card_id}/unblock", response_model=schemas.CardResponse)
async def unblock_card(
    card_id: int,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    card = await services.CardService.set_card_status(db, card_id, current_account.owner.id, "ACTIVE")
    if not card:
        raise HTTPException(status_code=404, detail="Cartao nao encontrado")
    return card


@router.post("/{card_id}/controls", response_model=schemas.CardResponse)
async def update_controls(
    card_id: int,
    data: schemas.CardControlUpdate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    card = await services.CardService.update_controls(db, card_id, current_account.owner.id, data)
    if not card:
        raise HTTPException(status_code=404, detail="Cartao nao encontrado")
    return card


@router.get("/{card_id}/transactions", response_model=list[schemas.CardTransactionResponse])
async def list_transactions(
    card_id: int,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.CardService.list_transactions(db, card_id, current_account.owner.id)


@router.post("/transactions", response_model=schemas.CardTransactionResponse)
async def create_transaction(
    data: schemas.CardTransactionCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    try:
        tx = await services.CardService.create_transaction(db, current_account.owner.id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not tx:
        raise HTTPException(status_code=404, detail="Cartao nao encontrado")
    return tx


@router.get("/{card_id}/invoices", response_model=list[schemas.CardInvoiceResponse])
async def list_invoices(
    card_id: int,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.CardService.list_invoices(db, card_id, current_account.owner.id)
