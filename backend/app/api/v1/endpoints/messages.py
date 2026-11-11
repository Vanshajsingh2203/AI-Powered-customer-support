
from uuid import UUID
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.message import MessageCreate, MessageResponse
from app.models.user import User
from app.dependencies import get_current_user
from app.database.session import get_db
from app.services.message_service import MessageService
from app.core.websocket_manager import websocket_manager
router = APIRouter()
message_service = MessageService()

logger = logging.getLogger(__name__)
@router.post(
    '/{ticket_id}/messages',
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_ticket_message(
    ticket_id: UUID,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        message = await message_service.create_message(
            db, ticket_id, message_data, current_user
        )

        if message is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )

        await db.commit()
        await db.refresh(message)

        # Explicitly construct the response with sender information.
        response =  MessageResponse(
            id=message.id,
            ticket_id=message.ticket_id,
            sender_id=message.sender_id,
            sender_name=current_user.full_name,
            sender_role=current_user.role,
            content=message.content,
            is_internal=message.is_internal,
            created_at=message.created_at,
        )
        # Broadcast the committed message to connected users.
        try:
            await websocket_manager.broadcast(
            ticket_id=ticket_id,
            message=response.model_dump(mode="json"),
            exclude_roles={"CUSTOMER"} if message.is_internal else None,
        )
        except Exception:
            logger.exception(
            "Failed to broadcast message %s for ticket %s",
            message.id,
            ticket_id,
    )
        
        return response

    except ValueError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except Exception:
        await db.rollback()
        raise


@router.get(
    '/{ticket_id}/messages',
    response_model=list[MessageResponse]
)
async def get_ticket_messages(
    ticket_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    messages = await message_service.get_ticket_message(
        db, ticket_id, current_user, limit, offset
    )

    if messages is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    return messages
