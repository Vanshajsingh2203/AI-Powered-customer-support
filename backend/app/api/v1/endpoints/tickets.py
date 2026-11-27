
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.ticket import Ticket
from app.database.session import get_db
from app.dependencies import get_current_user
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketResponse
from app.schemas.ticket import TicketListResponse
from app.schemas.ai.summary import TicketSummary
from app.services.ticket_service import TicketService
from app.services.auto_assignment import auto_assign_ticket
from app.services.message_service import message_service

logger = logging.getLogger(__name__)

router = APIRouter()
ticket_service = TicketService()


@router.post(
    '/',
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_ticket(
    ticket_data: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        ticket = await ticket_service.create_ticket(
            db, ticket_data, current_user
        )

        await auto_assign_ticket(db=db, ticket_id=ticket.id)
        await db.commit()

        # Retrieve ticket with its category eagerly loaded.
        ticket = await ticket_service.get_ticket_with_category(
            db=db,
            ticket_id=ticket.id
        )

        return ticket_service.to_ticket_response(ticket)

    except ValueError as error:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error)
        )

    except Exception:
        await db.rollback()
        raise


@router.get(
    "/",
    response_model=TicketListResponse
)
async def get_customer_tickets(
    category_id: UUID | None = None,

    status: str | None = Query(
        default=None,
        pattern="^(OPEN|IN_PROGRESS|WAITING_ON_CUSTOMER|RESOLVED|CLOSED)$"
    ),

    search: str | None = None,

    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),

    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$"
    ),

    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await ticket_service.list_tickets(
        db=db,
        current_user=current_user,
        category_id=category_id,
        status=status,
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


@router.get('/{ticket_id}', response_model=TicketResponse)
async def get_ticket_by_id(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = await ticket_service.get_ticket_by_id(
        db,
        ticket_id,
        current_user
    )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    return ticket_service.to_ticket_response(ticket)


@router.patch('/{ticket_id}', response_model=TicketResponse)
async def update_ticket(
    ticket_id: UUID,
    ticket_data: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        ticket = await ticket_service.update_ticket(
            db,
            ticket_id,
            ticket_data,
            current_user
        )

        if ticket is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )

        await db.commit()
        await db.refresh(ticket)

        return ticket_service.to_ticket_response(ticket)

    except ValueError as error:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        )

    except Exception:
        await db.rollback()
        raise


@router.post(
    "/{ticket_id}/summary",
    response_model=TicketSummary,
)
async def get_ticket_summary(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.ai.services.ticket_ai_service import summarize_ticket

    # Fetch the ticket directly so we can distinguish a missing ticket
    # from an existing ticket that the current agent cannot access.
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )

    ticket = result.scalar_one_or_none()

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # Only agents assigned to this ticket and administrators can
    # generate its AI summary.
    if current_user.role == "ADMIN":
        pass

    elif current_user.role == "AGENT":
        if ticket.assigned_agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view summary for this ticket",
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view summary for this ticket",
        )

    # Retrieve public messages and internal notes.
    # The message service already applies role-based visibility.
    messages = await message_service.get_ticket_message(
        db,
        ticket_id,
        current_user,
        limit=200,
        offset=0
    )

    conversation_parts = []

    for msg in messages:
        sender_name = msg.sender.full_name if msg.sender else "Unknown"
        sender_role = msg.sender.role if msg.sender else "Unknown"

        content_line = (
            f"{sender_name} ({sender_role}): {msg.content}"
        )

        conversation_parts.append(content_line)

    conversation_text = "\n".join(conversation_parts)

    try:
        summary = await summarize_ticket(
            title=ticket.title,
            description=ticket.description,
            conversation_text=conversation_text,
        )

        return summary

    except Exception:
        logger.exception(
            "AI ticket summarization failed for ticket_id=%s",
            ticket_id,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate ticket summary right now.",
        )
