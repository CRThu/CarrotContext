from pathlib import Path

from app.config import settings
from app.knowledge.manifest import (
    create_manifest,
    delete_knowledge,
    list_all_manifests,
    load_manifest,
    update_manifest,
)


def get_knowledge_path(knowledge_id: str) -> Path:
    return settings.KNOWLEDGE_BASE_PATH / knowledge_id


def list_knowledge() -> list[dict]:
    return list_all_manifests()


def get_knowledge(knowledge_id: str) -> dict | None:
    return load_manifest(knowledge_id)


def create_knowledge(
    knowledge_id: str,
    name: str,
    description: str,
    tags: list[str],
    created_by: str,
    category: str = "默认",
) -> dict:
    knowledge_path = get_knowledge_path(knowledge_id)
    if knowledge_path.exists():
        raise ValueError("知识库已存在")
    knowledge_path.mkdir(parents=True, exist_ok=True)
    return create_manifest(knowledge_id, name, description, tags, created_by, category)


def update_knowledge(
    knowledge_id: str, updates: dict, updated_by: str
) -> dict | None:
    return update_manifest(knowledge_id, updates, updated_by)


def remove_knowledge(knowledge_id: str) -> bool:
    return delete_knowledge(knowledge_id)
