
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket
from app.models.message import TicketMessage
from app.models.user import User
from app.schemas.message import MessageCreate


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

        ticket = await self.get_accessible_ticket(
            db, ticket_id, current_user
        )

        if ticket is None:
            return None

        new_message = TicketMessage(
            ticket_id=ticket_id,
            sender_id=current_user.id,
            content=message_data.content,
            is_internal=False,
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
    ):

        ticket = await self.get_accessible_ticket(
            db, ticket_id, current_user
        )

        if ticket is None:
            return None

        query = select(TicketMessage).where(
            TicketMessage.ticket_id == ticket_id
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

        return result.scalars().all()


message_service = MessageService()
