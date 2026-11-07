import pytest
from app.models.message import TicketMessage


@pytest.mark.asyncio
async def test_customer_can_send_and_retrieve_message(client, ticket_factory, auth_headers):
    customer, ticket = await ticket_factory()
    headers = auth_headers(customer)

    sent = await client.post(
        f"/api/v1/tickets/{ticket['id']}/messages",
        headers=headers,
        json={"content": "I can provide more information about this issue."},
    )
    assert sent.status_code == 201, sent.text
    assert sent.json()["content"] == "I can provide more information about this issue."
    assert sent.json()["is_internal"] is False

    messages = await client.get(
        f"/api/v1/tickets/{ticket['id']}/messages",
        headers=headers,
    )
    assert messages.status_code == 200
    assert len(messages.json()) == 1


@pytest.mark.asyncio
async def test_customer_does_not_see_internal_messages(
    client, ticket_factory, user_factory, auth_headers, db_session
):
    customer, ticket = await ticket_factory()
    admin = await user_factory(role="ADMIN")
    db_session.add(TicketMessage(
        ticket_id=ticket["id"],
        sender_id=admin.id,
        content="Internal note for support staff only.",
        is_internal=True,
    ))
    await db_session.flush()

    customer_messages = await client.get(
        f"/api/v1/tickets/{ticket['id']}/messages",
        headers=auth_headers(customer),
    )
    assert customer_messages.status_code == 200
    assert all(not message["is_internal"] for message in customer_messages.json())

    admin_messages = await client.get(
        f"/api/v1/tickets/{ticket['id']}/messages",
        headers=auth_headers(admin),
    )
    assert admin_messages.status_code == 200
    assert any(message["is_internal"] for message in admin_messages.json())


@pytest.mark.asyncio
async def test_customer_cannot_send_message_to_another_customers_ticket(
    client, ticket_factory, user_factory, auth_headers
):
    _, ticket = await ticket_factory()
    other_customer = await user_factory()

    response = await client.post(
        f"/api/v1/tickets/{ticket['id']}/messages",
        headers=auth_headers(other_customer),
        json={"content": "I should not be able to post here."},
    )
    assert response.status_code == 404
