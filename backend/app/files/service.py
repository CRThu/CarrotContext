import shutil
from pathlib import Path

from loguru import logger

from app.config import get_knowledge_path

# Known binary file extensions
BINARY_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "bmp", "ico", "webp",
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "zip", "rar", "7z", "tar", "gz",
    "mp3", "mp4", "avi", "mov", "wmv",
    "exe", "dll", "so", "dylib",
}


def _safe_path(knowledge_id: str, file_path: str) -> Path | None:
    """验证文件路径不越出知识库目录。返回安全路径，越界则返回 None。"""
    base = get_knowledge_path(knowledge_id).resolve()
    full = (base / file_path).resolve()
    if not str(full).startswith(str(base)):
        return None
    return full


def get_file_tree(knowledge_id: str, path: str = "") -> list[dict]:
    base_path = _safe_path(knowledge_id, path)
    if base_path is None or not base_path.exists():
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
    full_path = _safe_path(knowledge_id, file_path)
    if full_path is None or not full_path.exists() or full_path.is_dir():
        logger.warning("File not found: KB {}/{}", knowledge_id, file_path)
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
    full_path = _safe_path(knowledge_id, file_path)
    if full_path is None:
        return False
    try:
        if not full_path.parent.exists():
            full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return True
    except OSError as e:
        logger.error("Write failed: KB {}/{} - {}", knowledge_id, file_path, e)
        return False


def create_directory(knowledge_id: str, dir_path: str) -> bool:
    full_path = _safe_path(knowledge_id, dir_path)
    if full_path is None or full_path.exists():
        return False
    full_path.mkdir(parents=True, exist_ok=True)
    return True


def upload_file(knowledge_id: str, file_path: str, content: bytes) -> bool:
    full_path = _safe_path(knowledge_id, file_path)
    if full_path is None:
        return False
    try:
        if not full_path.parent.exists():
            full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return True
    except OSError as e:
        logger.error("Upload failed: KB {}/{} - {}", knowledge_id, file_path, e)
        return False


def delete_file(knowledge_id: str, file_path: str) -> bool:
    full_path = _safe_path(knowledge_id, file_path)
    if full_path is None or not full_path.exists():
        return False
    if file_path == ".manifest.json":
        return False
    if full_path.is_dir():
        shutil.rmtree(full_path)
    else:
        full_path.unlink()
    logger.info("File deleted: KB {}/{}", knowledge_id, file_path)
    return True


def move_file(knowledge_id: str, source_path: str, dest_path: str) -> bool:
    """Move or rename a file/directory within a knowledge base."""
    source = _safe_path(knowledge_id, source_path)
    dest = _safe_path(knowledge_id, dest_path)

    if source is None or dest is None or not source.exists():
        return False

    if source.name == ".manifest.json" or dest.name == ".manifest.json":
        return False

    if dest.exists() and dest.is_dir():
        dest = dest / source.name

    if not dest.parent.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)

    shutil.move(str(source), str(dest))
    return True


def is_binary_file(knowledge_id: str, file_path: str) -> bool:
    """Check if a file is binary based on extension or content"""
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    if ext in BINARY_EXTENSIONS:
        return True

    full_path = _safe_path(knowledge_id, file_path)
    if full_path is None or not full_path.exists():
        return False

    try:
        with open(full_path, "rb") as f:
            chunk = f.read(8192)
            chunk.decode("utf-8")
        return False
    except (UnicodeDecodeError, ValueError):
        return True


def get_binary_content(knowledge_id: str, file_path: str) -> bytes | None:
    """Get raw binary content of a file"""
    full_path = _safe_path(knowledge_id, file_path)
    if full_path is None or not full_path.exists() or full_path.is_dir():
        logger.warning("Binary file not found: KB {}/{}", knowledge_id, file_path)
        return None
    return full_path.read_bytes()
