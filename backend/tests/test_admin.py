import pytest


@pytest.mark.asyncio
async def test_admin_can_create_agent_and_list_customers(client, user_factory, auth_headers):
    admin = await user_factory(role="ADMIN")
    headers = auth_headers(admin)

    created = await client.post("/api/v1/admin/agents", headers=headers, json={
        "full_name": "New Support Agent",
        "email": "new-agent@example.com",
        "password": "StrongPassword123",
    })
    assert created.status_code == 201, created.text
    assert created.json()["role"] == "AGENT"

    customer = await user_factory(role="CUSTOMER")
    customers = await client.get("/api/v1/admin/customers", headers=headers)
    assert customers.status_code == 200
    assert any(item["id"] == str(customer.id) for item in customers.json())


@pytest.mark.asyncio
async def test_admin_can_deactivate_and_reactivate_agent(client, user_factory, auth_headers):
    admin = await user_factory(role="ADMIN")
    agent = await user_factory(role="AGENT")
    headers = auth_headers(admin)

    deactivated = await client.patch(
        f"/api/v1/admin/agents/{agent.id}/status",
        headers=headers,
        json={"is_active": False},
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False

    reactivated = await client.patch(
        f"/api/v1/admin/agents/{agent.id}/status",
        headers=headers,
        json={"is_active": True},
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["is_active"] is True


@pytest.mark.asyncio
async def test_non_admin_cannot_access_admin_management(client, user_factory, auth_headers):
    customer = await user_factory()
    response = await client.get(
        "/api/v1/admin/agents",
        headers=auth_headers(customer),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_analytics_is_admin_only(client, user_factory, auth_headers):
    admin = await user_factory(role="ADMIN")
    customer = await user_factory(role="CUSTOMER")

    admin_response = await client.get(
        "/api/v1/admin/analytics/overview",
        headers=auth_headers(admin),
    )
    assert admin_response.status_code == 200, admin_response.text

    customer_response = await client.get(
        "/api/v1/admin/analytics/overview",
        headers=auth_headers(customer),
    )
    assert customer_response.status_code == 403
