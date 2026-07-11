import uuid

import pytest
from httpx import AsyncClient


async def get_auth_headers(client: AsyncClient) -> dict:
    unique_id = str(uuid.uuid4())[:8]
    username = f"git_{unique_id}"
    await client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{unique_id}@test.com",
            "password": "pass123",
        },
    )
    resp = await client.post(
        "/api/auth/login",
        json={"username": username, "password": "pass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, f"git-{unique_id}"


@pytest.mark.asyncio
async def test_init_git(client: AsyncClient):
    headers, knowledge_id = await get_auth_headers(client)
    await client.post(
        "/api/knowledge",
        json={
            "name": knowledge_id,
            "description": "",
            "tags": [],
        },
        headers=headers,
    )
    response = await client.post(
        f"/api/git/{knowledge_id}/init",
        headers=headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_git_log(client: AsyncClient):
    headers, knowledge_id = await get_auth_headers(client)
    await client.post(
        "/api/knowledge",
        json={
            "name": knowledge_id,
            "description": "",
            "tags": [],
        },
        headers=headers,
    )
    await client.post(
        f"/api/git/{knowledge_id}/init",
        headers=headers,
    )
    response = await client.get(
        f"/api/git/{knowledge_id}/log",
        headers=headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_diff(client: AsyncClient):
    headers, knowledge_id = await get_auth_headers(client)
    await client.post(
        "/api/knowledge",
        json={
            "name": knowledge_id,
            "description": "",
            "tags": [],
        },
        headers=headers,
    )
    response = await client.get(
        f"/api/git/{knowledge_id}/diff",
        headers=headers,
    )
    assert response.status_code == 200
    assert "diff" in response.json()


@pytest.mark.asyncio
async def test_create_commit(client: AsyncClient):
    headers, knowledge_id = await get_auth_headers(client)
    await client.post(
        "/api/knowledge",
        json={
            "name": knowledge_id,
            "description": "",
            "tags": [],
        },
        headers=headers,
    )
    await client.post(
        f"/api/git/{knowledge_id}/init",
        headers=headers,
    )
    # Create a file first (content is passed as request body)
    await client.put(
        f"/api/knowledge/{knowledge_id}/file/test.md",
        content="# Test",
        headers={**headers, "Content-Type": "text/plain"},
    )
    # Commit
    response = await client.post(
        f"/api/git/{knowledge_id}/commit",
        json={
            "message": "Initial commit",
            "file_path": "test.md",
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "hash" in data
    assert data["message"] == "Initial commit"


@pytest.mark.asyncio
async def test_revert_commit(client: AsyncClient):
    headers, knowledge_id = await get_auth_headers(client)
    await client.post(
        "/api/knowledge",
        json={
            "name": knowledge_id,
            "description": "",
            "tags": [],
        },
        headers=headers,
    )
    await client.post(
        f"/api/git/{knowledge_id}/init",
        headers=headers,
    )
    # Create and commit a file
    await client.put(
        f"/api/knowledge/{knowledge_id}/file/test.md",
        content="# Test",
        headers={**headers, "Content-Type": "text/plain"},
    )
    commit_resp = await client.post(
        f"/api/git/{knowledge_id}/commit",
        json={
            "message": "Add test",
            "file_path": "test.md",
        },
        headers=headers,
    )
    commit_hash = commit_resp.json()["hash"]
    # Revert
    response = await client.post(
        f"/api/git/{knowledge_id}/revert",
        json={"commit_hash": commit_hash},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "回滚成功"
