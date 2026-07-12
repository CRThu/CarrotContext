"""manifest 防御测试 — 覆盖损坏、缺失、边界情况"""
import json
import shutil
import sqlite3
import uuid
from pathlib import Path

import pytest

from app.config import settings
from app.database import DATABASE_PATH
from app.knowledge.manifest import (
    create_manifest,
    delete_knowledge,
    get_manifest_path,
    list_all_manifests,
    load_manifest,
    save_manifest,
    update_manifest,
    _cleanup_db_records,
)


def _force_rmtree(path: Path):
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


class TestLoadManifest:
    def test_load_normal_json(self):
        kb_id = f"manifest-normal-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            manifest_path = kb_path / ".manifest.json"
            manifest_path.write_text(json.dumps({"id": kb_id, "name": "Test"}), encoding="utf-8")
            result = load_manifest(kb_id)
            assert result is not None
            assert result["id"] == kb_id
        finally:
            _force_rmtree(kb_path)

    def test_load_corrupted_json(self):
        kb_id = f"manifest-corrupt-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            manifest_path = kb_path / ".manifest.json"
            manifest_path.write_text("{invalid json!!!", encoding="utf-8")
            result = load_manifest(kb_id)
            assert result is None
        finally:
            _force_rmtree(kb_path)

    def test_load_empty_file(self):
        kb_id = f"manifest-empty-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            manifest_path = kb_path / ".manifest.json"
            manifest_path.write_text("", encoding="utf-8")
            result = load_manifest(kb_id)
            assert result is None
        finally:
            _force_rmtree(kb_path)

    def test_load_nonexistent(self):
        result = load_manifest("nonexistent-kb-xyz123")
        assert result is None

    def test_load_non_utf8_content(self):
        kb_id = f"manifest-binary-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            manifest_path = kb_path / ".manifest.json"
            manifest_path.write_bytes(b"\x89\x8a\x8b\xff\xfe")
            result = load_manifest(kb_id)
            assert result is None
        finally:
            _force_rmtree(kb_path)


class TestSaveManifest:
    def test_save_normal(self):
        kb_id = f"manifest-save-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            manifest = {"id": kb_id, "name": "Save Test"}
            save_manifest(kb_id, manifest)
            loaded = load_manifest(kb_id)
            assert loaded == manifest
        finally:
            _force_rmtree(kb_path)

    def test_save_creates_parent_dir(self):
        kb_id = f"manifest-nested-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            manifest = {"id": kb_id, "name": "Nested"}
            save_manifest(kb_id, manifest)
            assert (kb_path / ".manifest.json").exists()
        finally:
            _force_rmtree(kb_path)


class TestListAllManifests:
    def test_list_empty_directory(self):
        kb_id = f"manifest-list-empty-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            manifests = list_all_manifests()
            assert isinstance(manifests, list)
        finally:
            _force_rmtree(kb_path)

    def test_list_mixed_normal_and_corrupted(self):
        kb_id_ok = f"manifest-mixed-ok-{uuid.uuid4().hex[:8]}"
        kb_id_bad = f"manifest-mixed-bad-{uuid.uuid4().hex[:8]}"
        kb_path_ok = settings.KNOWLEDGE_BASE_PATH / kb_id_ok
        kb_path_bad = settings.KNOWLEDGE_BASE_PATH / kb_id_bad
        try:
            kb_path_ok.mkdir(parents=True, exist_ok=True)
            (kb_path_ok / ".manifest.json").write_text(
                json.dumps({"id": kb_id_ok, "name": "OK KB"}), encoding="utf-8"
            )
            kb_path_bad.mkdir(parents=True, exist_ok=True)
            (kb_path_bad / ".manifest.json").write_text("CORRUPTED!!!", encoding="utf-8")

            manifests = list_all_manifests()
            ids = [m["id"] for m in manifests]
            assert kb_id_ok in ids
            assert kb_id_bad not in ids
        finally:
            _force_rmtree(kb_path_ok)
            _force_rmtree(kb_path_bad)

    def test_list_directory_without_manifest(self):
        kb_id = f"manifest-no-file-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            manifests = list_all_manifests()
            ids = [m["id"] for m in manifests if m.get("id") == kb_id]
            assert len(ids) == 0
        finally:
            _force_rmtree(kb_path)


