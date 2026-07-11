"""搜索模块单元测试"""
import json
import shutil
import uuid
from pathlib import Path

import pytest

from app.config import settings
from app.database import DATABASE_PATH
from app.knowledge.service import create_knowledge
from app.search.service import (
    _rebuild_search_index,
    _search_metadata,
    _search_with_grep,
    _update_search_index,
    rebuild_search_index,
    search_content,
    search_metadata,
    update_search_index,
)
from app.search.models import SearchResponse, SearchResult


def _force_rmtree(path: Path):
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


# ========== search_metadata 测试 ==========

class TestSearchMetadataSync:
    def test_search_existing(self):
        kb_id = f"search-meta-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "搜索测试库", "测试描述", ["search"], "tester")
            update_search_index(kb_id, "", "搜索测试库", ["search"], "测试描述", "")

            results = search_metadata("搜索测试")
            assert len(results) > 0
            assert results[0]["knowledge_id"] == kb_id
        finally:
            _force_rmtree(kb_path)

    def test_search_no_results(self):
        results = search_metadata("完全不存在的关键词xyz12345")
        assert results == []

    def test_search_limit(self):
        kb_id = f"search-limit-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "限制测试", "desc", [], "tester")
            update_search_index(kb_id, "", "限制测试", [], "desc", "")

            results = search_metadata("限制", limit=1)
            assert len(results) <= 1
        finally:
            _force_rmtree(kb_path)

    def test_search_db_error(self):
        # 测试数据库不存在的情况
        results = search_metadata("test", limit=10)
        assert isinstance(results, list)


# ========== update_search_index 测试 ==========

class TestUpdateSearchIndex:
    def test_update_index(self):
        kb_id = f"search-idx-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "索引测试", "desc", ["idx"], "tester")
            update_search_index(kb_id, "doc.md", "索引测试", ["idx"], "desc", "content")

            results = search_metadata("索引测试")
            assert len(results) > 0
        finally:
            _force_rmtree(kb_path)

    def test_update_index_overwrite(self):
        kb_id = f"search-over-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "覆盖测试", "desc", [], "tester")
            update_search_index(kb_id, "", "旧标题", [], "旧描述", "")
            update_search_index(kb_id, "", "新标题", [], "新描述", "")

            results = search_metadata("新标题")
            assert len(results) > 0
        finally:
            _force_rmtree(kb_path)


# ========== _search_with_grep 测试 ==========

class TestSearchWithGrep:
    def test_grep_finds_content(self):
        kb_id = f"search-grep-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "grep测试", "desc", [], "tester")
            (kb_path / "test.md").write_text("# Hello World\nThis is a test.", encoding="utf-8")

            results = _search_with_grep("Hello", kb_path, limit=10)
            assert len(results) > 0
            assert results[0]["file"] == "test.md"
            assert results[0]["line"] == 1
        finally:
            _force_rmtree(kb_path)

    def test_grep_no_results(self):
        kb_id = f"search-grep-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "grep测试", "desc", [], "tester")
            (kb_path / "test.md").write_text("hello world", encoding="utf-8")

            results = _search_with_grep("nonexistent_xyz", kb_path, limit=10)
            assert results == []
        finally:
            _force_rmtree(kb_path)

    def test_grep_limit(self):
        kb_id = f"search-grep-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "grep限制", "desc", [], "tester")
            (kb_path / "test.md").write_text("match\nmatch\nmatch\nmatch\nmatch", encoding="utf-8")

            results = _search_with_grep("match", kb_path, limit=2)
            assert len(results) == 2
        finally:
            _force_rmtree(kb_path)

    def test_grep_skips_git_dir(self):
        kb_id = f"search-grep-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "grep跳过", "desc", [], "tester")
            git_dir = kb_path / ".git" / "objects"
            git_dir.mkdir(parents=True)
            (git_dir / "test.txt").write_text("should be skipped", encoding="utf-8")

            results = _search_with_grep("skipped", kb_path, limit=10)
            assert results == []
        finally:
            _force_rmtree(kb_path)

    def test_grep_skips_binary_files(self):
        kb_id = f"search-grep-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "grep二进制", "desc", [], "tester")
            (kb_path / "image.png").write_bytes(b"\x89PNG\r\n")
            (kb_path / "readme.md").write_text("find me", encoding="utf-8")

            results = _search_with_grep("find", kb_path, limit=10)
            assert len(results) == 1
            assert results[0]["file"] == "readme.md"
        finally:
            _force_rmtree(kb_path)

    def test_grep_nonexistent_path(self):
        results = _search_with_grep("test", Path("/nonexistent/path"), limit=10)
        assert results == []

    def test_grep_multiple_files(self):
        kb_id = f"search-grep-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "grep多文件", "desc", [], "tester")
            (kb_path / "a.md").write_text("hello", encoding="utf-8")
            (kb_path / "b.md").write_text("hello", encoding="utf-8")

            results = _search_with_grep("hello", kb_path, limit=10)
            assert len(results) == 2
        finally:
            _force_rmtree(kb_path)


