import json
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger

from app.config import get_knowledge_path, settings
from app.database import DATABASE_PATH


def get_manifest_path(knowledge_id: str) -> Path:
    return get_knowledge_path(knowledge_id) / ".manifest.json"


def load_manifest(knowledge_id: str) -> dict | None:
    manifest_path = get_manifest_path(knowledge_id)
    if not manifest_path.exists():
        return None
    try:
        with open(manifest_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        logger.warning("Manifest corrupted: {}, skipped ({})", manifest_path, e)
        return None


def save_manifest(knowledge_id: str, manifest: dict):
    manifest_path = get_manifest_path(knowledge_id)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.error("Manifest save failed: {}, {}", manifest_path, e)
        raise ValueError(f"保存元数据失败: {e}")


def create_manifest(
    knowledge_id: str,
    name: str,
    description: str,
    tags: list[str],
    created_by: str,
    category: str = "默认",
) -> dict:
    now = datetime.now(UTC).isoformat()
    manifest = {
        "id": knowledge_id,
        "name": name,
        "description": description,
        "created_by": created_by,
        "created_at": now,
        "updated_by": created_by,
        "updated_at": now,
        "tags": tags,
        "summary": "",
        "version": 1,
        "category": category,
    }
    save_manifest(knowledge_id, manifest)
    return manifest


def update_manifest(
    knowledge_id: str, updates: dict, updated_by: str
) -> dict | None:
    manifest = load_manifest(knowledge_id)
    if not manifest:
        return None
    manifest.update(updates)
    manifest["updated_by"] = updated_by
    manifest["updated_at"] = datetime.now(UTC).isoformat()
    manifest["version"] = manifest.get("version", 0) + 1
    save_manifest(knowledge_id, manifest)
    return manifest


def list_all_manifests() -> list[dict]:
    manifests = []
    if settings.KNOWLEDGE_BASE_PATH.exists():
        for item in settings.KNOWLEDGE_BASE_PATH.iterdir():
            if item.is_dir():
                manifest = load_manifest(item.name)
                if manifest:
                    manifests.append(manifest)
    logger.debug("Loaded {} knowledge bases", len(manifests))
    return manifests


def _cleanup_db_records(knowledge_id: str):
    """同步清理 SQLite 中的孤儿记录"""
    try:
        conn = sqlite3.connect(str(DATABASE_PATH))
        try:
            conn.execute("DELETE FROM access_rules WHERE knowledge_id = ?", (knowledge_id,))
            conn.execute("DELETE FROM search_index WHERE knowledge_id = ?", (knowledge_id,))
            conn.commit()
        except Exception as e:
            logger.warning("DB cleanup failed for KB {}: {}", knowledge_id, e)
            conn.rollback()
        finally:
            conn.close()
    except Exception as e:
        logger.error("DB connection failed during cleanup for KB {}: {}", knowledge_id, e)


def delete_knowledge(knowledge_id: str) -> bool:
    knowledge_path = get_knowledge_path(knowledge_id)
    if not knowledge_path.exists():
        return False
    shutil.rmtree(knowledge_path)
    _cleanup_db_records(knowledge_id)
    logger.info("KB deleted: {}", knowledge_id)
    return True
