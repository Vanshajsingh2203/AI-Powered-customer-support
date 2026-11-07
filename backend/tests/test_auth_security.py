import pytest


@pytest.mark.asyncio
async def test_refresh_token_rotates_token_pair(client):
    registered = await client.post("/api/v1/auth/register", json={
        "full_name": "Refresh Customer",
        "email": "refresh@example.com",
        "password": "StrongPassword123",
    })
    assert registered.status_code == 201

    login = await client.post("/api/v1/auth/login", json={
        "email": "refresh@example.com",
        "password": "StrongPassword123",
    })
    assert login.status_code == 200
    old_refresh = login.json()["refresh_token"]

    refreshed = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": old_refresh,
    })
    assert refreshed.status_code == 200, refreshed.text
    data = refreshed.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["refresh_token"] != old_refresh
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_reusing_rotated_refresh_token_revokes_token_family(client):
    await client.post("/api/v1/auth/register", json={
        "full_name": "Reuse Customer",
        "email": "reuse@example.com",
        "password": "StrongPassword123",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "reuse@example.com",
        "password": "StrongPassword123",
    })
    old_refresh = login.json()["refresh_token"]

    first_refresh = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": old_refresh,
    })
    assert first_refresh.status_code == 200
    replacement = first_refresh.json()["refresh_token"]

    reuse = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": old_refresh,
    })
    assert reuse.status_code == 401
    assert "reuse" in reuse.json()["detail"].lower()

    # Reuse detection revokes all still-active tokens in the same family.
    replacement_attempt = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": replacement,
    })
    assert replacement_attempt.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client):
    await client.post("/api/v1/auth/register", json={
        "full_name": "Logout Customer",
        "email": "logout@example.com",
        "password": "StrongPassword123",
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "logout@example.com",
        "password": "StrongPassword123",
    })
    refresh_token = login.json()["refresh_token"]

    logout = await client.post("/api/v1/auth/logout", json={
        "refresh_token": refresh_token,
    })
    assert logout.status_code == 200

    reuse = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert reuse.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rejects_unknown_token(client):
    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": "not-a-valid-refresh-token",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_missing_or_invalid_access_token(client):
    missing = await client.get("/api/v1/tickets/")
    assert missing.status_code in (401, 403)  # HTTPBearer may return 403 when credentials are absent.

    invalid = await client.get(
        "/api/v1/tickets/",
        headers={"Authorization": "Bearer definitely.invalid.token"},
    )
    assert invalid.status_code == 401
