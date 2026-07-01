import pytest
import uuid
from httpx import AsyncClient


async def get_auth_headers(client: AsyncClient) -> dict:
    unique_id = str(uuid.uuid4())[:8]
    username = f"ktest_{unique_id}"
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
async def test_create_knowledge(client: AsyncClient):
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    response = await client.post(
        "/api/knowledge",
        json={"name": f"Test-{unique_id}", "description": "A test", "tags": ["test"]},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == f"Test-{unique_id}"


@pytest.mark.asyncio
async def test_list_knowledge(client: AsyncClient):
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    await client.post(
        "/api/knowledge",
        json={"name": f"List-{unique_id}", "description": "", "tags": []},
        headers=headers,
    )
    response = await client.get("/api/knowledge", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_knowledge(client: AsyncClient):
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    knowledge_id = f"get-{unique_id}"
    await client.post(
        "/api/knowledge",
        json={"name": knowledge_id, "description": "Get test", "tags": ["test"]},
        headers=headers,
    )
    response = await client.get(f"/api/knowledge/{knowledge_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == knowledge_id
    assert data["description"] == "Get test"


@pytest.mark.asyncio
async def test_update_knowledge(client: AsyncClient):
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    knowledge_id = f"upd-{unique_id}"
    await client.post(
        "/api/knowledge",
        json={"name": knowledge_id, "description": "Original", "tags": []},
        headers=headers,
    )
    response = await client.put(
        f"/api/knowledge/{knowledge_id}",
        json={"description": "Updated", "tags": ["updated"]},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated"


@pytest.mark.asyncio
async def test_delete_knowledge(client: AsyncClient):
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    knowledge_id = f"del-{unique_id}"
    await client.post(
        "/api/knowledge",
        json={"name": knowledge_id, "description": "", "tags": []},
        headers=headers,
    )
    response = await client.delete(f"/api/knowledge/{knowledge_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "删除成功"


@pytest.mark.asyncio
async def test_get_file_tree(client: AsyncClient):
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    knowledge_id = f"tree-{unique_id}"
    await client.post(
        "/api/knowledge",
        json={"name": knowledge_id, "description": "", "tags": []},
        headers=headers,
    )
    response = await client.get(f"/api/knowledge/{knowledge_id}/tree", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_file_operations(client: AsyncClient):
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    knowledge_id = f"file-{unique_id}"
    await client.post(
        "/api/knowledge",
        json={"name": knowledge_id, "description": "", "tags": []},
        headers=headers,
    )
    # Create directory
    response = await client.post(
        f"/api/knowledge/{knowledge_id}/directory",
        params={"dir_path": "docs"},
        headers=headers,
    )
    assert response.status_code == 200

    # Update file content (content is passed as query parameter)
    response = await client.put(
        f"/api/knowledge/{knowledge_id}/file/docs/test.md",
        params={"content": "# Test\nHello World"},
        headers=headers,
    )
    assert response.status_code == 200

    # Get file content
    response = await client.get(
        f"/api/knowledge/{knowledge_id}/file/docs/test.md",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "# Test" in data["content"]
