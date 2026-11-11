from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database.session import get_db
from app.models.user import User
from app.core.permissions import require_roles
from app.services.assignment_service import AssignmentService
from app.schemas.ticket import TicketResponse, TicketAssign, TicketAssignmentResponse, TicketAgentUpdate
from app.services.ticket_service import TicketService
from app.schemas.ticket import TicketListResponse
from sqlalchemy import select

from app.models.ticket import Ticket
from app.core.websocket_manager import websocket_manager
router = APIRouter()
assignment_service = AssignmentService()
ticket_service = TicketService()

@router.get(
    "/tickets",
    response_model=TicketListResponse
)
async def get_assigned_tickets(
    category_id: UUID | None = None,

    status: str | None = Query(
        default=None,
        pattern="^(OPEN|IN_PROGRESS|WAITING_ON_CUSTOMER|RESOLVED|CLOSED)$"
    ),

    priority: str | None = Query(
        default=None,
        pattern="^(LOW|MEDIUM|HIGH|URGENT)$"
    ),

    search: str | None = None,

    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),

    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$"
    ),

    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("AGENT"))
):
    result = await ticket_service.list_tickets(
        db=db,
        current_user=current_user,
        category_id=category_id,
        status=status,
        priority=priority,
        search=search,
        page=page,
        limit=limit,
        sort_order=sort_order
    )

    result["items"] = [
        ticket_service.to_ticket_response(ticket)
        for ticket in result["items"]
    ]

    return result


@router.post(
    '/tickets/{ticket_id}/assign',
    response_model=TicketAssignmentResponse,
    status_code=status.HTTP_201_CREATED
)
async def assign_ticket(
    ticket_id: UUID,
    assignment_data: TicketAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN"))
):
    try:
        # 1. Lock the ticket and remember its previously assigned agent.
        result = await db.execute(
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .with_for_update()
        )

        ticket = result.scalar_one_or_none()

        previous_agent_id = (
            ticket.assigned_agent_id if ticket is not None else None
        )

        # 2. Perform the assignment using the existing service.
        assignment = await assignment_service.assign_ticket(
            db,
            ticket_id,
            assignment_data,
            current_user
        )

        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )

        # 3. Commit the database transaction.
        await db.commit()

        # 4. Disconnect the previous agent only after a successful commit.
        if (
            previous_agent_id is not None
            and previous_agent_id != assignment.agent_id
        ):
            await websocket_manager.disconnect_user(
                ticket_id=ticket_id,
                user_id=previous_agent_id,
            )

        await db.refresh(assignment)

        return assignment

    except ValueError as error:
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
    
