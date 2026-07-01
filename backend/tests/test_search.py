import pytest
import uuid
from httpx import AsyncClient


async def get_auth_headers(client: AsyncClient) -> dict:
    unique_id = str(uuid.uuid4())[:8]
    username = f"search_{unique_id}"
    await client.post(
        "/api/auth/register",
        json={"username": username, "email": f"{unique_id}@test.com", "password": "pass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"username": username, "password": "pass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_search_metadata(client: AsyncClient):
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    knowledge_id = f"search-{unique_id}"
    # Create knowledge
    await client.post(
        "/api/knowledge",
        json={"name": knowledge_id, "description": "Test search", "tags": ["search"]},
        headers=headers,
    )
    # Search
    response = await client.get(
        "/api/search",
        params={"q": "search", "mode": "metadata"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_search_content(client: AsyncClient):
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    knowledge_id = f"search-{unique_id}"
    # Create knowledge and file
    await client.post(
        "/api/knowledge",
        json={"name": knowledge_id, "description": "", "tags": []},
        headers=headers,
    )
    await client.put(
        f"/api/knowledge/{knowledge_id}/file/test.md",
        content="# Hello World\nThis is a test file.",
        headers=headers,
    )
    # Search content
    response = await client.get(
        "/api/search",
        params={"q": "Hello", "mode": "content"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


@pytest.mark.asyncio
async def test_search_all(client: AsyncClient):
    headers = await get_auth_headers(client)
    response = await client.get(
        "/api/search",
        params={"q": "test", "mode": "all"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data