# ========== search_content 测试 ==========

class TestSearchContent:
    def test_search_content_basic(self):
        kb_id = f"search-ct-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "内容搜索", "desc", [], "tester")
            (kb_path / "doc.md").write_text("# Test Document\nContent here.", encoding="utf-8")

            results = search_content("Test Document", kb_id)
            assert isinstance(results, list)
        finally:
            _force_rmtree(kb_path)

    def test_search_content_no_path(self):
        results = search_content("test")
        assert isinstance(results, list)

    def test_search_content_nonexistent_path(self):
        results = search_content("test", knowledge_id="nonexistent-kb")
        assert results == []


# ========== rebuild_search_index 测试 ==========

class TestRebuildSearchIndex:
    def test_rebuild_empty(self):
        rebuild_search_index()
        assert True

    def test_rebuild_with_data(self):
        kb_id = f"search-rebuild-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "重建测试", "desc", ["rebuild"], "tester")
            rebuild_search_index()

            results = search_metadata("重建测试")
            assert len(results) > 0
        finally:
            _force_rmtree(kb_path)

    def test_rebuild_nonexistent_path(self):
        # 测试知识库路径不存在的情况
        original_path = settings.KNOWLEDGE_BASE_PATH
        settings.KNOWLEDGE_BASE_PATH = Path("/nonexistent/path")
        try:
            rebuild_search_index()
            assert True
        finally:
            settings.KNOWLEDGE_BASE_PATH = original_path


# ========== async search tests ==========

@pytest.mark.asyncio
async def test_async_search_metadata():
    kb_id = f"search-async-{uuid.uuid4().hex[:8]}"
    kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
    try:
        create_knowledge(kb_id, "异步搜索测试", "desc", ["async"], "tester")
        update_search_index(kb_id, "", "异步搜索测试", ["async"], "desc", "")

        results = await _search_metadata("异步搜索")
        assert len(results) > 0
    finally:
        _force_rmtree(kb_path)


@pytest.mark.asyncio
async def test_async_update_search_index():
    kb_id = f"search-async-{uuid.uuid4().hex[:8]}"
    kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
    try:
        create_knowledge(kb_id, "异步索引测试", "desc", [], "tester")
        await _update_search_index(kb_id, "", "异步索引测试", ["test"], "desc", "content")

        results = await _search_metadata("异步索引")
        assert len(results) > 0
    finally:
        _force_rmtree(kb_path)


@pytest.mark.asyncio
async def test_async_rebuild_search_index():
    kb_id = f"search-async-{uuid.uuid4().hex[:8]}"
    kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
    try:
        create_knowledge(kb_id, "异步重建测试", "desc", [], "tester")
        await _rebuild_search_index()

        results = await _search_metadata("异步重建")
        assert len(results) > 0
    finally:
        _force_rmtree(kb_path)


@pytest.mark.asyncio
async def test_async_rebuild_nonexistent_path():
    original_path = settings.KNOWLEDGE_BASE_PATH
    settings.KNOWLEDGE_BASE_PATH = Path("/nonexistent/path")
    try:
        await _rebuild_search_index()
        assert True
    finally:
        settings.KNOWLEDGE_BASE_PATH = original_path


# ========== search/models.py 测试 ==========

class TestSearchModels:
    def test_search_result_model(self):
        result = SearchResult(
            knowledge_id="kb1",
            file_path="test.md",
            title="Test",
            score=0.95,
            snippet="hello world",
        )
        assert result.knowledge_id == "kb1"
        assert result.score == 0.95

    def test_search_response_model(self):
        response = SearchResponse(
            results=[
                SearchResult(
                    knowledge_id="kb1",
                    file_path="a.md",
                    title="A",
                    score=1.0,
                    snippet="test",
                )
            ],
            total=1,
        )
        assert response.total == 1
        assert len(response.results) == 1


# ========== HTTP API 测试 ==========

async def get_auth_headers(client) -> dict:
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
async def test_search_metadata_api(client):
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    knowledge_id = f"search-{unique_id}"
    await client.post(
        "/api/knowledge",
        json={"name": knowledge_id, "description": "Test search", "tags": ["search"]},
        headers=headers,
    )
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
async def test_search_content_api(client):
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    knowledge_id = f"search-{unique_id}"
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
    response = await client.get(
        "/api/search",
        params={"q": "Hello", "mode": "content"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


@pytest.mark.asyncio
async def test_search_all_api(client):
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
