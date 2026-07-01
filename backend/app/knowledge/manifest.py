import json
from pathlib import Path
from datetime import datetime, timezone
from app.config import settings


def get_manifest_path(knowledge_id: str) -> Path:
    return settings.KNOWLEDGE_BASE_PATH / knowledge_id / ".manifest.json"


def load_manifest(knowledge_id: str) -> dict | None:
    manifest_path = get_manifest_path(knowledge_id)
    if not manifest_path.exists():
        return None
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(knowledge_id: str, manifest: dict):
    manifest_path = get_manifest_path(knowledge_id)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def create_manifest(knowledge_id: str, name: str, description: str, tags: list[str], created_by: str, category: str = "默认") -> dict:
    now = datetime.now(timezone.utc).isoformat()
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


def update_manifest(knowledge_id: str, updates: dict, updated_by: str) -> dict | None:
    manifest = load_manifest(knowledge_id)
    if not manifest:
        return None
    manifest.update(updates)
    manifest["updated_by"] = updated_by
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
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
    return manifests


def delete_knowledge(knowledge_id: str) -> bool:
    knowledge_path = settings.KNOWLEDGE_BASE_PATH / knowledge_id
    if not knowledge_path.exists():
        return False
    import shutil
    shutil.rmtree(knowledge_path)
    return True
