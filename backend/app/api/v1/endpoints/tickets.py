from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.user import User
from app.database.session import get_db
from app.dependencies import get_current_user
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketResponse
from app.services.ticket_service import TicketService

router = APIRouter()
ticket_service = TicketService()

@router.post('/', response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(ticket_data: TicketCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        ticket = await ticket_service.create_ticket(db, ticket_data, current_user)
        
        await db.commit()
        await db.refresh(ticket)
        
        return ticket
    
    except Exception:
        await db.rollback()
        raise
    
@router.get('/',response_model=list[TicketResponse])
async def get_customer_tickets(
    db:AsyncSession= Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    tickets = await ticket_service.get_ticket(db, current_user)
    
    return tickets

@router.get('/{ticket_id}', response_model=TicketResponse)
async def get_ticket_by_id(
    ticket_id:UUID,
    db:AsyncSession= Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = await ticket_service.get_ticket_by_id(db, ticket_id, current_user)
    
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
        
    return ticket

@router.patch('/{ticket_id}', response_model=TicketResponse)
async def update_ticket(
    ticket_id: UUID,
    ticket_data: TicketUpdate,
    db:AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    try:
        ticket = await ticket_service.update_ticket(db, ticket_id, ticket_data, current_user)
        
        if ticket is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )
            
        await db.commit()
        await db.refresh(ticket)
        
        return ticket
    
    except ValueError as error:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        )

    except Exception:
        await db.rollback()
        raise