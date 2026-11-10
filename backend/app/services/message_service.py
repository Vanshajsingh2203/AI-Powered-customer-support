
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket
from app.models.message import TicketMessage
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse


class MessageService:

    async def get_accessible_ticket(
        self,
        db: AsyncSession,
        ticket_id: UUID,
        current_user: User,
    ):
        query = select(Ticket).where(Ticket.id == ticket_id)

        # Customer can access only their own tickets.
        if current_user.role == "CUSTOMER":
            query = query.where(
                Ticket.customer_id == current_user.id
            )

        # Agent can access only tickets currently assigned to them.
        elif current_user.role == "AGENT":
            query = query.where(
                Ticket.assigned_agent_id == current_user.id
            )

        # Admin can access all tickets.
        elif current_user.role != "ADMIN":
            return None

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_message(
        self,
        db: AsyncSession,
        ticket_id: UUID,
        message_data: MessageCreate,
        current_user: User,
    ) -> TicketMessage | None:

        # Customers must not be able to create internal notes.
        if (
            current_user.role == "CUSTOMER"
            and message_data.is_internal
        ):
            raise ValueError(
                "Customers cannot create internal notes"
            )

        ticket = await self.get_accessible_ticket(
            db, ticket_id, current_user
        )

        if ticket is None:
            return None

        new_message = TicketMessage(
            ticket_id=ticket_id,
            sender_id=current_user.id,
            content=message_data.content,
            is_internal=message_data.is_internal,
        )

        db.add(new_message)
        await db.flush()

        return new_message

    async def get_ticket_message(
        self,
        db: AsyncSession,
        ticket_id: UUID,
        current_user: User,
        limit: int = 20,
        offset: int = 0,
    ) -> list[MessageResponse] | None:

        ticket = await self.get_accessible_ticket(
            db, ticket_id, current_user
        )

        if ticket is None:
            return None

        query = (
            select(TicketMessage)
            .options(selectinload(TicketMessage.sender))
            .where(TicketMessage.ticket_id == ticket_id)
        )

        # Customers must never see internal agent messages.
        if current_user.role == "CUSTOMER":
            query = query.where(
                TicketMessage.is_internal.is_(False)
            )

        result = await db.execute(
            query
            .order_by(TicketMessage.created_at.asc())
            .limit(limit)
            .offset(offset)
        )

        messages = result.scalars().all()

        # Convert database models into API response schemas.
        return [
            MessageResponse(
                id=message.id,
                ticket_id=message.ticket_id,
                sender_id=message.sender_id,
                sender_name=message.sender.full_name,
                sender_role=message.sender.role,
                content=message.content,
                is_internal=message.is_internal,
                created_at=message.created_at,
            )
            for message in messages
        ]


message_service = MessageService()
