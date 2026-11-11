
import asyncio
import json
from pathlib import Path

import httpx
import websockets
from websockets.exceptions import ConnectionClosed


BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"


# Load local test configuration.
CONFIG_PATH = Path(__file__).parent / "test_config.local.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    CONFIG = json.load(file)


async def login_user(client, account):
    """Login and return a fresh access token."""

    response = await client.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "email": account["email"],
            "password": account["password"],
        },
    )

    response.raise_for_status()

    return response.json()["access_token"]


async def get_agent_b_id(client, admin_token):
    """Find Agent B using the admin agents API."""

    response = await client.get(
        f"{BASE_URL}/api/v1/admin/agents",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    response.raise_for_status()

    agents = response.json()

    for agent in agents:
        if agent["email"].lower() == CONFIG["agent_b"]["email"].lower():
            if not agent["is_active"]:
                raise ValueError("Agent B is inactive")

            return agent["id"]

    raise ValueError("Agent B was not found")


async def connect_user(client, access_token, ticket_id):
    """Obtain a WebSocket ticket and establish a connection."""

    response = await client.post(
        f"{BASE_URL}/api/v1/ws/ticket",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
    )

    response.raise_for_status()

    websocket_ticket = response.json()["ticket"]

    websocket = await websockets.connect(
        f"{WS_URL}/api/v1/ws/{ticket_id}?ticket={websocket_ticket}",
        origin="http://localhost:5173",
    )

    confirmation = await websocket.recv()

    print("Connected:", confirmation)

    return websocket


async def test_reassignment():

    ticket_id = CONFIG["ticket_id"]

    async with httpx.AsyncClient() as client:

        # ----------------------------------
        # STEP 1: LOGIN ALL USERS
        # ----------------------------------

        print("\nSTEP 1: Authenticating users...")

        customer_token = await login_user(
            client, CONFIG["customer"]
        )

        agent_a_token = await login_user(
            client, CONFIG["agent_a"]
        )

        agent_b_token = await login_user(
            client, CONFIG["agent_b"]
        )

        admin_token = await login_user(
            client, CONFIG["admin"]
        )

        print("PASS: All four users authenticated.")

        # ----------------------------------
        # STEP 2: IDENTIFY AGENT B
        # ----------------------------------

        agent_b_id = await get_agent_b_id(
            client, admin_token
        )

        print("PASS: Agent B identified.")

        customer_ws = None
        agent_a_ws = None
        agent_b_ws = None

        try:

            # ----------------------------------
            # STEP 3: CONNECT CUSTOMER AND AGENT A
            # ----------------------------------

            print("\nSTEP 2: Establishing existing connections...")

            customer_ws = await connect_user(
                client, customer_token, ticket_id
            )

            agent_a_ws = await connect_user(
                client, agent_a_token, ticket_id
            )

            print("PASS: Customer and Agent A connected.")

            # ----------------------------------
            # STEP 4: REASSIGN TICKET
            # ----------------------------------

            print("\nSTEP 3: Reassigning ticket to Agent B...")

            response = await client.post(
                f"{BASE_URL}/api/v1/agents/tickets/{ticket_id}/assign",
                headers={
                    "Authorization": f"Bearer {admin_token}"
                },
                json={
                    "agent_id": agent_b_id
                },
            )

            print("Assignment HTTP status:", response.status_code)

            if response.status_code != 201:
                print("Assignment response:", response.text)

            response.raise_for_status()

            print("PASS: Ticket reassigned successfully.")

            # ----------------------------------
            # STEP 5: VERIFY AGENT A DISCONNECTION
            # ----------------------------------

            print("\nSTEP 4: Checking Agent A connection...")

            try:
                await asyncio.wait_for(
                    agent_a_ws.recv(),
                    timeout=5,
                )

                raise AssertionError(
                    "Agent A's connection is still open."
                )

            except ConnectionClosed:
                print("PASS: Agent A was disconnected.")

            except asyncio.TimeoutError:
                raise AssertionError(
                    "Agent A was not disconnected within 5 seconds."
                )

            # ----------------------------------
            # STEP 6: CONNECT AGENT B
            # ----------------------------------

            print("\nSTEP 5: Connecting Agent B...")

            agent_b_ws = await connect_user(
                client, agent_b_token, ticket_id
            )

            print("PASS: Agent B connected successfully.")

            # ----------------------------------
            # STEP 7: VERIFY CUSTOMER CONNECTION
            # ----------------------------------

            print("\nSTEP 6: Testing message delivery...")

            test_message = (
                "Testing message after ticket reassignment."
            )

            response = await client.post(
                f"{BASE_URL}/api/v1/tickets/{ticket_id}/messages",
                headers={
                    "Authorization": f"Bearer {agent_b_token}"
                },
                json={
                    "content": test_message,
                    "is_internal": False,
                },
            )

            response.raise_for_status()

            customer_message = json.loads(
                await asyncio.wait_for(
                    customer_ws.recv(),
                    timeout=5,
                )
            )

            agent_b_message = json.loads(
                await asyncio.wait_for(
                    agent_b_ws.recv(),
                    timeout=5,
                )
            )

            assert customer_message["content"] == test_message
            assert agent_b_message["content"] == test_message

            print("PASS: Customer remained connected.")
            print("PASS: Customer received Agent B's message.")
            print("PASS: Agent B received the broadcast.")

            print("\nALL REASSIGNMENT TESTS PASSED.")

        finally:

            # Close all remaining test connections.
            for websocket in (
                customer_ws,
                agent_a_ws,
                agent_b_ws,
            ):
                if websocket is not None:
                    try:
                        await websocket.close()
                    except Exception:
                        pass


asyncio.run(test_reassignment())
