import pytest
import uuid
from httpx import AsyncClient


async def get_auth_headers(client: AsyncClient) -> dict:
    unique_id = str(uuid.uuid4())[:8]
    username = f"lock_{unique_id}"
    await client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{unique_id}@test.com", "password": "pass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"username": username, "password": "pass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, f"lock-{unique_id}"


@pytest.mark.asyncio
async def test_acquire_lock(client: AsyncClient):
    headers, knowledge_id = await get_auth_headers(client)
    await client.post(
        "/api/knowledge",
        json={"name": knowledge_id, "description": "", "tags": []},
        headers=headers,
    )
    response = await client.post(
        "/api/lock",
        json={"knowledge_id": knowledge_id, "file_path": "test.md"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_lock_status(client: AsyncClient):
    headers, knowledge_id = await get_auth_headers(client)
    await client.post(
        "/api/knowledge",
        json={"name": knowledge_id, "description": "", "tags": []},
        headers=headers,
    )
    await client.post(
        "/api/lock",
        json={"knowledge_id": knowledge_id, "file_path": "test.md"},
        headers=headers,
    )
    response = await client.get(
        f"/api/lock/status?knowledge_id={knowledge_id}&file_path=test.md",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["locked"] is True


@pytest.mark.asyncio
async def test_release_lock(client: AsyncClient):
    headers, knowledge_id = await get_auth_headers(client)
    await client.post(
        "/api/knowledge",
        json={"name": knowledge_id, "description": "", "tags": []},
        headers=headers,
    )
    await client.post(
        "/api/lock",
        json={"knowledge_id": knowledge_id, "file_path": "test.md"},
        headers=headers,
    )
    response = await client.request(
        "DELETE",
        "/api/lock",
        json={"knowledge_id": knowledge_id, "file_path": "test.md"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
