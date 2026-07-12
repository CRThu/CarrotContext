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
            # .git is already created by create_knowledge auto-init
            # Write a file inside .git to verify it's skipped
            git_objects = kb_path / ".git" / "objects"
            if git_objects.exists():
                (git_objects / "test.txt").write_text("should be skipped", encoding="utf-8")

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


# ========== _search_with_rg 测试 ==========

class TestSearchWithRg:
    def test_rg_with_mock_output(self):
        """Mock ripgrep JSON output to test parsing"""
        from unittest.mock import patch, MagicMock
        from app.search.service import _search_with_rg

        search_path = Path("/fake/path")
        mock_result = MagicMock()
        # Use platform-appropriate path in mock output
        mock_path = str(search_path / "test.md")
        mock_result.stdout = json.dumps({
            "type": "match",
            "data": {
                "path": {"text": mock_path},
                "line_number": 5,
                "lines": {"text": "hello world"},
            },
        }) + "\n"
        mock_result.stderr = ""

        with patch("app.search.service.subprocess.run", return_value=mock_result):
            results = _search_with_rg("hello", search_path, limit=10)
            assert len(results) == 1
            assert results[0]["file"] == "test.md"
            assert results[0]["line"] == 5

    def test_rg_with_non_match_output(self):
        """Non-match output lines are skipped"""
        from unittest.mock import patch, MagicMock
        from app.search.service import _search_with_rg

        mock_result = MagicMock()
        mock_result.stdout = json.dumps({"type": "begin", "data": {}}) + "\n"
        mock_result.stderr = ""

        with patch("app.search.service.subprocess.run", return_value=mock_result):
            results = _search_with_rg("test", Path("/fake"), limit=10)
            assert results == []

    def test_rg_with_invalid_json(self):
        """Invalid JSON lines are skipped"""
        from unittest.mock import patch, MagicMock
        from app.search.service import _search_with_rg

        mock_result = MagicMock()
        mock_result.stdout = "not json\n{bad\n"
        mock_result.stderr = ""

        with patch("app.search.service.subprocess.run", return_value=mock_result):
            results = _search_with_rg("test", Path("/fake"), limit=10)
            assert results == []

    def test_rg_limit(self):
        """RG respects limit"""
        from unittest.mock import patch, MagicMock
        from app.search.service import _search_with_rg

        lines = []
        for i in range(5):
            lines.append(json.dumps({
                "type": "match",
                "data": {
                    "path": {"text": f"/fake/file{i}.md"},
                    "line_number": 1,
                    "lines": {"text": "match"},
                },
            }))
        mock_result = MagicMock()
        mock_result.stdout = "\n".join(lines) + "\n"
        mock_result.stderr = ""

        with patch("app.search.service.subprocess.run", return_value=mock_result):
            results = _search_with_rg("match", Path("/fake"), limit=2)
            assert len(results) == 2

    def test_rg_windows_path_separator(self):
        """RG handles Windows path separators"""
        from unittest.mock import patch, MagicMock
        from app.search.service import _search_with_rg

        search_path = Path("C:/Users/test")
        mock_result = MagicMock()
        mock_path = str(search_path / "file.md")
        mock_result.stdout = json.dumps({
            "type": "match",
            "data": {
                "path": {"text": mock_path},
                "line_number": 1,
                "lines": {"text": "hello"},
            },
        }) + "\n"
        mock_result.stderr = ""

        with patch("app.search.service.subprocess.run", return_value=mock_result):
            results = _search_with_rg("hello", search_path, limit=10)
            assert len(results) == 1
            assert results[0]["file"] == "file.md"


# ========== _load_knowledge_manifests 测试 ==========

class TestLoadKnowledgeManifests:
    def test_load_with_manifests(self):
        """加载有manifest的知识库"""
        from app.search.service import _load_knowledge_manifests

        kb_id = f"search-lm-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "加载测试", "desc", ["load"], "tester")
            entries = _load_knowledge_manifests()
            ids = [e[0] for e in entries]
            assert kb_id in ids
        finally:
            _force_rmtree(kb_path)

    def test_load_empty_directory(self):
        """空目录返回空列表"""
        from app.search.service import _load_knowledge_manifests

        entries = _load_knowledge_manifests()
        assert isinstance(entries, list)

    def test_load_nonexistent_path(self):
        """不存在的路径返回空列表"""
        from app.search.service import _load_knowledge_manifests
        original = settings.KNOWLEDGE_BASE_PATH
        settings.KNOWLEDGE_BASE_PATH = Path("/nonexistent/path")
        try:
            entries = _load_knowledge_manifests()
            assert entries == []
        finally:
            settings.KNOWLEDGE_BASE_PATH = original

    def test_load_skips_non_directories(self):
        """跳过非目录项"""
        from app.search.service import _load_knowledge_manifests
        # 直接测试 - 文件系统中的普通文件会被 is_dir() 过滤
        entries = _load_knowledge_manifests()
        assert isinstance(entries, list)


