
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect


class WebSocketConnectionManager:

    def __init__(self):
        # ticket_id -> {websocket: (user_id, user_role)}
        self.active_connections: dict[
            UUID,
            dict[WebSocket, tuple[UUID, str]]
        ] = {}

    async def connect(
        self,
        ticket_id: UUID,
        websocket: WebSocket,
        user_id: UUID,
        user_role: str,
    ):
        """Register an already-accepted WebSocket connection."""

        self.active_connections.setdefault(ticket_id, {})[websocket] = (
            user_id,
            user_role,
        )

    def disconnect(self, ticket_id: UUID, websocket: WebSocket):
        """Remove a disconnected WebSocket."""

        connections = self.active_connections.get(ticket_id)

        if connections is None:
            return

        connections.pop(websocket, None)

        if not connections:
            self.active_connections.pop(ticket_id, None)

    async def disconnect_user(
        self,
        ticket_id: UUID,
        user_id: UUID,
    ):
        """Close all connections belonging to a particular user on a ticket."""

        connections = self.active_connections.get(ticket_id, {})

        user_connections = [
            websocket
            for websocket, (connected_user_id, _) in connections.items()
            if connected_user_id == user_id
        ]

        for websocket in user_connections:
            try:
                await websocket.close(
                    code=1008,
                    reason="You no longer have access to this ticket",
                )

            except (WebSocketDisconnect, RuntimeError, OSError):
                pass

            finally:
                self.disconnect(ticket_id, websocket)

    async def broadcast(
        self,
        ticket_id: UUID,
        message: dict,
        exclude_roles: set[str] | None = None,
    ):
        """Send a message to connected users of a particular ticket."""

        connections = self.active_connections.get(ticket_id, {})

        for websocket, (_, user_role) in list(connections.items()):

            if exclude_roles and user_role in exclude_roles:
                continue

            try:
                await websocket.send_json(message)

            except (WebSocketDisconnect, RuntimeError, OSError):
                self.disconnect(ticket_id, websocket)

    async def disconnect_user_from_all_tickets(self, user_id: UUID):
        """
        Disconnect a user from every ticket WebSocket connection.
        """

        user_connections = []

        for ticket_id, connections in list(self.active_connections.items()):
            for websocket, (connected_user_id, _) in list(connections.items()):
                if connected_user_id == user_id:
                    user_connections.append((ticket_id, websocket))

        for ticket_id, websocket in user_connections:
            try:
                await websocket.close(
                    code=1008,
                    reason="Your account has been deactivated",
                )
            except (WebSocketDisconnect, RuntimeError, OSError):
                pass
            finally:
                self.disconnect(ticket_id, websocket)

# Shared manager instance for the application process.
websocket_manager = WebSocketConnectionManager()

