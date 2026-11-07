
import pytest


@pytest.mark.asyncio
async def test_register_user(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test Customer",
            "email": "customer@example.com",
            "password": "StrongPassword123"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Test Customer"
    assert data["email"] == "customer@example.com"
    assert data["role"] == "CUSTOMER"
    assert data["is_active"] is True

    # Password must never be returned in the response.
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    user_data = {
        "full_name": "Test Customer",
        "email": "duplicate@example.com",
        "password": "StrongPassword123"
    }

    # First registration should succeed.
    first_response = await client.post(
        "/api/v1/auth/register",
        json=user_data
    )

    assert first_response.status_code == 201

    # Second registration with the same email should fail.
    second_response = await client.post(
        "/api/v1/auth/register",
        json=user_data
    )

    assert second_response.status_code == 409


@pytest.mark.asyncio
async def test_login_user(client):
    # First, register a user.
    await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Login Customer",
            "email": "login@example.com",
            "password": "StrongPassword123"
        }
    )

    # Now login with the registered credentials.
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "StrongPassword123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"

    assert data["user"]["email"] == "login@example.com"
    assert data["user"]["role"] == "CUSTOMER"


@pytest.mark.asyncio
async def test_login_with_incorrect_password(client):
    # Register a user.
    await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Login Customer",
            "email": "wrongpass@example.com",
            "password": "StrongPassword123"
        }
    )

    # Attempt login with an incorrect password.
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "IncorrectPassword123"
        }
    )

    assert response.status_code == 401
