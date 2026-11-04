from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime , timezone
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate, TicketAgentUpdate
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
    
    async def update_ticket_by_agent(self, db:AsyncSession, ticket_id: UUID, update_data:TicketAgentUpdate, current_user: User):
        result = await db.execute(
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .with_for_update()
        )
        
        ticket = result.scalar_one_or_none()
        
        if ticket is None:
            return None
        
        # Only the assigned agent or an admin can update the ticket.
        
        if(
            current_user.role == "AGENT"
            and ticket.assigned_agent_id != current_user.id
        ):
            return None
        
        if current_user.role not in ("AGENT", "ADMIN"):
            raise ValueError("You do not have permisson to update this ticket")
        
        changes = update_data.model_dump(exclude_unset=True)
        
        if not changes:
            raise ValueError("At least one field must be provided")
        
        for field, value in changes.items():
            if value is None:
                raise ValueError(f"{field} cannot be null")
            
        allowed_transitions = {
            "OPEN": ["IN_PROGRESS"],
            "IN_PROGRESS": ["WAITING_ON_CUSTOMER", "RESOLVED"],
            "WAITING_ON_CUSTOMER": ["IN_PROGRESS"],
            "RESOLVED": ["IN_PROGRESS", "CLOSED"],
            "CLOSED": [],
        }
        
        if "status" in changes:
            new_status = changes["status"]

            if new_status != ticket.status:
                 if new_status not in allowed_transitions[ticket.status]:
                     raise ValueError(
                f"Cannot change status from {ticket.status} to {new_status}"
            )

            ticket.status = new_status
            
        if "priority" in changes:
            ticket.priority = changes["priority"]       
            
        if ticket.status == "CLOSED":
            ticket.closed_at = datetime.now(timezone.utc)
            
        elif "status" in changes and ticket.status != "CLOSED":
            ticket.closed_at = None
            
        await db.flush()
        
        return ticket

            
            