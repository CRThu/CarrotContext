import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.config import settings


def get_lock_path(knowledge_id: str, file_path: str) -> Path:
    knowledge_path = settings.KNOWLEDGE_BASE_PATH / knowledge_id
    lock_dir = knowledge_path / ".locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    safe_name = file_path.replace("/", "_").replace("\\", "_")
    return lock_dir / f"{safe_name}.lock"


def acquire_lock(
    knowledge_id: str, file_path: str, username: str
) -> dict:
    """获取文件锁"""
    lock_path = get_lock_path(knowledge_id, file_path)

    if lock_path.exists():
        try:
            with open(lock_path, encoding="utf-8") as f:
                lock_data = json.load(f)
            lock_time = datetime.fromisoformat(lock_data["locked_at"])
            timeout = timedelta(minutes=settings.LOCK_TIMEOUT_MINUTES)
            if datetime.now(UTC) - lock_time < timeout:
                return {
                    "success": False,
                    "locked_by": lock_data["username"],
                    "locked_at": lock_data["locked_at"],
                }
        except (json.JSONDecodeError, KeyError):
            pass

    lock_data = {
        "username": username,
        "file_path": file_path,
        "locked_at": datetime.now(UTC).isoformat(),
    }
    with open(lock_path, "w", encoding="utf-8") as f:
        json.dump(lock_data, f, ensure_ascii=False, indent=2)
    return {
        "success": True,
        "locked_by": username,
        "locked_at": lock_data["locked_at"],
    }


def release_lock(
    knowledge_id: str, file_path: str, username: str
) -> bool:
    """释放文件锁"""
    lock_path = get_lock_path(knowledge_id, file_path)
    if not lock_path.exists():
        return False

    try:
        with open(lock_path, encoding="utf-8") as f:
            lock_data = json.load(f)
        if lock_data.get("username") != username:
            return False
    except (json.JSONDecodeError, KeyError):
        pass

    lock_path.unlink()
    return True


def get_lock_status(
    knowledge_id: str, file_path: str
) -> dict | None:
    """获取锁状态"""
    lock_path = get_lock_path(knowledge_id, file_path)
    if not lock_path.exists():
        return None

    try:
        with open(lock_path, encoding="utf-8") as f:
            lock_data = json.load(f)
        lock_time = datetime.fromisoformat(lock_data["locked_at"])
        timeout = timedelta(minutes=settings.LOCK_TIMEOUT_MINUTES)
        if datetime.now(UTC) - lock_time >= timeout:
            lock_path.unlink()
            return None
        return lock_data
    except (json.JSONDecodeError, KeyError):
        return None
