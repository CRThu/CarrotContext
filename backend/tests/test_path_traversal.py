"""路径穿越安全测试 — 覆盖 _safe_path 和所有文件操作"""
import shutil
import uuid
from pathlib import Path

import pytest

from app.config import settings
from app.files.service import (
    _safe_path,
    create_directory,
    delete_file,
    get_binary_content,
    get_file_content,
    get_file_tree,
    is_binary_file,
    move_file,
    update_file_content,
    upload_file,
)


def _force_rmtree(path: Path):
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


class TestSafePath:
    def test_normal_path(self):
        kb_id = f"safe-normal-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = _safe_path(kb_id, "test.md")
            assert result is not None
            assert str(result).startswith(str(kb_path.resolve()))
        finally:
            _force_rmtree(kb_path)

    def test_nested_path(self):
        kb_id = f"safe-nested-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = _safe_path(kb_id, "docs/sub/file.md")
            assert result is not None
        finally:
            _force_rmtree(kb_path)

    def test_path_traversal_dotdot(self):
        kb_id = f"safe-traversal-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = _safe_path(kb_id, "../../../etc/passwd")
            assert result is None
        finally:
            _force_rmtree(kb_path)

    def test_path_traversal_deep(self):
        kb_id = f"safe-deep-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = _safe_path(kb_id, "../../../../../../etc/shadow")
            assert result is None
        finally:
            _force_rmtree(kb_path)

    def test_empty_path(self):
        kb_id = f"safe-empty-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = _safe_path(kb_id, "")
            assert result is not None
            assert result.resolve() == kb_path.resolve()
        finally:
            _force_rmtree(kb_path)

    def test_absolute_path_rejected(self):
        kb_id = f"safe-abs-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = _safe_path(kb_id, "/etc/passwd")
            assert result is None
        finally:
            _force_rmtree(kb_path)


class TestGetFileContentTraversal:
    def test_normal_file(self):
        kb_id = f"trav-content-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            (kb_path / "test.md").write_text("Hello", encoding="utf-8")
            result = get_file_content(kb_id, "test.md")
            assert result is not None
            assert result["content"] == "Hello"
        finally:
            _force_rmtree(kb_path)

    def test_traversal_returns_none(self):
        kb_id = f"trav-content2-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = get_file_content(kb_id, "../../../etc/passwd")
            assert result is None
        finally:
            _force_rmtree(kb_path)

    def test_nonexistent_file(self):
        kb_id = f"trav-content3-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = get_file_content(kb_id, "nonexistent.md")
            assert result is None
        finally:
            _force_rmtree(kb_path)


class TestUpdateFileContentTraversal:
    def test_normal_update(self):
        kb_id = f"trav-update-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = update_file_content(kb_id, "test.md", "content")
            assert result is True
            assert (kb_path / "test.md").read_text(encoding="utf-8") == "content"
        finally:
            _force_rmtree(kb_path)

    def test_traversal_returns_false(self):
        kb_id = f"trav-update2-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = update_file_content(kb_id, "../../../etc/evil", "content")
            assert result is False
        finally:
            _force_rmtree(kb_path)


class TestUploadFileTraversal:
    def test_normal_upload(self):
        kb_id = f"trav-upload-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = upload_file(kb_id, "test.bin", b"\x00\x01\x02")
            assert result is True
            assert (kb_path / "test.bin").read_bytes() == b"\x00\x01\x02"
        finally:
            _force_rmtree(kb_path)

    def test_traversal_returns_false(self):
        kb_id = f"trav-upload2-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = upload_file(kb_id, "../../../tmp/evil", b"\x00")
            assert result is False
        finally:
            _force_rmtree(kb_path)


class TestMoveFileTraversal:
    def test_normal_move(self):
        kb_id = f"trav-move-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            (kb_path / "a.md").write_text("x", encoding="utf-8")
            result = move_file(kb_id, "a.md", "b.md")
            assert result is True
            assert (kb_path / "b.md").exists()
            assert not (kb_path / "a.md").exists()
        finally:
            _force_rmtree(kb_path)

    def test_source_traversal_returns_false(self):
        kb_id = f"trav-move2-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = move_file(kb_id, "../../../etc/passwd", "safe.md")
            assert result is False
        finally:
            _force_rmtree(kb_path)

    def test_dest_traversal_returns_false(self):
        kb_id = f"trav-move3-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            (kb_path / "a.md").write_text("x", encoding="utf-8")
            result = move_file(kb_id, "a.md", "../../../etc/evil")
            assert result is False
        finally:
            _force_rmtree(kb_path)


class TestCreateDirectoryTraversal:
    def test_normal_create(self):
        kb_id = f"trav-mkdir-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = create_directory(kb_id, "newdir")
            assert result is True
            assert (kb_path / "newdir").is_dir()
        finally:
            _force_rmtree(kb_path)

    def test_traversal_returns_false(self):
        kb_id = f"trav-mkdir2-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = create_directory(kb_id, "../../../tmp/evil")
            assert result is False
        finally:
            _force_rmtree(kb_path)


class TestDeleteFileTraversal:
    def test_normal_delete(self):
        kb_id = f"trav-del-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            (kb_path / "to_delete.md").write_text("x", encoding="utf-8")
            result = delete_file(kb_id, "to_delete.md")
            assert result is True
            assert not (kb_path / "to_delete.md").exists()
        finally:
            _force_rmtree(kb_path)

    def test_traversal_returns_false(self):
        kb_id = f"trav-del2-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            result = delete_file(kb_id, "../../../etc/passwd")
            assert result is False
        finally:
            _force_rmtree(kb_path)

    def test_delete_manifest_rejected(self):
        kb_id = f"trav-del3-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            (kb_path / ".manifest.json").write_text("{}", encoding="utf-8")
            result = delete_file(kb_id, ".manifest.json")
            assert result is False
        finally:
            _force_rmtree(kb_path)


class TestGetFileTreeTraversal:
    def test_normal_tree(self):
        kb_id = f"trav-tree-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            (kb_path / "a.md").write_text("x", encoding="utf-8")
            tree = get_file_tree(kb_id)
            assert len(tree) == 1
            assert tree[0]["name"] == "a.md"
        finally:
            _force_rmtree(kb_path)

    def test_traversal_returns_empty(self):
        kb_id = f"trav-tree2-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            tree = get_file_tree(kb_id, "../../../etc")
            assert tree == []
        finally:
            _force_rmtree(kb_path)


class TestIsBinaryFileTraversal:
    def test_normal_binary(self):
        kb_id = f"trav-bin-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            (kb_path / "test.png").write_bytes(b"\x89PNG")
            assert is_binary_file(kb_id, "test.png") is True
        finally:
            _force_rmtree(kb_path)

    def test_traversal_not_binary(self):
        kb_id = f"trav-bin2-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            assert is_binary_file(kb_id, "../../../etc/passwd") is False
        finally:
            _force_rmtree(kb_path)
