from uuid import UUID
from sqlalchemy import select

from app.models.ticket import Ticket
from app.schemas.message import MessageCreate
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import TicketMessage
from app.models.user import User

class MessageService:
    
    async def create_message(self, db:AsyncSession, ticket_id:UUID, message_data:MessageCreate, current_user)-> TicketMessage:
        
        result = await db.execute(
            select(Ticket).where(
                Ticket.id == ticket_id,
                Ticket.customer_id == current_user.id,
            )
        )
        
        ticket = result.scalar_one_or_none()
        if ticket is None:
            return None
        
        new_message = TicketMessage(
            ticket_id = ticket_id,
            sender_id = current_user.id,
            content = message_data.content,
            is_internal= False,
        )
        
        db.add(new_message)
        await db.flush()
        
        return new_message
    
    async def get_ticket_message(self, db: AsyncSession, ticket_id: UUID , current_user: User, limit: int =20, offset: int = 0):
        
        result = await db.execute(select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.customer_id == current_user.id,
        )
    )

        ticket = result.scalar_one_or_none()
        
        if ticket is None:
            return None
        
        result = await db.execute(
            select(TicketMessage)
            .where(TicketMessage.ticket_id==ticket_id)
            .order_by(TicketMessage.created_at.asc(),
            )
            .limit(limit)
            .offset(offset)
        )
        
        return result.scalars().all()