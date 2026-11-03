from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlalchemy import select
from datetime import datetime, timezone
from app.models.ticket import Ticket
from app.models.user import User
from app.models.ticket_assignment import TicketAssignment
from app.schemas.ticket import TicketAssign

class AssignmentService:
    
    async def get_assigned_tickets(self, db:AsyncSession, current_user: User):
        result = await db.execute(
            select(Ticket).where(
                Ticket.assigned_agent_id== current_user.id
            )
        )
        
        return result.scalars().all()
    
    async def assign_ticket(self, db:AsyncSession, ticket_id: UUID, assignment_data: TicketAssign, current_user: User):
        
        # find and look the ticket
        result = await db.execute(
            select(Ticket)
            .where(Ticket.id==ticket_id)
            .with_for_update()
        )
        
        ticket = result.scalar_one_or_none()
        
        if ticket is None:
            return None
        
        result = await db.execute(
            select(User).where(User.id == assignment_data.agent_id)
        )
        
        agent = result.scalar_one_or_none()
        
        if agent is None or agent.role != "AGENT" or not agent.is_active:
            raise ValueError("Invalid or inactive agent")
        
        # find the existing active assignment
        
        result = await db.execute(
            select(TicketAssignment).where(
                TicketAssignment.ticket_id == ticket_id,
                TicketAssignment.unassigned_at.is_(None)
            )
        )
        
        active_assignment = result.scalar_one_or_none()
        
        # 4. Avoid creating a duplicate assignment
         
        if active_assignment is not None:
            if active_assignment.agent_id == agent.id:
                return active_assignment
            
            active_assignment.unassigned_at = datetime.now(timezone.utc)
        
        # 5. Create a new assignment record
        
        new_assignment = TicketAssignment(
            ticket_id= ticket_id,
            agent_id = agent.id,
            assigned_by = current_user.id
        )                
        
        db.add(new_assignment)
        
        # 6. Update the current assignment on the ticket
        ticket.assigned_agent_id = agent.id
        
        await db.flush()
        
        return new_assignment