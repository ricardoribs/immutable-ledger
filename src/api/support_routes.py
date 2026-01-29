from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.api import deps
from src.domain.support import schemas, services

router = APIRouter(prefix="/support", tags=["Support"])


@router.post("/tickets", response_model=schemas.TicketResponse)
async def create_ticket(
    data: schemas.TicketCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.SupportService.create_ticket(db, current_account.owner.id, data)


@router.get("/tickets", response_model=list[schemas.TicketResponse])
async def list_tickets(
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    return await services.SupportService.list_tickets(db, current_account.owner.id)


@router.post("/tickets/messages", response_model=schemas.TicketMessageResponse)
async def add_message(
    data: schemas.TicketMessageCreate,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    msg = await services.SupportService.add_message(db, current_account.owner.id, data)
    if not msg:
        raise HTTPException(status_code=404, detail="Ticket nao encontrado")
    return msg


@router.get("/faq", response_model=list[schemas.FaqResponse])
async def list_faq(db: AsyncSession = Depends(get_db)):
    return await services.SupportService.list_faq(db)


@router.post("/chatbot", response_model=schemas.ChatbotResponse)
async def chatbot(
    data: schemas.ChatbotRequest,
    current_account=Depends(deps.get_current_account),
    db: AsyncSession = Depends(get_db),
):
    answer, from_faq, ticket_id = await services.SupportService.chatbot_reply(
        db, current_account.owner.id, data.message
    )
    return {"answer": answer, "from_faq": from_faq, "ticket_id": ticket_id}
