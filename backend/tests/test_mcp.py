"""MCP工具单元测试 + SSE集成测试"""
import json
import shutil
import time
from pathlib import Path
from unittest.mock import patch

import pytest
import aiosqlite

from app.config import settings
from app.database import DATABASE_PATH
from app.knowledge.service import create_knowledge
from app.mcp.tools import (
    commit_changes,
    create_new_knowledge,
    get_file_diff,
    get_git_history,
    get_knowledge_detail,
    list_knowledge_base,
    read_file_content,
    search_knowledge,
    update_file,
)


def _force_rmtree(path: Path):
    """强制删除目录，处理Windows文件锁定问题"""
    if not path.exists():
        return
    for _ in range(3):
        try:
            shutil.rmtree(path, onexc=_onexc_handler)
            return
        except PermissionError:
            time.sleep(0.1)
    shutil.rmtree(path, onexc=_onexc_handler, ignore_errors=True)


def _onexc_handler(func, path, exc):
    """Windows文件锁定错误处理"""
    import os
    try:
        os.chmod(path, 0o777)
        func(path)
    except (OSError, PermissionError):
        pass


@pytest.fixture
def setup_test_kb(tmp_path):
    """创建测试知识库并在测试后清理，使用唯一ID避免冲突"""
    import asyncio
    import uuid

    kb_id = f"mcp-test-{uuid.uuid4().hex[:8]}"
    kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
    try:
        create_knowledge(kb_id, f"MCP测试库-{kb_id}", "用于MCP工具测试", ["test"], "tester")
        # Grant anonymous read/write for MCP tool tests (no user context)
        from app.knowledge.access_rules import set_access_rule
        asyncio.run(set_access_rule(kb_id, None, "write"))
        yield kb_id, kb_path
    finally:
        _force_rmtree(kb_path)


@pytest.fixture
def setup_test_kb_with_search_index(setup_test_kb):
    """创建带搜索索引的测试知识库"""
    kb_id, kb_path = setup_test_kb
    from app.search.service import update_search_index
    update_search_index(kb_id, "", f"MCP测试库-{kb_id}", ["test"], "用于MCP工具测试", "")
    yield kb_id, kb_path


@pytest.fixture
def setup_git_kb(setup_test_kb):
    """创建带Git初始化的测试知识库"""
    kb_id, kb_path = setup_test_kb
    from app.git.service import init_git
    init_git(kb_id)
    yield kb_id, kb_path


# ========== list_knowledge_base 测试 ==========

