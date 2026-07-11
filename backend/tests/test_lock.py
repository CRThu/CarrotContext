"""文件锁定模块测试"""
import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.config import settings
from app.lock.service import (
    acquire_lock,
    get_lock_path,
    get_lock_status,
    release_lock,
)


def _cleanup_locks(kb_id: str):
    """清理测试锁文件"""
    lock_dir = settings.KNOWLEDGE_BASE_PATH / kb_id / ".locks"
    if lock_dir.exists():
        import shutil
        shutil.rmtree(lock_dir, ignore_errors=True)


# ========== get_lock_path 测试 ==========

class TestGetLockPath:
    def test_basic_path(self):
        path = get_lock_path("kb1", "test.md")
        assert path.name == "test.md.lock"
        assert ".locks" in str(path)

    def test_nested_path(self):
        path = get_lock_path("kb1", "sub/dir/file.md")
        # 安全化：/ 和 \ 都替换为 _
        assert path.name == "sub_dir_file.md.lock"

    def test_windows_path(self):
        path = get_lock_path("kb1", "sub\\dir\\file.md")
        assert path.name == "sub_dir_file.md.lock"


# ========== acquire_lock 测试 ==========

class TestAcquireLock:
    def test_acquire_success(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            result = acquire_lock(kb_id, "test.md", "alice")
            assert result["success"] is True
            assert result["locked_by"] == "alice"
            assert "locked_at" in result
        finally:
            _cleanup_locks(kb_id)

    def test_acquire_already_locked(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            acquire_lock(kb_id, "test.md", "alice")
            result = acquire_lock(kb_id, "test.md", "bob")
            assert result["success"] is False
            assert result["locked_by"] == "alice"
        finally:
            _cleanup_locks(kb_id)

    def test_acquire_after_timeout(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            lock_path = get_lock_path(kb_id, "test.md")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            # 写入过期的锁
            expired_time = (datetime.now(UTC) - timedelta(minutes=settings.LOCK_TIMEOUT_MINUTES + 1)).isoformat()
            lock_data = {
                "username": "alice",
                "file_path": "test.md",
                "locked_at": expired_time,
            }
            lock_path.write_text(json.dumps(lock_data), encoding="utf-8")

            result = acquire_lock(kb_id, "test.md", "bob")
            assert result["success"] is True
            assert result["locked_by"] == "bob"
        finally:
            _cleanup_locks(kb_id)

    def test_acquire_corrupted_lock_file(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            lock_path = get_lock_path(kb_id, "test.md")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text("not json", encoding="utf-8")

            result = acquire_lock(kb_id, "test.md", "alice")
            assert result["success"] is True
        finally:
            _cleanup_locks(kb_id)

    def test_acquire_lock_missing_key(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            lock_path = get_lock_path(kb_id, "test.md")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text(json.dumps({"username": "alice"}), encoding="utf-8")

            result = acquire_lock(kb_id, "test.md", "bob")
            assert result["success"] is True
        finally:
            _cleanup_locks(kb_id)

    def test_acquire_different_files(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            r1 = acquire_lock(kb_id, "a.md", "alice")
            r2 = acquire_lock(kb_id, "b.md", "alice")
            assert r1["success"] is True
            assert r2["success"] is True
        finally:
            _cleanup_locks(kb_id)


# ========== release_lock 测试 ==========

class TestReleaseLock:
    def test_release_success(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            acquire_lock(kb_id, "test.md", "alice")
            result = release_lock(kb_id, "test.md", "alice")
            assert result is True
        finally:
            _cleanup_locks(kb_id)

    def test_release_not_exists(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            result = release_lock(kb_id, "nonexistent.md", "alice")
            assert result is False
        finally:
            _cleanup_locks(kb_id)

    def test_release_wrong_user(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            acquire_lock(kb_id, "test.md", "alice")
            result = release_lock(kb_id, "test.md", "bob")
            assert result is False
            # 确认锁仍然存在
            status = get_lock_status(kb_id, "test.md")
            assert status is not None
        finally:
            _cleanup_locks(kb_id)

    def test_release_corrupted_file(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            lock_path = get_lock_path(kb_id, "test.md")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text("invalid json", encoding="utf-8")

            result = release_lock(kb_id, "test.md", "alice")
            # 锁文件损坏时，跳过用户验证，直接删除
            assert result is True
        finally:
            _cleanup_locks(kb_id)

    def test_release_missing_username_key(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            lock_path = get_lock_path(kb_id, "test.md")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text(json.dumps({"file_path": "test.md"}), encoding="utf-8")

            result = release_lock(kb_id, "test.md", "alice")
            # 缺少username字段时，get("username")返回None，不匹配请求者，拒绝释放
            assert result is False
        finally:
            _cleanup_locks(kb_id)


# ========== get_lock_status 测试 ==========

class TestGetLockStatus:
    def test_status_no_lock(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            result = get_lock_status(kb_id, "test.md")
            assert result is None
        finally:
            _cleanup_locks(kb_id)

    def test_status_locked(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            acquire_lock(kb_id, "test.md", "alice")
            result = get_lock_status(kb_id, "test.md")
            assert result is not None
            assert result["username"] == "alice"
        finally:
            _cleanup_locks(kb_id)

    def test_status_expired_lock(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            lock_path = get_lock_path(kb_id, "test.md")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            expired_time = (datetime.now(UTC) - timedelta(minutes=settings.LOCK_TIMEOUT_MINUTES + 1)).isoformat()
            lock_data = {
                "username": "alice",
                "file_path": "test.md",
                "locked_at": expired_time,
            }
            lock_path.write_text(json.dumps(lock_data), encoding="utf-8")

            result = get_lock_status(kb_id, "test.md")
            assert result is None
            assert not lock_path.exists()
        finally:
            _cleanup_locks(kb_id)

    def test_status_corrupted_file(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            lock_path = get_lock_path(kb_id, "test.md")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text("bad json", encoding="utf-8")

            result = get_lock_status(kb_id, "test.md")
            assert result is None
        finally:
            _cleanup_locks(kb_id)

    def test_status_missing_key(self):
        kb_id = f"lock-test-{uuid.uuid4().hex[:8]}"
        try:
            lock_path = get_lock_path(kb_id, "test.md")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text(json.dumps({"username": "alice"}), encoding="utf-8")

            result = get_lock_status(kb_id, "test.md")
            assert result is None
        finally:
            _cleanup_locks(kb_id)


# ========== HTTP API 测试 ==========

async def get_auth_headers(client) -> dict:
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
async def test_acquire_lock_api(client):
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
async def test_lock_status_api(client):
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
async def test_release_lock_api(client):
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