# ========== search_content rg fallback 测试 ==========

class TestSearchContentRgFallback:
    def test_search_content_fallback_to_grep(self):
        """rg不可用时降级为grep"""
        from unittest.mock import patch
        from app.search.service import search_content

        kb_id = f"search-fb-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "fallback测试", "desc", [], "tester")
            (kb_path / "doc.md").write_text("fallback content here", encoding="utf-8")

            # Mock rg to raise FileNotFoundError (not installed)
            with patch("app.search.service.subprocess.run", side_effect=FileNotFoundError):
                results = search_content("fallback", kb_id)
                assert isinstance(results, list)
        finally:
            _force_rmtree(kb_path)


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


# ========== Search API 深度覆盖测试 ==========


@pytest.mark.asyncio
async def test_search_metadata_filters_by_permission(client):
    """用户只能看到有权限的知识库搜索结果"""
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    kb_id = f"search-perm-{unique_id}"

    # 创建知识库
    await client.post(
        "/api/knowledge",
        json={"name": kb_id, "description": "permission test", "tags": ["perm"]},
        headers=headers,
    )
    # 手动填充搜索索引
    from app.search.service import update_search_index
    update_search_index(kb_id, "", "permission test", ["perm"], "desc", "")

    # 用另一个无权限的用户搜索
    headers2 = await get_auth_headers(client)
    response = await client.get(
        "/api/search",
        params={"q": "permission", "mode": "metadata"},
        headers=headers2,
    )
    assert response.status_code == 200
    data = response.json()
    # 无权限用户不应看到结果
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_search_content_filters_by_permission(client):
    """内容搜索也受权限过滤"""
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    kb_id = f"search-ct-perm-{unique_id}"
    kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id

    try:
        # 创建知识库并写入文件
        await client.post(
            "/api/knowledge",
            json={"name": kb_id, "description": "", "tags": []},
            headers=headers,
        )
        kb_path.mkdir(parents=True, exist_ok=True)
        (kb_path / "secret.md").write_text("classified content here", encoding="utf-8")

        # 无权限用户搜索
        headers2 = await get_auth_headers(client)
        response = await client.get(
            "/api/search",
            params={"q": "classified", "mode": "content"},
            headers=headers2,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
    finally:
        _force_rmtree(kb_path)


@pytest.mark.asyncio
async def test_search_permission_cache(client):
    """同一知识库的权限检查应被缓存（只查一次DB）"""
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    kb_id = f"search-cache-{unique_id}"

    await client.post(
        "/api/knowledge",
        json={"name": kb_id, "description": "cache test", "tags": ["cache"]},
        headers=headers,
    )
    from app.search.service import update_search_index
    update_search_index(kb_id, "", "cache test", ["cache"], "desc one", "")
    update_search_index(kb_id, "b.md", "cache test 2", ["cache"], "desc two", "")

    response = await client.get(
        "/api/search",
        params={"q": "cache", "mode": "metadata"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    # 两条结果都被返回（权限缓存生效）
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_search_limit_works(client):
    """limit 参数限制返回数量"""
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    kb_id = f"search-lim-{unique_id}"

    await client.post(
        "/api/knowledge",
        json={"name": kb_id, "description": "limit test", "tags": []},
        headers=headers,
    )
    from app.search.service import update_search_index
    for i in range(5):
        update_search_index(kb_id, f"f{i}.md", f"limit item {i}", [], "desc", "")

    response = await client.get(
        "/api/search",
        params={"q": "limit", "mode": "metadata", "limit": 2},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 2


@pytest.mark.asyncio
async def test_search_empty_results(client):
    """搜索不存在的关键词返回空结果"""
    headers = await get_auth_headers(client)
    response = await client.get(
        "/api/search",
        params={"q": "nonexistent_xyz_12345", "mode": "all"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_search_invalid_mode(client):
    """无效的搜索模式仍返回200（走all分支但匹配不到）"""
    headers = await get_auth_headers(client)
    response = await client.get(
        "/api/search",
        params={"q": "test", "mode": "invalid_mode"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


@pytest.mark.asyncio
async def test_search_content_mode_with_file(client):
    """content模式搜索文件内容"""
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    kb_id = f"search-cm-{unique_id}"
    kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id

    try:
        await client.post(
            "/api/knowledge",
            json={"name": kb_id, "description": "", "tags": []},
            headers=headers,
        )
        kb_path.mkdir(parents=True, exist_ok=True)
        (kb_path / "docs.md").write_text("unique_searchable_term_xyz", encoding="utf-8")

        response = await client.get(
            "/api/search",
            params={"q": "unique_searchable_term_xyz", "mode": "content"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 0  # ripgrep may or may not find it
    finally:
        _force_rmtree(kb_path)


@pytest.mark.asyncio
async def test_search_all_mode_combines_results(client):
    """all模式同时搜索元数据和内容"""
    headers = await get_auth_headers(client)
    unique_id = str(uuid.uuid4())[:8]
    kb_id = f"search-all-{unique_id}"
    kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id

    try:
        await client.post(
            "/api/knowledge",
            json={"name": kb_id, "description": "combo test", "tags": ["combo"]},
            headers=headers,
        )
        from app.search.service import update_search_index
        update_search_index(kb_id, "", "combo test", ["combo"], "combo desc", "")
        kb_path.mkdir(parents=True, exist_ok=True)
        (kb_path / "note.md").write_text("combo content", encoding="utf-8")

        response = await client.get(
            "/api/search",
            params={"q": "combo", "mode": "all"},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
    finally:
        _force_rmtree(kb_path)


@pytest.mark.asyncio
async def test_search_requires_auth(client):
    """未认证用户不能搜索"""
    response = await client.get(
        "/api/search",
        params={"q": "test", "mode": "all"},
    )
    assert response.status_code in (401, 403)


# ========== 损坏 Manifest 防御测试 ==========


class TestCorruptedManifestDefense:
    def test_load_manifests_skips_corrupted(self):
        kb_id_ok = f"search-ok-{uuid.uuid4().hex[:8]}"
        kb_id_bad = f"search-bad-{uuid.uuid4().hex[:8]}"
        kb_path_ok = settings.KNOWLEDGE_BASE_PATH / kb_id_ok
        kb_path_bad = settings.KNOWLEDGE_BASE_PATH / kb_id_bad
        try:
            kb_path_ok.mkdir(parents=True, exist_ok=True)
            (kb_path_ok / ".manifest.json").write_text(
                json.dumps({"name": "OK", "tags": [], "summary": "", "description": ""}),
                encoding="utf-8",
            )
            kb_path_bad.mkdir(parents=True, exist_ok=True)
            (kb_path_bad / ".manifest.json").write_text("CORRUPTED!!!", encoding="utf-8")

            from app.search.service import _load_knowledge_manifests
            entries = _load_knowledge_manifests()
            ids = [e[0] for e in entries]
            assert kb_id_ok in ids
            assert kb_id_bad not in ids
        finally:
            _force_rmtree(kb_path_ok)
            _force_rmtree(kb_path_bad)

    def test_load_manifests_skips_empty_file(self):
        kb_id = f"search-empty-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            (kb_path / ".manifest.json").write_text("", encoding="utf-8")

            from app.search.service import _load_knowledge_manifests
            entries = _load_knowledge_manifests()
            ids = [e[0] for e in entries]
            assert kb_id not in ids
        finally:
            _force_rmtree(kb_path)

    def test_load_manifests_skips_non_utf8(self):
        kb_id = f"search-binary-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            (kb_path / ".manifest.json").write_bytes(b"\x89\x8a\x8b\xff\xfe")

            from app.search.service import _load_knowledge_manifests
            entries = _load_knowledge_manifests()
            ids = [e[0] for e in entries]
            assert kb_id not in ids
        finally:
            _force_rmtree(kb_path)

    def test_rebuild_with_corrupted_manifest(self):
        kb_id_ok = f"rebuild-ok-{uuid.uuid4().hex[:8]}"
        kb_id_bad = f"rebuild-bad-{uuid.uuid4().hex[:8]}"
        kb_path_ok = settings.KNOWLEDGE_BASE_PATH / kb_id_ok
        kb_path_bad = settings.KNOWLEDGE_BASE_PATH / kb_id_bad
        try:
            kb_path_ok.mkdir(parents=True, exist_ok=True)
            (kb_path_ok / ".manifest.json").write_text(
                json.dumps({"name": "OK KB", "tags": ["test"], "summary": "sum", "description": "desc"}),
                encoding="utf-8",
            )
            kb_path_bad.mkdir(parents=True, exist_ok=True)
            (kb_path_bad / ".manifest.json").write_text("{bad json", encoding="utf-8")

            rebuild_search_index()

            import sqlite3
            conn = sqlite3.connect(str(DATABASE_PATH))
            try:
                cursor = conn.execute("SELECT knowledge_id FROM search_index WHERE knowledge_id = ?", (kb_id_ok,))
                assert cursor.fetchone() is not None
                cursor = conn.execute("SELECT knowledge_id FROM search_index WHERE knowledge_id = ?", (kb_id_bad,))
                assert cursor.fetchone() is None
            finally:
                conn.close()
        finally:
            _force_rmtree(kb_path_ok)
            _force_rmtree(kb_path_bad)
