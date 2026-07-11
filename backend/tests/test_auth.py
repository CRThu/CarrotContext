import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    unique_id = str(uuid.uuid4())[:8]
    response = await client.post(
        "/api/auth/register",
        json={
            "username": f"user_{unique_id}",
            "email": f"{unique_id}@test.com",
            "password": "testpass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == f"user_{unique_id}"
    assert "id" in data


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    unique_id = str(uuid.uuid4())[:8]
    username = f"login_{unique_id}"
    await client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{unique_id}@test.com", "password": "pass123"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"username": username, "password": "pass123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    unique_id = str(uuid.uuid4())[:8]
    username = f"wrong_{unique_id}"
    await client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{unique_id}@test.com", "password": "pass123"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"username": username, "password": "wrongpass"},
    )
    assert response.status_code == 401
