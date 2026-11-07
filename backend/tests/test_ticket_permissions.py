import pytest


@pytest.mark.asyncio
async def test_customer_cannot_view_another_customers_ticket(client, ticket_factory, user_factory, auth_headers):
    _, ticket = await ticket_factory()
    other_customer = await user_factory(role="CUSTOMER")

    response = await client.get(
        f"/api/v1/tickets/{ticket['id']}",
        headers=auth_headers(other_customer),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_can_assign_ticket_and_assigned_agent_can_update_it(
    client, ticket_factory, user_factory, auth_headers
):
    _, ticket = await ticket_factory()
    admin = await user_factory(role="ADMIN")
    agent = await user_factory(role="AGENT")

    assigned = await client.post(
        f"/api/v1/agents/tickets/{ticket['id']}/assign",
        headers=auth_headers(admin),
        json={"agent_id": str(agent.id)},
    )
    assert assigned.status_code == 201, assigned.text
    assert assigned.json()["agent_id"] == str(agent.id)

    agent_update = await client.patch(
        f"/api/v1/agents/tickets/{ticket['id']}",
        headers=auth_headers(agent),
        json={"status": "IN_PROGRESS", "priority": "HIGH"},
    )
    assert agent_update.status_code == 200, agent_update.text
    assert agent_update.json()["status"] == "IN_PROGRESS"
    assert agent_update.json()["priority"] == "HIGH"


@pytest.mark.asyncio
async def test_unassigned_agent_cannot_update_ticket(client, ticket_factory, user_factory, auth_headers):
    _, ticket = await ticket_factory()
    agent = await user_factory(role="AGENT")

    response = await client.patch(
        f"/api/v1/agents/tickets/{ticket['id']}",
        headers=auth_headers(agent),
        json={"status": "IN_PROGRESS"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_customer_cannot_use_agent_ticket_update_endpoint(client, ticket_factory, auth_headers):
    customer, ticket = await ticket_factory()
    response = await client.patch(
        f"/api/v1/agents/tickets/{ticket['id']}",
        headers=auth_headers(customer),
        json={"status": "IN_PROGRESS"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_invalid_ticket_status_transition_is_rejected(client, ticket_factory, user_factory, auth_headers):
    _, ticket = await ticket_factory()
    admin = await user_factory(role="ADMIN")

    response = await client.patch(
        f"/api/v1/agents/tickets/{ticket['id']}",
        headers=auth_headers(admin),
        json={"status": "CLOSED"},
    )
    assert response.status_code == 400
