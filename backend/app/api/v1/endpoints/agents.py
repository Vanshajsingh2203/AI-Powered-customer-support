from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database.session import get_db
from app.models.user import User
from app.core.permissions import require_roles
from app.services.assignment_service import AssignmentService
from app.schemas.ticket import TicketResponse, TicketAssign, TicketAssignmentResponse, TicketAgentUpdate
from app.services.ticket_service import TicketService


router = APIRouter()
assignment_service = AssignmentService()
ticket_service = TicketService()

@router.get('/tickets', response_model=list[TicketResponse])
async def get_assigned_tickets(
    db:AsyncSession= Depends(get_db),
    current_user: User = Depends(require_roles("AGENT"))
):
    tickets = await assignment_service.get_assigned_tickets(db, current_user)
    
    return tickets

@router.post('/tickets/{ticket_id}/assign', response_model=TicketAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_ticket(
    ticket_id: UUID,
    assignment_data: TicketAssign,
    db:AsyncSession = Depends(get_db),
    current_user : User = Depends(require_roles("ADMIN"))
):
    try:
        assignment = await assignment_service.assign_ticket(db, ticket_id , assignment_data, current_user)
        
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )
            
        await db.commit()
        await db.refresh(assignment)
        
        return assignment
    
    except  ValueError as error:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    except Exception:
        await db.rollback()
        raise

@router.patch('/tickets/{ticket_id}', response_model=TicketResponse)
async def update_assigned_ticket(
    ticket_id: UUID,
    update_data:TicketAgentUpdate,
    db:AsyncSession = Depends(get_db),
    current_user : User = Depends(require_roles("AGENT", "ADMIN"))
):
    try:
        ticket = await ticket_service.update_ticket_by_agent(db, ticket_id, update_data, current_user)
        
        if ticket is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )
            
        await db.commit()
        await db.refresh(ticket)
        
        return ticket
    
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception:
        await db.rollback()
        raise