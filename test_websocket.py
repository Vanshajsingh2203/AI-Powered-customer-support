
import asyncio
import json
from pathlib import Path

import httpx
import websockets
from websockets.exceptions import ConnectionClosed


BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"

CONFIG_PATH = Path(__file__).parent / "test_config.local.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    CONFIG = json.load(file)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

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


async def get_agent_id(client, admin_token, account):
    """Find an agent using the admin agents API."""

    response = await client.get(
        f"{BASE_URL}/api/v1/admin/agents",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    response.raise_for_status()

    for agent in response.json():
        if agent["email"].lower() == account["email"].lower():
            return agent["id"]

    raise ValueError("Agent was not found")


async def get_customer_id(client, admin_token, account):
    """Find a customer using the admin customers API."""

    response = await client.get(
        f"{BASE_URL}/api/v1/admin/customers",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    response.raise_for_status()

    for customer in response.json():
        if customer["email"].lower() == account["email"].lower():
            return customer["id"]

    raise ValueError("Customer was not found")


async def connect_user(client, access_token, ticket_id):
    """Obtain a single-use WebSocket ticket and connect."""

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


async def update_account_status(
    client,
    admin_token,
    account_type,
    user_id,
    is_active,
):
    """Activate or deactivate an account through the admin API."""

    response = await client.patch(
        f"{BASE_URL}/api/v1/admin/{account_type}/{user_id}/status",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "is_active": is_active
        },
    )

    if response.status_code != 200:
        print("Status update response:", response.text)

    response.raise_for_status()

    return response


async def verify_disconnection(websocket, account_name):
    """Verify that an existing WebSocket connection is closed."""

    try:
        await asyncio.wait_for(
            websocket.recv(),
            timeout=5,
        )

        raise AssertionError(
            f"{account_name} connection is still open."
        )

    except ConnectionClosed:
        print(f"PASS: {account_name} was disconnected.")

    except asyncio.TimeoutError:
        raise AssertionError(
            f"{account_name} was not disconnected within 5 seconds."
        )


async def verify_reconnection_rejected(
    client,
    access_token,
    account_name,
    ticket_id,
):
    """Verify that a deactivated user cannot obtain a new WS ticket."""

    response = await client.post(
        f"{BASE_URL}/api/v1/ws/ticket",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
    )

    if response.status_code == 401:
        print(
            f"PASS: {account_name} cannot obtain a new WebSocket ticket."
        )
        return

    raise AssertionError(
        f"{account_name} was able to obtain a WebSocket ticket "
        f"after deactivation. HTTP status: {response.status_code}"
    )


# ==========================================
# MAIN INTEGRATION TEST
# ==========================================

async def test_account_deactivation():

    ticket_id = CONFIG["ticket_id"]

    async with httpx.AsyncClient() as client:

        # ----------------------------------
        # STEP 1: AUTHENTICATE USERS
        # ----------------------------------

        print("\nSTEP 1: Authenticating users...")

        admin_token = await login_user(
            client,
            CONFIG["admin"],
        )

        customer_token = await login_user(
            client,
            CONFIG["customer"],
        )

        agent_token = await login_user(
            client,
            CONFIG["agent_a"],
        )

        print("PASS: Admin, customer and Agent A authenticated.")

        # ----------------------------------
        # STEP 2: IDENTIFY USERS
        # ----------------------------------

        agent_id = await get_agent_id(
            client,
            admin_token,
            CONFIG["agent_a"],
        )

        customer_id = await get_customer_id(
            client,
            admin_token,
            CONFIG["customer"],
        )

        print("PASS: Agent A identified.")
        print("PASS: Customer identified.")

        # ----------------------------------
        # STEP 3: ENSURE TICKET ASSIGNMENT
        # ----------------------------------

        print("\nSTEP 2: Assigning test ticket to Agent A...")

        response = await client.post(
            f"{BASE_URL}/api/v1/agents/tickets/{ticket_id}/assign",
            headers={
                "Authorization": f"Bearer {admin_token}"
            },
            json={
                "agent_id": agent_id
            },
        )

        response.raise_for_status()

        print("PASS: Test ticket assigned to Agent A.")

        # ==========================================
        # TEST 1: AGENT DEACTIVATION
        # ==========================================

        print("\n======================================")
        print("TEST 1: AGENT ACCOUNT DEACTIVATION")
        print("======================================")

        agent_ws = None
        customer_ws = None

        try:

            # ----------------------------------
            # STEP 4: ESTABLISH CONNECTIONS
            # ----------------------------------

            print("\nSTEP 3: Connecting Agent A and customer...")

            agent_ws = await connect_user(
                client,
                agent_token,
                ticket_id,
            )

            customer_ws = await connect_user(
                client,
                customer_token,
                ticket_id,
            )

            print("PASS: Both users connected.")

            # ----------------------------------
            # STEP 5: DEACTIVATE AGENT
            # ----------------------------------

            print("\nSTEP 4: Deactivating Agent A...")

            response = await update_account_status(
                client,
                admin_token,
                "agents",
                agent_id,
                False,
            )

            print("Deactivation HTTP status:", response.status_code)
            print("PASS: Agent A deactivated.")

            # ----------------------------------
            # STEP 6: VERIFY DISCONNECTION
            # ----------------------------------

            print("\nSTEP 5: Checking Agent A connection...")

            await verify_disconnection(
                agent_ws,
                "Agent A",
            )

            # ----------------------------------
            # STEP 7: VERIFY RECONNECTION REJECTION
            # ----------------------------------

            print("\nSTEP 6: Checking Agent A reconnection...")

            await verify_reconnection_rejected(
                client,
                agent_token,
                "Agent A",
                ticket_id,
            )

        finally:

            if agent_ws is not None:
                try:
                    await agent_ws.close()
                except Exception:
                    pass

            if customer_ws is not None:
                try:
                    await customer_ws.close()
                except Exception:
                    pass

            # Restore Agent A for the next test.
            await update_account_status(
                client,
                admin_token,
                "agents",
                agent_id,
                True,
            )

            print("Agent A account restored to active.")

        # ==========================================
        # TEST 2: CUSTOMER DEACTIVATION
        # ==========================================

        print("\n======================================")
        print("TEST 2: CUSTOMER ACCOUNT DEACTIVATION")
        print("======================================")

        customer_ws = None
        agent_ws = None

        try:

            # ----------------------------------
            # STEP 8: ESTABLISH CONNECTIONS
            # ----------------------------------

            print("\nSTEP 7: Connecting customer and Agent A...")

            customer_ws = await connect_user(
                client,
                customer_token,
                ticket_id,
            )

            agent_ws = await connect_user(
                client,
                agent_token,
                ticket_id,
            )

            print("PASS: Both users connected.")

            # ----------------------------------
            # STEP 9: DEACTIVATE CUSTOMER
            # ----------------------------------

            print("\nSTEP 8: Deactivating customer...")

            response = await update_account_status(
                client,
                admin_token,
                "customers",
                customer_id,
                False,
            )

            print("Deactivation HTTP status:", response.status_code)
            print("PASS: Customer deactivated.")

            # ----------------------------------
            # STEP 10: VERIFY DISCONNECTION
            # ----------------------------------

            print("\nSTEP 9: Checking customer connection...")

            await verify_disconnection(
                customer_ws,
                "Customer",
            )

            # ----------------------------------
            # STEP 11: VERIFY RECONNECTION REJECTION
            # ----------------------------------

            print("\nSTEP 10: Checking customer reconnection...")

            await verify_reconnection_rejected(
                client,
                customer_token,
                "Customer",
                ticket_id,
            )

        finally:

            if customer_ws is not None:
                try:
                    await customer_ws.close()
                except Exception:
                    pass

            if agent_ws is not None:
                try:
                    await agent_ws.close()
                except Exception:
                    pass

            # Restore customer for future testing.
            await update_account_status(
                client,
                admin_token,
                "customers",
                customer_id,
                True,
            )

            print("Customer account restored to active.")

        print("\nALL ACCOUNT DEACTIVATION TESTS PASSED.")


asyncio.run(test_account_deactivation())
