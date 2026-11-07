import pytest


@pytest.mark.asyncio
async def test_customer_can_create_and_list_own_tickets(client, user_factory, auth_headers):
    customer = await user_factory()
    headers = auth_headers(customer)

    created = await client.post("/api/v1/tickets/", headers=headers, json={
        "title": "Cannot access account",
        "description": "I cannot sign in to my account after resetting my password.",
    })
    assert created.status_code == 201, created.text
    ticket = created.json()
    assert ticket["title"] == "Cannot access account"
    assert ticket["status"] == "OPEN"
    assert ticket["priority"] == "MEDIUM"

    listed = await client.get("/api/v1/tickets/", headers=headers)
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == ticket["id"]


@pytest.mark.asyncio
async def test_customer_can_retrieve_and_update_own_ticket(client, ticket_factory, auth_headers):
    customer, ticket = await ticket_factory()
    headers = auth_headers(customer)

    retrieved = await client.get(f"/api/v1/tickets/{ticket['id']}", headers=headers)
    assert retrieved.status_code == 200, retrieved.text

    updated = await client.patch(
        f"/api/v1/tickets/{ticket['id']}",
        headers=headers,
        json={"title": "Updated support ticket title"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["title"] == "Updated support ticket title"


@pytest.mark.asyncio
async def test_ticket_creation_rejects_invalid_category(client, user_factory, auth_headers):
    customer = await user_factory()
    response = await client.post("/api/v1/tickets/", headers=auth_headers(customer), json={
        "title": "Invalid category ticket",
        "description": "This ticket references a category that does not exist.",
        "category_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ticket_list_pagination(client, user_factory, auth_headers):
    customer = await user_factory()
    headers = auth_headers(customer)
    for number in range(3):
        response = await client.post("/api/v1/tickets/", headers=headers, json={
            "title": f"Pagination ticket {number}",
            "description": "A valid description for pagination test tickets.",
        })
        assert response.status_code == 201

    page = await client.get("/api/v1/tickets/?page=1&limit=2", headers=headers)
    assert page.status_code == 200
    data = page.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["limit"] == 2
    assert data["total_pages"] == 2
