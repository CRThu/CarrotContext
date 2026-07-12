import shutil
import sqlite3
import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient

from app.config import settings
from app.database import DATABASE_PATH
from app.git.service import init_git
from app.knowledge.service import create_knowledge, remove_knowledge


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
        json={
            "name": knowledge_id,
            "description": "",
            "tags": [],
        },
        headers=headers,
    )
    # Create directory
    response = await client.post(
        f"/api/knowledge/{knowledge_id}/dirs",
        params={"dir_path": "docs"},
        headers=headers,
    )
    assert response.status_code == 200

    # Update file content (content is passed as request body)
    response = await client.put(
        f"/api/knowledge/{knowledge_id}/files/docs/test.md",
        content="# Test\nHello World",
        headers={**headers, "Content-Type": "text/plain"},
    )
    assert response.status_code == 200

    # Get file content
    response = await client.get(
        f"/api/knowledge/{knowledge_id}/files/docs/test.md",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "# Test" in data["content"]


# ========== 自动 Git 初始化测试 ==========


class TestAutoGitInit:
    def test_create_knowledge_auto_inits_git(self):
        kb_id = f"auto-git-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "Auto Git", "", [], "admin")
            assert (kb_path / ".git").exists()
        finally:
            if kb_path.exists():
                shutil.rmtree(kb_path, ignore_errors=True)

    def test_create_knowledge_has_git_dir(self):
        kb_id = f"auto-git2-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "Git Dir", "", [], "admin")
            git_dir = kb_path / ".git"
            assert git_dir.is_dir()
            assert (git_dir / "config").exists()
        finally:
            if kb_path.exists():
                shutil.rmtree(kb_path, ignore_errors=True)


# ========== KB 删除清理测试 ==========


class TestDeleteKnowledgeCleanup:
    def test_delete_cleans_access_rules(self):
        kb_id = f"del-clean-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(DATABASE_PATH))
            try:
                conn.execute(
                    "INSERT INTO access_rules (knowledge_id, group_id, access_level) VALUES (?, NULL, 'read')",
                    (kb_id,),
                )
                conn.commit()
            finally:
                conn.close()

            remove_knowledge(kb_id)

            conn = sqlite3.connect(str(DATABASE_PATH))
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM access_rules WHERE knowledge_id = ?", (kb_id,))
                assert cursor.fetchone()[0] == 0
            finally:
                conn.close()
        finally:
            if kb_path.exists():
                shutil.rmtree(kb_path, ignore_errors=True)

    def test_delete_cleans_search_index(self):
        kb_id = f"del-clean2-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(DATABASE_PATH))
            try:
                conn.execute(
                    "INSERT INTO search_index (knowledge_id, file_path, title, tags, summary, content) VALUES (?, '', ?, '', '', '')",
                    (kb_id, kb_id),
                )
                conn.commit()
            finally:
                conn.close()

            remove_knowledge(kb_id)

            conn = sqlite3.connect(str(DATABASE_PATH))
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM search_index WHERE knowledge_id = ?", (kb_id,))
                assert cursor.fetchone()[0] == 0
            finally:
                conn.close()
        finally:
            if kb_path.exists():
                shutil.rmtree(kb_path, ignore_errors=True)

    def test_delete_nonexistent_returns_false(self):
        result = remove_knowledge("nonexistent-del-xyz123")
        assert result is False