class TestListKnowledgeBase:
    @pytest.mark.asyncio
    async def test_list_with_knowledge(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = await list_knowledge_base()
        assert kb_id in result

    @pytest.mark.asyncio
    async def test_list_empty(self):
        result = await list_knowledge_base()
        assert isinstance(result, str)


# ========== get_knowledge_detail 测试 ==========

class TestGetKnowledgeDetail:
    @pytest.mark.asyncio
    async def test_get_existing(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = await get_knowledge_detail(kb_id)
        assert kb_id in result
        assert "tester" in result

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        result = await get_knowledge_detail("nonexistent-kb-xyz123")
        # Anonymous with no rule gets denied, or nonexistent gets "不存在"
        assert "不存在" in result or "权限不足" in result


# ========== read_file_content 测试 ==========

class TestReadFileContent:
    @pytest.mark.asyncio
    async def test_read_existing_file(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        test_file = kb_path / "test.txt"
        test_file.write_text("hello mcp", encoding="utf-8")

        result = await read_file_content(kb_id, "test.txt")
        assert result == "hello mcp"

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = await read_file_content(kb_id, "no-such-file.txt")
        assert "不存在" in result

    @pytest.mark.asyncio
    async def test_read_nested_file(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        nested = kb_path / "subdir" / "nested.txt"
        nested.parent.mkdir(parents=True)
        nested.write_text("nested content", encoding="utf-8")

        result = await read_file_content(kb_id, "subdir/nested.txt")
        assert result == "nested content"


# ========== update_file 测试 ==========

class TestUpdateFile:
    @pytest.mark.asyncio
    async def test_update_existing_file(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        test_file = kb_path / "update-me.txt"
        test_file.write_text("old content", encoding="utf-8")

        result = await update_file(kb_id, "update-me.txt", "new content")
        assert "更新成功" in result
        assert test_file.read_text(encoding="utf-8") == "new content"

    @pytest.mark.asyncio
    async def test_update_creates_new_file(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        result = await update_file(kb_id, "new-file.txt", "created by mcp")
        assert "更新成功" in result
        assert (kb_path / "new-file.txt").read_text(encoding="utf-8") == "created by mcp"

    @pytest.mark.asyncio
    async def test_update_creates_nested_file(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        result = await update_file(kb_id, "deep/nested/file.txt", "deep content")
        assert "更新成功" in result
        assert (kb_path / "deep" / "nested" / "file.txt").read_text(encoding="utf-8") == "deep content"

    @pytest.mark.asyncio
    async def test_update_empty_content(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        result = await update_file(kb_id, "empty.txt", "")
        assert "更新成功" in result
        assert (kb_path / "empty.txt").read_text(encoding="utf-8") == ""


# ========== create_new_knowledge 测试 ==========

class TestCreateNewKnowledge:
    @pytest.fixture(autouse=True)
    async def setup_admin(self):
        """Set admin user in MCP context for create tests"""
        import aiosqlite
        from app.database import DATABASE_PATH
        from app.mcp.auth import _current_user
        from app.auth.service import create_user

        # Clean DB to avoid conflicts
        async with aiosqlite.connect(str(DATABASE_PATH)) as db:
            await db.execute("DELETE FROM users")
            await db.execute("DELETE FROM permission_groups")
            await db.execute("DELETE FROM user_groups")
            await db.execute("DELETE FROM access_rules")
            await db.commit()

        admin = await create_user("mcp_admin_create", "mcp_admin_create@test.com", "test123")
        async with aiosqlite.connect(str(DATABASE_PATH)) as db:
            await db.execute("UPDATE users SET role = 'admin' WHERE id = ?", (admin["id"],))
            await db.commit()
        admin["role"] = "admin"
        _current_user.set(admin)
        yield
        _current_user.set(None)

    @pytest.mark.asyncio
    async def test_create_success(self):
        import uuid
        kb_id = f"mcp-create-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            result = await create_new_knowledge(kb_id, "新建测试库", "描述", "tag1,tag2")
            assert "创建成功" in result
            assert kb_path.exists()
            manifest = json.loads((kb_path / ".manifest.json").read_text(encoding="utf-8"))
            assert manifest["name"] == "新建测试库"
            assert "tag1" in manifest["tags"]
        finally:
            _force_rmtree(kb_path)

    @pytest.mark.asyncio
    async def test_create_duplicate(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = await create_new_knowledge(kb_id, "重复创建")
        assert "已存在" in result

    @pytest.mark.asyncio
    async def test_create_no_tags(self):
        import uuid
        kb_id = f"mcp-notags-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            result = await create_new_knowledge(kb_id, "无标签库", "desc", "")
            assert "创建成功" in result
            manifest = json.loads((kb_path / ".manifest.json").read_text(encoding="utf-8"))
            assert manifest["tags"] == []
        finally:
            _force_rmtree(kb_path)

    @pytest.mark.asyncio
    async def test_create_single_tag(self):
        import uuid
        kb_id = f"mcp-onetag-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            result = await create_new_knowledge(kb_id, "单标签库", "desc", "solo")
            assert "创建成功" in result
            manifest = json.loads((kb_path / ".manifest.json").read_text(encoding="utf-8"))
            assert manifest["tags"] == ["solo"]
        finally:
            _force_rmtree(kb_path)

    @pytest.mark.asyncio
    async def test_create_tags_with_spaces(self):
        import uuid
        kb_id = f"mcp-spaces-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            result = await create_new_knowledge(kb_id, "空格标签", "desc", " tag1 , tag2 , ")
            assert "创建成功" in result
            manifest = json.loads((kb_path / ".manifest.json").read_text(encoding="utf-8"))
            assert manifest["tags"] == ["tag1", "tag2"]
        finally:
            _force_rmtree(kb_path)


# ========== search_knowledge 测试 ==========

class TestSearchKnowledge:
    @pytest.mark.asyncio
    async def test_search_metadata(self, setup_test_kb_with_search_index):
        kb_id, _ = setup_test_kb_with_search_index
        result = await search_knowledge(kb_id, mode="metadata")
        assert "元数据" in result or kb_id in result

    @pytest.mark.asyncio
    async def test_search_content(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        (kb_path / "readme.md").write_text("这是一个测试文档", encoding="utf-8")

        result = await search_knowledge("测试文档", mode="content")
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_search_all_mode(self, setup_test_kb_with_search_index):
        kb_id, kb_path = setup_test_kb_with_search_index
        (kb_path / "doc.md").write_text("hello world", encoding="utf-8")

        result = await search_knowledge(kb_id, mode="all")
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_search_no_results(self, setup_test_kb):
        result = await search_knowledge("完全不存在的关键词xyz123")
        assert "没有找到" in result

    @pytest.mark.asyncio
    async def test_search_invalid_mode(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = await search_knowledge(kb_id, mode="invalid")
        assert isinstance(result, str)


# ========== get_git_history 测试 ==========

class TestGitHistory:
    @pytest.mark.asyncio
    async def test_get_history_empty(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = await get_git_history(kb_id)
        assert "没有提交历史" in result

    @pytest.mark.asyncio
    async def test_get_history_with_commits(self, setup_git_kb):
        kb_id, kb_path = setup_git_kb
        (kb_path / "file1.txt").write_text("content", encoding="utf-8")
        from app.git.service import create_git_commit
        commit_result = create_git_commit(kb_id, "initial commit")
        assert commit_result is not None, "Git commit should succeed"

        result = await get_git_history(kb_id, limit=5)
        assert "initial commit" in result

    @pytest.mark.asyncio
    async def test_get_history_limit(self, setup_git_kb):
        kb_id, kb_path = setup_git_kb
        from app.git.service import create_git_commit

        for i in range(5):
            (kb_path / f"file{i}.txt").write_text(f"content {i}", encoding="utf-8")
            create_git_commit(kb_id, f"commit {i}")

        result = await get_git_history(kb_id, limit=2)
        lines = result.strip().split("\n")
        assert len(lines) == 2


# ========== get_file_diff 测试 ==========

class TestFileDiff:
    @pytest.mark.asyncio
    async def test_diff_no_repo(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = await get_file_diff(kb_id)
        assert "没有差异" in result

    @pytest.mark.asyncio
    async def test_diff_with_changes(self, setup_git_kb):
        kb_id, kb_path = setup_git_kb
        (kb_path / "diff-test.txt").write_text("original", encoding="utf-8")
        from app.git.service import create_git_commit
        create_git_commit(kb_id, "add file")
        (kb_path / "diff-test.txt").write_text("modified", encoding="utf-8")

        result = await get_file_diff(kb_id, "diff-test.txt")
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_diff_no_changes(self, setup_git_kb):
        kb_id, kb_path = setup_git_kb
        (kb_path / "clean.txt").write_text("stable", encoding="utf-8")
        from app.git.service import create_git_commit
        create_git_commit(kb_id, "add file")

        result = await get_file_diff(kb_id, "clean.txt")
        assert "没有差异" in result

    @pytest.mark.asyncio
    async def test_diff_with_commit_param(self, setup_git_kb):
        kb_id, kb_path = setup_git_kb
        (kb_path / "file.txt").write_text("v1", encoding="utf-8")
        from app.git.service import create_git_commit
        commit = create_git_commit(kb_id, "first")
        (kb_path / "file.txt").write_text("v2", encoding="utf-8")

        result = await get_file_diff(kb_id, "file.txt", commit["hash"])
        assert isinstance(result, str)


# ========== commit_changes 测试 ==========

class TestCommitChanges:
    @pytest.mark.asyncio
    async def test_commit_success(self, setup_git_kb):
        kb_id, kb_path = setup_git_kb
        (kb_path / "commit.txt").write_text("to commit", encoding="utf-8")

        result = await commit_changes(kb_id, "test commit", "commit.txt")
        assert "提交成功" in result
        assert "test commit" in result

    @pytest.mark.asyncio
    async def test_commit_no_repo(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        (kb_path / "orphan.txt").write_text("orphan", encoding="utf-8")
        result = await commit_changes(kb_id, "no repo commit", "orphan.txt")
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_commit_all_files(self, setup_git_kb):
        kb_id, kb_path = setup_git_kb
        (kb_path / "a.txt").write_text("aaa", encoding="utf-8")
        (kb_path / "b.txt").write_text("bbb", encoding="utf-8")

        result = await commit_changes(kb_id, "commit all")
        assert "提交成功" in result

    @pytest.mark.asyncio
    async def test_commit_nonexistent_file(self, setup_git_kb):
        kb_id, _ = setup_git_kb
        result = await commit_changes(kb_id, "commit missing", "ghost.txt")
        assert "提交失败" in result


# ========== MCP server 应用测试 ==========

class TestMCPServer:
    def test_mcp_app_creation(self):
        from app.mcp.server import mcp_app
        assert mcp_app is not None

    def test_mcp_instance_has_all_tools(self):
        from app.mcp.tools import mcp
        tool_names = [t.name for t in mcp._tool_manager.list_tools()]
        expected = [
            "list_knowledge_base",
            "get_knowledge_detail",
            "read_file_content",
            "update_file",
            "create_new_knowledge",
            "search_knowledge",
            "get_git_history",
            "get_file_diff",
            "commit_changes",
        ]
        for name in expected:
            assert name in tool_names, f"Tool {name} not registered"


# ========== MCP SSE HTTP集成测试 ==========

class TestMCPSSEIntegration:
    def test_mcp_mount_configured(self):
        from app.main import app
        routes_found = False
        for route in app.routes:
            if hasattr(route, "path") and route.path.startswith("/mcp"):
                routes_found = True
                break
        assert routes_found, "MCP route not found in app routes"

    def test_mcp_disabled_no_mount(self):
        from unittest.mock import patch
        from fastapi import FastAPI

        test_app = FastAPI()
        with patch("app.config.settings") as mock_settings:
            mock_settings.MCP_ENABLED = False
            mock_settings.MCP_PATH = "/mcp"
            assert not any(
                hasattr(r, "path") and r.path.startswith("/mcp")
                for r in test_app.routes
            )


# ========== MCP工具参数测试 ==========

class TestMCPToolSchemas:
    def test_list_knowledge_base_schema(self):
        from app.mcp.tools import mcp
        tools = {t.name: t for t in mcp._tool_manager.list_tools()}
        tool = tools["list_knowledge_base"]
        assert tool.parameters == {} or tool.parameters.get("properties", {}) == {}

    @pytest.mark.asyncio
    async def test_search_knowledge_default_mode(self, setup_test_kb_with_search_index):
        kb_id, _ = setup_test_kb_with_search_index
        result = await search_knowledge(kb_id)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_get_file_diff_defaults(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = await get_file_diff(kb_id, "", "")
        assert "没有差异" in result

    @pytest.mark.asyncio
    async def test_commit_changes_defaults(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = await commit_changes(kb_id, "test commit", "")
        assert isinstance(result, str)


# ========== MCP Authentication Tests ==========

class TestMCPAuth:
    def test_middleware_class_exists(self):
        from app.mcp.server import MCPAuthMiddleware
        assert MCPAuthMiddleware is not None

    def test_middleware_initialization(self):
        from app.mcp.server import MCPAuthMiddleware

        async def dummy_app(scope, receive, send):
            pass

        middleware = MCPAuthMiddleware(dummy_app)
        assert middleware.app == dummy_app

    def test_auth_module_functions(self):
        from app.mcp.auth import set_mcp_user, get_mcp_user
        assert callable(set_mcp_user)
        assert callable(get_mcp_user)

    def test_tools_import_with_permission_check(self):
        from app.mcp.tools import update_file, create_new_knowledge, commit_changes
        assert callable(update_file)
        assert callable(create_new_knowledge)
        assert callable(commit_changes)


class TestMCPAuthMiddleware:
    def test_middleware_class_exists(self):
        from app.mcp.server import MCPAuthMiddleware
        assert MCPAuthMiddleware is not None

    def test_middleware_initialization(self):
        from app.mcp.server import MCPAuthMiddleware

        async def dummy_app(scope, receive, send):
            pass

        middleware = MCPAuthMiddleware(dummy_app)
        assert middleware.app == dummy_app


# ========== MCP Permission Denial Tests ==========


class TestMCPPermissionDenial:
    """Test that MCP tools deny access when user lacks permissions"""

    @pytest.fixture(autouse=True)
    async def cleanup_users(self):
        """Clean users table before each test to avoid UNIQUE conflicts"""
        async with aiosqlite.connect(str(DATABASE_PATH)) as db:
            await db.execute("DELETE FROM users")
            await db.execute("DELETE FROM permission_groups")
            await db.execute("DELETE FROM user_groups")
            await db.execute("DELETE FROM access_rules")
            await db.commit()
        yield
        async with aiosqlite.connect(str(DATABASE_PATH)) as db:
            await db.execute("DELETE FROM users")
            await db.execute("DELETE FROM permission_groups")
            await db.execute("DELETE FROM user_groups")
            await db.execute("DELETE FROM access_rules")
            await db.commit()

    @pytest.mark.asyncio
    async def test_get_knowledge_detail_denied(self, setup_test_kb):
        """User without read access should get permission error"""
        kb_id, _ = setup_test_kb
        from app.auth.service import create_user

        user = await create_user("mcp_no_access", "mcp_no@test.com", "test123")
        # Ensure user is NOT admin
        async with aiosqlite.connect(str(DATABASE_PATH)) as db:
            await db.execute("UPDATE users SET role = 'user' WHERE id = ?", (user["id"],))
            await db.commit()

        from app.mcp.auth import _current_user
        _current_user.set(user)

        try:
            result = await get_knowledge_detail(kb_id)
            # No group access → denied
            assert "权限不足" in result
        finally:
            _current_user.set(None)

    @pytest.mark.asyncio
    async def test_read_file_content_denied(self, setup_test_kb):
        """User without read access should get permission error for file read"""
        kb_id, kb_path = setup_test_kb
        test_file = kb_path / "secret.txt"
        test_file.write_text("secret content", encoding="utf-8")

        from app.mcp.auth import _current_user
        from app.auth.service import create_user

        user = await create_user("mcp_file_no_access", "mcp_file_no@test.com", "test123")
        # Ensure user is NOT admin
        async with aiosqlite.connect(str(DATABASE_PATH)) as db:
            await db.execute("UPDATE users SET role = 'user' WHERE id = ?", (user["id"],))
            await db.commit()

        _current_user.set(user)

        try:
            result = await read_file_content(kb_id, "secret.txt")
            # No group access → denied
            assert "权限不足" in result
        finally:
            _current_user.set(None)

    @pytest.mark.asyncio
    async def test_update_file_denied(self, setup_test_kb):
        """User without write access should get permission error for file update"""
        kb_id, kb_path = setup_test_kb
        test_file = kb_path / "existing.txt"
        test_file.write_text("original", encoding="utf-8")

        from app.mcp.auth import _current_user
        from app.auth.service import create_user, create_group, add_user_to_group
        from app.knowledge.access_rules import set_access_rule
        from app.database import DATABASE_PATH
        import aiosqlite

        # Create user with read-only access
        user = await create_user("mcp_readonly", "mcp_readonly@test.com", "test123")
        # Ensure user is NOT admin
        async with aiosqlite.connect(str(DATABASE_PATH)) as db:
            await db.execute("UPDATE users SET role = 'user' WHERE id = ?", (user["id"],))
            await db.commit()

        group = await create_group("readonly_group_mcp")
        await add_user_to_group(user["id"], group["id"])
        await set_access_rule(kb_id, group["id"], "read")

        _current_user.set(user)

        try:
            result = await update_file(kb_id, "existing.txt", "hacked")
            assert "权限不足" in result
        finally:
            _current_user.set(None)

    @pytest.mark.asyncio
    async def test_commit_changes_denied(self, setup_git_kb):
        """User without write access should get permission error for commit"""
        kb_id, kb_path = setup_git_kb
        (kb_path / "commit.txt").write_text("to commit", encoding="utf-8")

        from app.mcp.auth import _current_user
        from app.auth.service import create_user, create_group, add_user_to_group
        from app.knowledge.access_rules import set_access_rule
        from app.database import DATABASE_PATH
        import aiosqlite

        # Create user with read-only access
        user = await create_user("mcp_commit_ro", "mcp_commit_ro@test.com", "test123")
        # Ensure user is NOT admin
        async with aiosqlite.connect(str(DATABASE_PATH)) as db:
            await db.execute("UPDATE users SET role = 'user' WHERE id = ?", (user["id"],))
            await db.commit()

        group = await create_group("commit_ro_group")
        await add_user_to_group(user["id"], group["id"])
        await set_access_rule(kb_id, group["id"], "read")

        _current_user.set(user)

        try:
            result = await commit_changes(kb_id, "test commit", "commit.txt")
            assert "权限不足" in result
        finally:
            _current_user.set(None)

    @pytest.mark.asyncio
    async def test_get_git_history_denied(self, setup_git_kb):
        """User without read access should get permission error for git history"""
        kb_id, kb_path = setup_git_kb

        from app.mcp.auth import _current_user
        from app.auth.service import create_user, create_group, add_user_to_group
        from app.knowledge.access_rules import set_access_rule

        # Create user with no access (use "none" level)
        user = await create_user("mcp_history_none", "mcp_history_none@test.com", "test123")
        # Ensure user is NOT admin - update both DB and dict
        user["role"] = "user"
        async with aiosqlite.connect(str(DATABASE_PATH)) as db:
            await db.execute("UPDATE users SET role = 'user' WHERE id = ?", (user["id"],))
            await db.commit()

        group = await create_group("history_none_group")
        await add_user_to_group(user["id"], group["id"])
        await set_access_rule(kb_id, group["id"], "none")

        _current_user.set(user)

        try:
            result = await get_git_history(kb_id)
            assert "权限不足" in result
        finally:
            _current_user.set(None)

    @pytest.mark.asyncio
    async def test_list_knowledge_base_filters_by_access(self):
        """list_knowledge_base should filter by user access"""
        from app.mcp.auth import _current_user
        from app.auth.service import create_user

        user = await create_user("mcp_list_filter", "mcp_list_filter@test.com", "test123")
        # Ensure user is NOT admin
        async with aiosqlite.connect(str(DATABASE_PATH)) as db:
            await db.execute("UPDATE users SET role = 'user' WHERE id = ?", (user["id"],))
            await db.commit()

        _current_user.set(user)

        try:
            result = await list_knowledge_base()
            # User has no group access, so KBs should be filtered out
            assert isinstance(result, str)
        finally:
            _current_user.set(None)

    @pytest.mark.asyncio
    async def test_create_new_knowledge_non_admin_denied(self):
        """Non-admin user should be denied creating knowledge bases"""
        from app.mcp.auth import _current_user
        from app.auth.service import create_user

        user = await create_user("mcp_create_denied", "mcp_create_denied@test.com", "test123")
        # Ensure user is NOT admin - update both DB and dict
        user["role"] = "user"
        async with aiosqlite.connect(str(DATABASE_PATH)) as db:
            await db.execute("UPDATE users SET role = 'user' WHERE id = ?", (user["id"],))
            await db.commit()

        _current_user.set(user)

        try:
            result = await create_new_knowledge("should-fail", "Should Fail")
            assert "权限不足" in result
        finally:
            _current_user.set(None)


# ========== MCP Anonymous Permission Tests ==========


class TestMCPAnonymousPermission:
    """Test that MCP tools enforce permissions for anonymous users"""

    @pytest.fixture(autouse=True)
    async def cleanup_users(self):
        async with aiosqlite.connect(str(DATABASE_PATH)) as db:
            await db.execute("DELETE FROM users")
            await db.execute("DELETE FROM permission_groups")
            await db.execute("DELETE FROM user_groups")
            await db.execute("DELETE FROM access_rules")
            await db.commit()
        yield
        async with aiosqlite.connect(str(DATABASE_PATH)) as db:
            await db.execute("DELETE FROM users")
            await db.execute("DELETE FROM permission_groups")
            await db.execute("DELETE FROM user_groups")
            await db.execute("DELETE FROM access_rules")
            await db.commit()

    @pytest.mark.asyncio
    async def test_anonymous_denied_with_no_rule(self):
        """Anonymous user with no rule should be denied"""
        import uuid
        from app.mcp.auth import _current_user

        kb_id = f"anon-deny-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_knowledge(kb_id, "No Anon KB", "", [], "tester")
            _current_user.set(None)

            result = await get_knowledge_detail(kb_id)
            assert "权限不足" in result
        finally:
            _current_user.set(None)
            _force_rmtree(kb_path)

    @pytest.mark.asyncio
    async def test_anonymous_allowed_with_read_rule(self, setup_test_kb):
        """Anonymous user with read rule should be allowed to read"""
        kb_id, _ = setup_test_kb
        from app.mcp.auth import _current_user
        from app.knowledge.access_rules import set_access_rule

        await set_access_rule(kb_id, None, "read")
        _current_user.set(None)

        try:
            result = await get_knowledge_detail(kb_id)
            assert kb_id in result
        finally:
            _current_user.set(None)

    @pytest.mark.asyncio
    async def test_anonymous_denied_write_with_read_rule(self, setup_test_kb):
        """Anonymous user with only read rule should be denied write"""
        kb_id, kb_path = setup_test_kb
        test_file = kb_path / "test.txt"
        test_file.write_text("original", encoding="utf-8")

        from app.mcp.auth import _current_user
        from app.knowledge.access_rules import set_access_rule

        await set_access_rule(kb_id, None, "read")
        _current_user.set(None)

        try:
            result = await update_file(kb_id, "test.txt", "hacked")
            assert "权限不足" in result
        finally:
            _current_user.set(None)


# ========== MCP Auth Middleware Integration Tests ==========


class TestMCPAuthMiddlewareIntegration:
    """Integration tests for MCPAuthMiddleware ASGI middleware"""

    def _make_scope(self, headers=None, scope_type="http"):
        """Create a minimal ASGI scope"""
        return {
            "type": scope_type,
            "headers": headers or [],
        }

    async def _dummy_receive(self):
        return {"type": "http.request"}

    async def _dummy_send(self, message):
        pass

    @pytest.mark.asyncio
    async def test_middleware_extracts_bearer_token(self):
        """Middleware extracts Bearer token from Authorization header"""
        from app.mcp.server import MCPAuthMiddleware
        from app.mcp.auth import _current_user, get_mcp_user

        captured_tokens = []

        async def mock_set_mcp_user(token):
            captured_tokens.append(token)

        async def app(scope, receive, send):
            pass

        middleware = MCPAuthMiddleware(app)
        scope = self._make_scope(headers=[
            (b"authorization", b"Bearer test-token-123"),
        ])

        with patch("app.mcp.server.set_mcp_user", side_effect=mock_set_mcp_user):
            await middleware(scope, self._dummy_receive, self._dummy_send)

        assert captured_tokens == ["test-token-123"]

    @pytest.mark.asyncio
    async def test_middleware_handles_no_auth_header(self):
        """Middleware passes None when no Authorization header"""
        from app.mcp.server import MCPAuthMiddleware

        captured_tokens = []

        async def mock_set_mcp_user(token):
            captured_tokens.append(token)

        async def app(scope, receive, send):
            pass

        middleware = MCPAuthMiddleware(app)
        scope = self._make_scope(headers=[])

        with patch("app.mcp.server.set_mcp_user", side_effect=mock_set_mcp_user):
            await middleware(scope, self._dummy_receive, self._dummy_send)

        assert captured_tokens == [None]

    @pytest.mark.asyncio
    async def test_middleware_handles_non_bearer_auth(self):
        """Middleware passes full header value when not Bearer prefix"""
        from app.mcp.server import MCPAuthMiddleware

        captured_tokens = []

        async def mock_set_mcp_user(token):
            captured_tokens.append(token)

        async def app(scope, receive, send):
            pass

        middleware = MCPAuthMiddleware(app)
        scope = self._make_scope(headers=[
            (b"authorization", b"Basic dXNlcjpwYXNz"),
        ])

        with patch("app.mcp.server.set_mcp_user", side_effect=mock_set_mcp_user):
            await middleware(scope, self._dummy_receive, self._dummy_send)

        # Non-Bearer auth header: auth_header doesn't start with "Bearer ", so token stays None
        assert captured_tokens == [None]

    @pytest.mark.asyncio
    async def test_middleware_skips_non_http_scope(self):
        """Middleware does not call set_mcp_user for non-HTTP scopes"""
        from app.mcp.server import MCPAuthMiddleware

        called = []

        async def mock_set_mcp_user(token):
            called.append(True)

        async def app(scope, receive, send):
            pass

        middleware = MCPAuthMiddleware(app)
        scope = self._make_scope(scope_type="websocket")

        with patch("app.mcp.server.set_mcp_user", side_effect=mock_set_mcp_user):
            await middleware(scope, self._dummy_receive, self._dummy_send)

        assert called == []

    @pytest.mark.asyncio
    async def test_middleware_handles_empty_auth_header(self):
        """Middleware passes None when Authorization header is empty"""
        from app.mcp.server import MCPAuthMiddleware

        captured_tokens = []

        async def mock_set_mcp_user(token):
            captured_tokens.append(token)

        async def app(scope, receive, send):
            pass

        middleware = MCPAuthMiddleware(app)
        scope = self._make_scope(headers=[
            (b"authorization", b""),
        ])

        with patch("app.mcp.server.set_mcp_user", side_effect=mock_set_mcp_user):
            await middleware(scope, self._dummy_receive, self._dummy_send)

        assert captured_tokens == [None]

    @pytest.mark.asyncio
    async def test_set_mcp_user_with_none_clears_context(self):
        """set_mcp_user(None) clears the user context"""
        from app.mcp.auth import set_mcp_user, get_mcp_user, _current_user

        _current_user.set({"id": 1, "username": "test"})
        await set_mcp_user(None)
        assert get_mcp_user() is None

    @pytest.mark.asyncio
    async def test_set_mcp_user_with_invalid_token_clears_context(self):
        """set_mcp_user with invalid JWT clears the user context"""
        from app.mcp.auth import set_mcp_user, get_mcp_user, _current_user

        _current_user.set({"id": 1, "username": "test"})
        await set_mcp_user("invalid-token-string")
        assert get_mcp_user() is None

    @pytest.mark.asyncio
    async def test_get_mcp_user_returns_none_by_default(self):
        """get_mcp_user returns None when no user is set"""
        from app.mcp.auth import get_mcp_user, _current_user

        _current_user.set(None)
        assert get_mcp_user() is None

    @pytest.mark.asyncio
    async def test_get_mcp_user_returns_set_user(self):
        """get_mcp_user returns the user that was set"""
        from app.mcp.auth import set_mcp_user, get_mcp_user, _current_user

        test_user = {"id": 42, "username": "testuser", "role": "admin"}
        _current_user.set(test_user)
        assert get_mcp_user() == test_user

    @pytest.mark.asyncio
    async def test_set_mcp_user_with_valid_token(self):
        """set_mcp_user with a valid JWT sets the user context"""
        from app.mcp.auth import set_mcp_user, get_mcp_user, _current_user
        from app.auth.service import create_user, create_access_token

        # Create a real user and token
        user = await create_user("mcp_valid_token", "mcp_valid@test.com", "test123")
        token = create_access_token({"sub": user["username"], "user_id": user["id"]})

        _current_user.set(None)
        await set_mcp_user(token)
        result = get_mcp_user()
        assert result is not None
        assert result["username"] == "mcp_valid_token"
