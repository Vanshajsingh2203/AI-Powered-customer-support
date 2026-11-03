from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.user import User
from app.core.permissions import require_roles
from app.services.assignment_service import AssignmentService
from app.schemas.ticket import TicketResponse

router = APIRouter()
assignment_service = AssignmentService()

@router.get('/tickets', response_model=list[TicketResponse])
async def get_assigned_tickets(
    db:AsyncSession= Depends(get_db),
    current_user: User = Depends(require_roles("AGENT"))
):
    tickets = await assignment_service.get_assigned_tickets(db, current_user)
    
    return tickets