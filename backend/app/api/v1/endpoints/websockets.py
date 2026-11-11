
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy import select
from app.core.websocket_ticket_manager import websocket_ticket_manager
from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.services.message_service import MessageService
from app.dependencies import get_current_user
from app.core.websocket_manager import websocket_manager

router = APIRouter()
message_service = MessageService()


@router.post("/ticket")
async def create_websocket_ticket(
    current_user: User = Depends(get_current_user),
):
    ticket = await websocket_ticket_manager.create_ticket(
        user_id=current_user.id
    )

    return {
        "ticket": ticket,
        "expires_in": 30,
    }


@router.websocket("/{ticket_id}")
async def ticket_websocket(
    websocket: WebSocket,
    ticket_id: UUID,
):
    # 1. Validate the browser origin.
    allowed_origins = {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    }

    origin = websocket.headers.get("origin")

    if origin not in allowed_origins:
        await websocket.close(code=1008)
        return

    # 2. Retrieve the single-use authentication ticket.
    ticket = websocket.query_params.get("ticket")

    if not ticket:
        await websocket.close(code=1008)
        return

    # 3. Consume the ticket. It cannot be reused.
    user_id = await websocket_ticket_manager.consume_ticket(ticket)

    if user_id is None:
        await websocket.close(code=1008)
        return

    # 4. Verify the user and their access to this ticket.
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )

        current_user = result.scalar_one_or_none()

        if current_user is None or not current_user.is_active:
            await websocket.close(code=1008)
            return

        accessible_ticket = await message_service.get_accessible_ticket(
            db,
            ticket_id,
            current_user,
        )

        if accessible_ticket is None:
            await websocket.close(code=1008)
            return

    # 5. Authentication and authorization succeeded.
    # 5. Authentication and authorization succeeded.
    await websocket.accept()

    # Register this connection with the connection manager.
    await websocket_manager.connect(
        ticket_id=ticket_id,
        websocket=websocket,
        user_id=current_user.id,
        user_role=current_user.role,
    )

    try:
        await websocket.send_json({
            "message": "WebSocket connection established",
            "ticket_id": str(ticket_id),
        })

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass

    finally:
        # Always remove the connection when it ends.
        websocket_manager.disconnect(
            ticket_id=ticket_id,
            websocket=websocket,
        )