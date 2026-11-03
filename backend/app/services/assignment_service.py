from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy import select

from app.models.ticket import Ticket
from app.models.user import User

class AssignmentService:
    
    async def get_assigned_tickets(self, db:AsyncSession, current_user: User):
        result = await db.execute(
            select(Ticket).where(
                Ticket.assigned_agent_id== current_user.id
            )
        )
        
        return result.scalars().all()