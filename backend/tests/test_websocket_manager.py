
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.websocket_manager import WebSocketConnectionManager


@pytest.mark.asyncio
async def test_connect_and_disconnect():
    manager = WebSocketConnectionManager()

    ticket_id = uuid4()
    user_id = uuid4()
    websocket = AsyncMock()

    # Register the connection.
    await manager.connect(
        ticket_id=ticket_id,
        websocket=websocket,
        user_id=user_id,
        user_role="CUSTOMER",
    )

    assert websocket in manager.active_connections[ticket_id]

    # Remove the connection.
    manager.disconnect(ticket_id, websocket)

    assert ticket_id not in manager.active_connections


@pytest.mark.asyncio
async def test_broadcast_message():
    manager = WebSocketConnectionManager()

    ticket_id = uuid4()

    customer_id = uuid4()
    agent_id = uuid4()

    customer_socket = AsyncMock()
    agent_socket = AsyncMock()

    await manager.connect(
        ticket_id, customer_socket, customer_id, "CUSTOMER"
    )

    await manager.connect(
        ticket_id, agent_socket, agent_id, "AGENT"
    )

    message = {
        "content": "Hello, how can I help you?"
    }

    await manager.broadcast(ticket_id, message)

    customer_socket.send_json.assert_awaited_once_with(message)
    agent_socket.send_json.assert_awaited_once_with(message)


@pytest.mark.asyncio
async def test_broadcast_excludes_customers():
    manager = WebSocketConnectionManager()

    ticket_id = uuid4()

    customer_id = uuid4()
    agent_id = uuid4()

    customer_socket = AsyncMock()
    agent_socket = AsyncMock()

    await manager.connect(
        ticket_id, customer_socket, customer_id, "CUSTOMER"
    )

    await manager.connect(
        ticket_id, agent_socket, agent_id, "AGENT"
    )

    internal_note = {
        "content": "Internal discussion between agents."
    }

    await manager.broadcast(
        ticket_id,
        internal_note,
        exclude_roles={"CUSTOMER"},
    )

    customer_socket.send_json.assert_not_awaited()
    agent_socket.send_json.assert_awaited_once_with(internal_note)


@pytest.mark.asyncio
async def test_disconnect_specific_user():
    manager = WebSocketConnectionManager()

    ticket_id = uuid4()

    customer_id = uuid4()
    agent_a_id = uuid4()
    agent_b_id = uuid4()

    customer_socket = AsyncMock()
    agent_a_socket = AsyncMock()
    agent_b_socket = AsyncMock()

    await manager.connect(
        ticket_id, customer_socket, customer_id, "CUSTOMER"
    )

    await manager.connect(
        ticket_id, agent_a_socket, agent_a_id, "AGENT"
    )

    await manager.connect(
        ticket_id, agent_b_socket, agent_b_id, "AGENT"
    )

    # Disconnect only Agent A.
    await manager.disconnect_user(ticket_id, agent_a_id)

    agent_a_socket.close.assert_awaited_once()

    # Customer and Agent B must remain connected.
    assert customer_socket in manager.active_connections[ticket_id]
    assert agent_b_socket in manager.active_connections[ticket_id]

    # Agent A must be removed.
    assert agent_a_socket not in manager.active_connections[ticket_id]
