from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate
from app.models.user import User

class TicketService:
    async def create_ticket(self, db:AsyncSession, ticket_data: TicketCreate, current_user: User)->Ticket:
        new_ticket = Ticket(
            title = ticket_data.title,
            description = ticket_data.description,
            customer_id = current_user.id,
            priority = 'MEDIUM',
            status="OPEN",
        )
        
        db.add(new_ticket)
        
        await db.flush()
        
        return new_ticket
    
    async def get_ticket(self, db:AsyncSession, current_user:User):
        
        result = await db.execute(
            select(Ticket).where(Ticket.customer_id == current_user.id)
        )
        
        return result.scalars().all()
    
    async def get_ticket_by_id(self, db:AsyncSession, ticket_id:UUID, current_user: User):
        result = await db.execute(select(Ticket).where(
            Ticket.id == ticket_id,
            Ticket.customer_id== current_user.id
            )
        )
        
        return result.scalar_one_or_none()
    
    async def update_ticket(self, db:AsyncSession, ticket_id, ticket_data: TicketUpdate, current_user):
        ticket = await self.get_ticket_by_id(db, ticket_id, current_user)
        
        if ticket is None:
            return None
        
        update_data = ticket_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is None:
                raise ValueError(f"{field} cannoy be null")
            
            setattr(ticket, field, value)
            
        await db.flush()
        
        return ticket