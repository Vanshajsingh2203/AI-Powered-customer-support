import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_database_health_endpoint(client):
    response = await client.get("/db_check")
    assert response.status_code == 200, response.text
    assert response.json()["database"] == "connected"
    assert response.json()["result"] == 1