class TestCreateManifest:
    def test_create_normal(self):
        kb_id = f"manifest-create-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            result = create_manifest(kb_id, "Test KB", "Description", ["tag1"], "admin")
            assert result["id"] == kb_id
            assert result["name"] == "Test KB"
            assert result["version"] == 1
            assert (kb_path / ".manifest.json").exists()
        finally:
            _force_rmtree(kb_path)


class TestUpdateManifest:
    def test_update_increments_version(self):
        kb_id = f"manifest-update-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            create_manifest(kb_id, "Original", "", [], "admin")
            updated = update_manifest(kb_id, {"description": "Updated"}, "admin")
            assert updated is not None
            assert updated["version"] == 2
            assert updated["description"] == "Updated"
        finally:
            _force_rmtree(kb_path)

    def test_update_nonexistent(self):
        result = update_manifest("nonexistent-kb-xyz123", {"name": "x"}, "admin")
        assert result is None


class TestDeleteKnowledge:
    def test_delete_removes_directory(self):
        kb_id = f"manifest-del-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            (kb_path / ".manifest.json").write_text("{}", encoding="utf-8")
            result = delete_knowledge(kb_id)
            assert result is True
            assert not kb_path.exists()
        finally:
            if kb_path.exists():
                _force_rmtree(kb_path)

    def test_delete_nonexistent(self):
        result = delete_knowledge("nonexistent-kb-xyz123")
        assert result is False

    def test_delete_cleans_db_records(self):
        kb_id = f"manifest-del-db-{uuid.uuid4().hex[:8]}"
        kb_path = settings.KNOWLEDGE_BASE_PATH / kb_id
        try:
            kb_path.mkdir(parents=True, exist_ok=True)
            (kb_path / ".manifest.json").write_text("{}", encoding="utf-8")
            conn = sqlite3.connect(str(DATABASE_PATH))
            try:
                conn.execute(
                    "INSERT INTO access_rules (knowledge_id, group_id, access_level) VALUES (?, NULL, 'read')",
                    (kb_id,),
                )
                conn.execute(
                    "INSERT INTO search_index (knowledge_id, file_path, title, tags, summary, content) VALUES (?, '', ?, '', '', '')",
                    (kb_id, kb_id),
                )
                conn.commit()
            finally:
                conn.close()

            delete_knowledge(kb_id)

            conn = sqlite3.connect(str(DATABASE_PATH))
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM access_rules WHERE knowledge_id = ?", (kb_id,))
                assert cursor.fetchone()[0] == 0
                cursor = conn.execute("SELECT COUNT(*) FROM search_index WHERE knowledge_id = ?", (kb_id,))
                assert cursor.fetchone()[0] == 0
            finally:
                conn.close()
        finally:
            if kb_path.exists():
                _force_rmtree(kb_path)


class TestCleanupDbRecords:
    def test_cleanup_removes_access_rules(self):
        kb_id = f"cleanup-ar-{uuid.uuid4().hex[:8]}"
        conn = sqlite3.connect(str(DATABASE_PATH))
        try:
            conn.execute(
                "INSERT INTO access_rules (knowledge_id, group_id, access_level) VALUES (?, NULL, 'read')",
                (kb_id,),
            )
            conn.commit()
            _cleanup_db_records(kb_id)
            cursor = conn.execute("SELECT COUNT(*) FROM access_rules WHERE knowledge_id = ?", (kb_id,))
            assert cursor.fetchone()[0] == 0
        finally:
            conn.close()

    def test_cleanup_removes_search_index(self):
        kb_id = f"cleanup-si-{uuid.uuid4().hex[:8]}"
        conn = sqlite3.connect(str(DATABASE_PATH))
        try:
            conn.execute(
                "INSERT INTO search_index (knowledge_id, file_path, title, tags, summary, content) VALUES (?, '', ?, '', '', '')",
                (kb_id, kb_id),
            )
            conn.commit()
            _cleanup_db_records(kb_id)
            cursor = conn.execute("SELECT COUNT(*) FROM search_index WHERE knowledge_id = ?", (kb_id,))
            assert cursor.fetchone()[0] == 0
        finally:
            conn.close()

    def test_cleanup_nonexistent_kb_is_noop(self):
        _cleanup_db_records("nonexistent-cleanup-xyz123")
