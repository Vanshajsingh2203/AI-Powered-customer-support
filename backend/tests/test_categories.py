import pytest


@pytest.mark.asyncio
async def test_admin_can_create_list_update_and_delete_category(client, user_factory, auth_headers):
    admin = await user_factory(role="ADMIN")
    headers = auth_headers(admin)

    created = await client.post("/api/v1/admin/categories", headers=headers, json={
        "name": "Billing",
        "description": "Billing and payment questions",
    })
    assert created.status_code == 201, created.text
    category_id = created.json()["id"]

    listed = await client.get("/api/v1/admin/categories", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == category_id for item in listed.json())

    updated = await client.patch(
        f"/api/v1/admin/categories/{category_id}",
        headers=headers,
        json={"description": "Updated billing description"},
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Updated billing description"

    deleted = await client.delete(
        f"/api/v1/admin/categories/{category_id}",
        headers=headers,
    )
    assert deleted.status_code == 200


@pytest.mark.asyncio
async def test_category_name_is_case_insensitively_unique(client, user_factory, auth_headers):
    admin = await user_factory(role="ADMIN")
    headers = auth_headers(admin)

    first = await client.post("/api/v1/admin/categories", headers=headers, json={"name": "Technical"})
    assert first.status_code == 201

    duplicate = await client.post("/api/v1/admin/categories", headers=headers, json={"name": "technical"})
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_category_cannot_be_deleted_while_ticket_uses_it(
    client, user_factory, auth_headers, ticket_factory
):
    admin = await user_factory(role="ADMIN")
    headers = auth_headers(admin)
    category = await client.post(
        "/api/v1/admin/categories",
        headers=headers,
        json={"name": "Account"},
    )
    assert category.status_code == 201
    await ticket_factory(category_id=category.json()["id"])

    deleted = await client.delete(
        f"/api/v1/admin/categories/{category.json()['id']}",
        headers=headers,
    )
    assert deleted.status_code == 409


@pytest.mark.asyncio
async def test_customer_cannot_manage_categories(client, user_factory, auth_headers):
    customer = await user_factory()
    response = await client.get(
        "/api/v1/admin/categories",
        headers=auth_headers(customer),
    )
    assert response.status_code == 403
