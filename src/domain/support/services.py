from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.domain.support import models, schemas


class SupportService:
    @staticmethod
    async def create_ticket(db: AsyncSession, user_id: int, data: schemas.TicketCreate):
        ticket = models.Ticket(
            user_id=user_id,
            subject=data.subject,
        )
        db.add(ticket)
        await db.flush()
        msg = models.TicketMessage(
            ticket_id=ticket.id,
            message=data.message,
        )
        db.add(msg)
        await db.commit()
        return ticket

    @staticmethod
    async def list_tickets(db: AsyncSession, user_id: int):
        res = await db.execute(select(models.Ticket).where(models.Ticket.user_id == user_id))
        return res.scalars().all()

    @staticmethod
    async def add_message(db: AsyncSession, user_id: int, data: schemas.TicketMessageCreate):
        ticket = await db.get(models.Ticket, data.ticket_id)
        if not ticket or ticket.user_id != user_id:
            return None
        msg = models.TicketMessage(
            ticket_id=data.ticket_id,
            message=data.message,
        )
        db.add(msg)
        await db.commit()
        return msg

    @staticmethod
    async def list_faq(db: AsyncSession):
        res = await db.execute(select(models.Faq))
        return res.scalars().all()

    @staticmethod
    async def chatbot_reply(db: AsyncSession, user_id: int, message: str) -> tuple[str, bool, int | None]:
        faq_items = await SupportService.list_faq(db)
        if faq_items:
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.metrics.pairwise import cosine_similarity
                corpus = [f.question for f in faq_items] + [message]
                vec = TfidfVectorizer().fit_transform(corpus)
                sims = cosine_similarity(vec[-1], vec[:-1]).flatten()
                best = sims.argmax()
                if sims[best] > 0.3:
                    return faq_items[best].answer, True, None
            except Exception:
                pass

        ticket = models.Ticket(user_id=user_id, subject="Chatbot Handoff", status="OPEN")
        db.add(ticket)
        await db.flush()
        db.add(models.TicketMessage(ticket_id=ticket.id, message=message))
        await db.commit()
        return "Encaminhei para um atendente humano.", False, ticket.id
