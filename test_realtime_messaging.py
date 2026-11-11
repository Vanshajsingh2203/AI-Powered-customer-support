
import asyncio
import json
from getpass import getpass

import httpx
import websockets


BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"


async def get_websocket_ticket(client, access_token):
    response = await client.post(
        f"{BASE_URL}/api/v1/ws/ticket",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()["ticket"]


async def connect_user(client, access_token, ticket_id):
    ticket = await get_websocket_ticket(client, access_token)

    websocket = await websockets.connect(
        f"{WS_URL}/api/v1/ws/{ticket_id}?ticket={ticket}",
        origin="http://localhost:5173",
    )

    # Read the initial connection confirmation.
    confirmation = await websocket.recv()
    print("Connected:", confirmation)

    return websocket


async def test_realtime_messaging():
    customer_token = getpass("Customer access token: ")
    agent_token = getpass("Agent access token: ")
    ticket_id = input("Ticket UUID: ").strip()

    async with httpx.AsyncClient() as client:

        # Establish both WebSocket connections.
        customer_ws = await connect_user(
            client, customer_token, ticket_id
        )

        agent_ws = await connect_user(
            client, agent_token, ticket_id
        )

        try:
            # ----------------------------------
            # TEST 1: PUBLIC MESSAGE
            # ----------------------------------

            print("\nTEST 1: Sending public message...")

            response = await client.post(
                f"{BASE_URL}/api/v1/tickets/{ticket_id}/messages",
                headers={
                    "Authorization": f"Bearer {agent_token}"
                },
                json={
                    "content": "Testing real-time public messaging.",
                    "is_internal": False,
                },
            )

            print("HTTP status:", response.status_code)
            response.raise_for_status()

            customer_message = json.loads(
                await asyncio.wait_for(customer_ws.recv(), timeout=5)
            )

            agent_message = json.loads(
                await asyncio.wait_for(agent_ws.recv(), timeout=5)
            )

            assert customer_message["content"] == (
                "Testing real-time public messaging."
            )

            assert agent_message["content"] == (
                "Testing real-time public messaging."
            )

            print("PASS: Customer received public message.")
            print("PASS: Agent received public message.")

            # ----------------------------------
            # TEST 2: INTERNAL NOTE
            # ----------------------------------

            print("\nTEST 2: Sending internal note...")

            response = await client.post(
                f"{BASE_URL}/api/v1/tickets/{ticket_id}/messages",
                headers={
                    "Authorization": f"Bearer {agent_token}"
                },
                json={
                    "content": "Testing private internal notes.",
                    "is_internal": True,
                },
            )

            print("HTTP status:", response.status_code)
            response.raise_for_status()

            agent_message = json.loads(
                await asyncio.wait_for(agent_ws.recv(), timeout=5)
            )

            assert agent_message["content"] == (
                "Testing private internal notes."
            )

            print("PASS: Agent received internal note.")

            try:
                await asyncio.wait_for(customer_ws.recv(), timeout=2)

                print("FAIL: Customer received an internal note!")

            except asyncio.TimeoutError:
                print("PASS: Customer did not receive internal note.")

        finally:
            await customer_ws.close()
            await agent_ws.close()


asyncio.run(test_realtime_messaging())
