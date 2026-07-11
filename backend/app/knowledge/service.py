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


def get_file_tree(knowledge_id: str, path: str = "") -> list[dict]:
    base_path = get_knowledge_path(knowledge_id) / path
    if not base_path.exists():
        return []

    tree = []
    for item in sorted(base_path.iterdir()):
        if item.name.startswith(".") and item.name != ".manifest.json":
            continue
        node = {
            "name": item.name,
            "path": str(Path(path) / item.name) if path else item.name,
            "is_dir": item.is_dir(),
        }
        if item.is_dir():
            node["children"] = get_file_tree(knowledge_id, node["path"])
        tree.append(node)
    return tree


def get_file_content(knowledge_id: str, file_path: str) -> dict | None:
    full_path = get_knowledge_path(knowledge_id) / file_path
    if not full_path.exists() or full_path.is_dir():
        return None

    stat = full_path.stat()
    content = full_path.read_text(encoding="utf-8", errors="ignore")
    return {
        "path": file_path,
        "content": content,
        "size": stat.st_size,
        "modified_at": str(stat.st_mtime),
    }


def update_file_content(knowledge_id: str, file_path: str, content: str) -> bool:
    full_path = get_knowledge_path(knowledge_id) / file_path
    if not full_path.parent.exists():
        full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    return True


def create_directory(knowledge_id: str, dir_path: str) -> bool:
    full_path = get_knowledge_path(knowledge_id) / dir_path
    if full_path.exists():
        return False
    full_path.mkdir(parents=True, exist_ok=True)
    return True


def upload_file(knowledge_id: str, file_path: str, content: bytes) -> bool:
    full_path = get_knowledge_path(knowledge_id) / file_path
    if not full_path.parent.exists():
        full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(content)
    return True
