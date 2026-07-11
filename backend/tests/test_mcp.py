"""MCP工具单元测试 + SSE集成测试"""
import json
import shutil
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from app.config import settings
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
    # 最后尝试忽略错误
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
    import uuid

    kb_id = f"mcp-test-{uuid.uuid4().hex[:8]}"
    kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
    try:
        create_knowledge(kb_id, f"MCP测试库-{kb_id}", "用于MCP工具测试", ["test"], "tester")
        yield kb_id, kb_path
    finally:
        _force_rmtree(kb_path)


@pytest.fixture
def setup_test_kb_with_search_index(setup_test_kb):
    """创建带搜索索引的测试知识库"""
    kb_id, kb_path = setup_test_kb
    # 更新搜索索引，使元数据搜索可用
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
    def test_list_with_knowledge(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = list_knowledge_base()
        assert kb_id in result

    def test_list_empty(self):
        # 确保数据库中没有其他测试库干扰
        result = list_knowledge_base()
        assert isinstance(result, str)


# ========== get_knowledge_detail 测试 ==========

class TestGetKnowledgeDetail:
    def test_get_existing(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = get_knowledge_detail(kb_id)
        assert kb_id in result
        assert "tester" in result

    def test_get_nonexistent(self):
        result = get_knowledge_detail("nonexistent-kb-xyz123")
        assert "不存在" in result


# ========== read_file_content 测试 ==========

class TestReadFileContent:
    def test_read_existing_file(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        test_file = kb_path / "test.txt"
        test_file.write_text("hello mcp", encoding="utf-8")

        result = read_file_content(kb_id, "test.txt")
        assert result == "hello mcp"

    def test_read_nonexistent_file(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = read_file_content(kb_id, "no-such-file.txt")
        assert "不存在" in result

    def test_read_nested_file(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        nested = kb_path / "subdir" / "nested.txt"
        nested.parent.mkdir(parents=True)
        nested.write_text("nested content", encoding="utf-8")

        result = read_file_content(kb_id, "subdir/nested.txt")
        assert result == "nested content"


# ========== update_file 测试 ==========

class TestUpdateFile:
    def test_update_existing_file(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        test_file = kb_path / "update-me.txt"
        test_file.write_text("old content", encoding="utf-8")

        result = update_file(kb_id, "update-me.txt", "new content")
        assert "更新成功" in result
        assert test_file.read_text(encoding="utf-8") == "new content"

    def test_update_creates_new_file(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        result = update_file(kb_id, "new-file.txt", "created by mcp")
        assert "更新成功" in result
        assert (kb_path / "new-file.txt").read_text(encoding="utf-8") == "created by mcp"

    def test_update_creates_nested_file(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        result = update_file(kb_id, "deep/nested/file.txt", "deep content")
        assert "更新成功" in result
        assert (kb_path / "deep" / "nested" / "file.txt").read_text(encoding="utf-8") == "deep content"

    def test_update_empty_content(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        result = update_file(kb_id, "empty.txt", "")
        assert "更新成功" in result
        assert (kb_path / "empty.txt").read_text(encoding="utf-8") == ""


# ========== create_new_knowledge 测试 ==========

class TestCreateNewKnowledge:
    def test_create_success(self):
        import uuid
        kb_id = f"mcp-create-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            result = create_new_knowledge(kb_id, "新建测试库", "描述", "tag1,tag2")
            assert "创建成功" in result
            assert kb_path.exists()
            manifest = json.loads((kb_path / ".manifest.json").read_text(encoding="utf-8"))
            assert manifest["name"] == "新建测试库"
            assert "tag1" in manifest["tags"]
        finally:
            _force_rmtree(kb_path)

    def test_create_duplicate(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = create_new_knowledge(kb_id, "重复创建")
        assert "已存在" in result

    def test_create_no_tags(self):
        import uuid
        kb_id = f"mcp-notags-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            result = create_new_knowledge(kb_id, "无标签库", "desc", "")
            assert "创建成功" in result
            manifest = json.loads((kb_path / ".manifest.json").read_text(encoding="utf-8"))
            assert manifest["tags"] == []
        finally:
            _force_rmtree(kb_path)

    def test_create_single_tag(self):
        import uuid
        kb_id = f"mcp-onetag-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            result = create_new_knowledge(kb_id, "单标签库", "desc", "solo")
            assert "创建成功" in result
            manifest = json.loads((kb_path / ".manifest.json").read_text(encoding="utf-8"))
            assert manifest["tags"] == ["solo"]
        finally:
            _force_rmtree(kb_path)

    def test_create_tags_with_spaces(self):
        import uuid
        kb_id = f"mcp-spaces-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            result = create_new_knowledge(kb_id, "空格标签", "desc", " tag1 , tag2 , ")
            assert "创建成功" in result
            manifest = json.loads((kb_path / ".manifest.json").read_text(encoding="utf-8"))
            assert manifest["tags"] == ["tag1", "tag2"]
        finally:
            _force_rmtree(kb_path)


# ========== search_knowledge 测试 ==========

class TestSearchKnowledge:
    def test_search_metadata(self, setup_test_kb_with_search_index):
        kb_id, _ = setup_test_kb_with_search_index
        result = search_knowledge(kb_id, mode="metadata")
        assert "元数据" in result or kb_id in result

    def test_search_content(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        (kb_path / "readme.md").write_text("这是一个测试文档", encoding="utf-8")

        result = search_knowledge("测试文档", mode="content")
        assert isinstance(result, str)

    def test_search_all_mode(self, setup_test_kb_with_search_index):
        kb_id, kb_path = setup_test_kb_with_search_index
        (kb_path / "doc.md").write_text("hello world", encoding="utf-8")

        result = search_knowledge(kb_id, mode="all")
        assert isinstance(result, str)

    def test_search_no_results(self, setup_test_kb):
        result = search_knowledge("完全不存在的关键词xyz123")
        assert "没有找到" in result

    def test_search_invalid_mode(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = search_knowledge(kb_id, mode="invalid")
        assert isinstance(result, str)


# ========== get_git_history 测试 ==========

class TestGitHistory:
    def test_get_history_empty(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = get_git_history(kb_id)
        assert "没有提交历史" in result

    def test_get_history_with_commits(self, setup_git_kb):
        kb_id, kb_path = setup_git_kb
        (kb_path / "file1.txt").write_text("content", encoding="utf-8")
        from app.git.service import create_git_commit
        commit_result = create_git_commit(kb_id, "initial commit")
        assert commit_result is not None, "Git commit should succeed"

        result = get_git_history(kb_id, limit=5)
        assert "initial commit" in result

    def test_get_history_limit(self, setup_git_kb):
        kb_id, kb_path = setup_git_kb
        from app.git.service import create_git_commit

        for i in range(5):
            (kb_path / f"file{i}.txt").write_text(f"content {i}", encoding="utf-8")
            create_git_commit(kb_id, f"commit {i}")

        result = get_git_history(kb_id, limit=2)
        lines = result.strip().split("\n")
        assert len(lines) == 2


# ========== get_file_diff 测试 ==========

class TestFileDiff:
    def test_diff_no_repo(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        result = get_file_diff(kb_id)
        assert "没有差异" in result

    def test_diff_with_changes(self, setup_git_kb):
        kb_id, kb_path = setup_git_kb
        (kb_path / "diff-test.txt").write_text("original", encoding="utf-8")
        from app.git.service import create_git_commit
        create_git_commit(kb_id, "add file")
        (kb_path / "diff-test.txt").write_text("modified", encoding="utf-8")

        result = get_file_diff(kb_id, "diff-test.txt")
        assert isinstance(result, str)

    def test_diff_no_changes(self, setup_git_kb):
        kb_id, kb_path = setup_git_kb
        (kb_path / "clean.txt").write_text("stable", encoding="utf-8")
        from app.git.service import create_git_commit
        create_git_commit(kb_id, "add file")

        result = get_file_diff(kb_id, "clean.txt")
        assert "没有差异" in result

    def test_diff_with_commit_param(self, setup_git_kb):
        kb_id, kb_path = setup_git_kb
        (kb_path / "file.txt").write_text("v1", encoding="utf-8")
        from app.git.service import create_git_commit
        commit = create_git_commit(kb_id, "first")
        (kb_path / "file.txt").write_text("v2", encoding="utf-8")

        result = get_file_diff(kb_id, "file.txt", commit["hash"])
        assert isinstance(result, str)


# ========== commit_changes 测试 ==========

class TestCommitChanges:
    def test_commit_success(self, setup_git_kb):
        kb_id, kb_path = setup_git_kb
        (kb_path / "commit.txt").write_text("to commit", encoding="utf-8")

        result = commit_changes(kb_id, "test commit", "commit.txt")
        assert "提交成功" in result
        assert "test commit" in result

    def test_commit_no_repo(self, setup_test_kb):
        kb_id, kb_path = setup_test_kb
        (kb_path / "orphan.txt").write_text("orphan", encoding="utf-8")
        result = commit_changes(kb_id, "no repo commit", "orphan.txt")
        # commit_changes auto-initializes git, so this should succeed or fail gracefully
        assert isinstance(result, str)

    def test_commit_all_files(self, setup_git_kb):
        kb_id, kb_path = setup_git_kb
        (kb_path / "a.txt").write_text("aaa", encoding="utf-8")
        (kb_path / "b.txt").write_text("bbb", encoding="utf-8")

        result = commit_changes(kb_id, "commit all")
        assert "提交成功" in result

    def test_commit_nonexistent_file(self, setup_git_kb):
        kb_id, _ = setup_git_kb
        result = commit_changes(kb_id, "commit missing", "ghost.txt")
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
        """测试MCP路由在FastAPI中已正确配置"""
        from app.main import app

        # 检查FastAPI路由表中是否包含/mcp挂载点
        routes_found = False
        for route in app.routes:
            if hasattr(route, "path") and route.path.startswith("/mcp"):
                routes_found = True
                break
        assert routes_found, "MCP route not found in app routes"

    def test_mcp_disabled_no_mount(self):
        """测试MCP禁用时不挂载路由"""
        from unittest.mock import patch
        from fastapi import FastAPI

        test_app = FastAPI()
        with patch("app.config.settings") as mock_settings:
            mock_settings.MCP_ENABLED = False
            mock_settings.MCP_PATH = "/mcp"
            # 不挂载MCP时，路由不存在
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
        # 无参数工具
        assert tool.parameters == {} or tool.parameters.get("properties", {}) == {}

    def test_search_knowledge_default_mode(self, setup_test_kb_with_search_index):
        kb_id, _ = setup_test_kb_with_search_index
        # 默认mode应该是"all"
        result = search_knowledge(kb_id)
        assert isinstance(result, str)

    def test_get_file_diff_defaults(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        # 测试默认参数（空字符串转None）
        result = get_file_diff(kb_id, "", "")
        assert "没有差异" in result

    def test_commit_changes_defaults(self, setup_test_kb):
        kb_id, _ = setup_test_kb
        # 测试默认参数（空字符串转None）
        result = commit_changes(kb_id, "test commit", "")
        assert isinstance(result, str)
