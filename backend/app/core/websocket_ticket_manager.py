
import asyncio
import secrets
import time
from uuid import UUID


class WebSocketTicketManager:
    """
    Manages temporary, single-use tickets for WebSocket authentication.

    Tickets are stored in memory and are valid for a limited duration.
    """

    def __init__(self, expiry_seconds: int = 30):
        self.expiry_seconds = expiry_seconds

        # ticket -> (user_id, expiration_timestamp)
        self._tickets: dict[str, tuple[UUID, float]] = {}

        # Protect ticket creation and consumption from concurrent access.
        self._lock = asyncio.Lock()

    async def create_ticket(self, user_id: UUID) -> str:
        

        ticket = secrets.token_urlsafe(32)
        expires_at = time.monotonic() + self.expiry_seconds

        async with self._lock:
            # Remove expired tickets to prevent unlimited memory growth.
            now = time.monotonic()

            expired_tickets = [
                stored_ticket
                for stored_ticket, (_, expiry) in self._tickets.items()
                if expiry <= now
            ]

            for stored_ticket in expired_tickets:
                self._tickets.pop(stored_ticket, None)

            self._tickets[ticket] = (user_id, expires_at)

        return ticket

    async def consume_ticket(self, ticket: str) -> UUID | None:
        """
        Validate and consume a ticket.

        A ticket can only be used once.
        Returns the associated user ID if valid.
        """

        async with self._lock:
            ticket_data = self._tickets.pop(ticket, None)

            if ticket_data is None:
                return None

            user_id, expires_at = ticket_data

            if time.monotonic() >= expires_at:
                return None

            return user_id


# Shared manager instance for the application process.
websocket_ticket_manager = WebSocketTicketManager()
