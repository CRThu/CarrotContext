import json
import subprocess
from pathlib import Path

import aiosqlite

from app.config import settings
from app.database import DATABASE_PATH

# Shared SQL constants
_SEARCH_INDEX_SELECT = "SELECT * FROM search_index WHERE title LIKE ? OR tags LIKE ? OR summary LIKE ?"
_SEARCH_INDEX_UPSERT = """INSERT OR REPLACE INTO search_index
               (knowledge_id, file_path, title, tags, summary, content, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, datetime('now'))"""


async def _search_metadata(query: str, limit: int = 20) -> list[dict]:
    """异步BM25搜索元数据"""
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            _SEARCH_INDEX_SELECT,
            (f"%{query}%", f"%{query}%", f"%{query}%"),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows[:limit]]


def search_metadata(query: str, limit: int = 20) -> list[dict]:
    """使用LIKE搜索元数据（同步包装器）"""
    import sqlite3

    try:
        with sqlite3.connect(str(DATABASE_PATH)) as db:
            db.row_factory = sqlite3.Row
            cursor = db.execute(
                _SEARCH_INDEX_SELECT,
                (f"%{query}%", f"%{query}%", f"%{query}%"),
            )
            rows = cursor.fetchmany(limit)
            return [dict(row) for row in rows]
    except Exception:
        return []


def _search_with_grep(query: str, search_path: Path, limit: int) -> list[dict]:
    """使用 grep 命令搜索文件内容（跨平台 fallback）"""
    import re

    results = []
    text_extensions = {
        ".md", ".txt", ".py", ".js", ".ts", ".tsx", ".jsx",
        ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini",
        ".html", ".css", ".scss", ".vue", ".svelte",
        ".sh", ".bash", ".zsh", ".fish",
        ".sql", ".graphql",
        ".java", ".go", ".rs", ".c", ".cpp", ".h", ".hpp",
        ".cs", ".rb", ".php", ".swift", ".kt",
    }

    try:
        for item in search_path.rglob("*"):
            if not item.is_file() or len(results) >= limit:
                break
            if item.suffix.lower() not in text_extensions:
                continue
            if ".git" in item.parts:
                continue

            try:
                content = item.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(content.splitlines(), 1):
                    if re.search(re.escape(query), line, re.IGNORECASE):
                        file_path = str(item.relative_to(search_path))
                        results.append({
                            "file": file_path,
                            "line": i,
                            "content": line.strip()[:200],
                        })
                        if len(results) >= limit:
                            break
            except (OSError, UnicodeDecodeError):
                continue
    except (OSError, PermissionError):
        pass

    return results


def _search_with_rg(query: str, search_path: Path, limit: int) -> list[dict]:
    """使用 ripgrep 搜索文件内容（高性能）"""
    results = []
    cmd = ["rg", "--json", "--max-count", "3", query, str(search_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        try:
            data = json.loads(line)
            if data.get("type") == "match":
                match = data["data"]
                file_path = match["path"]["text"]
                prefix = str(search_path) + ("\\" if "\\" in file_path else "/")
                if file_path.startswith(prefix):
                    file_path = file_path[len(prefix):]
                results.append({
                    "file": file_path,
                    "line": match["line_number"],
                    "content": match["lines"]["text"].strip()[:200],
                })
        except json.JSONDecodeError:
            continue
        if len(results) >= limit:
            break

    return results


def search_content(
    query: str,
    knowledge_id: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """搜索文件内容，优先使用 ripgrep，不可用时降级为 Python grep"""
    search_path = settings.KNOWLEDGE_BASE_PATH
    if knowledge_id:
        search_path = settings.KNOWLEDGE_BASE_PATH / knowledge_id

    if not search_path.exists():
        return []

    try:
        return _search_with_rg(query, search_path, limit)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return _search_with_grep(query, search_path, limit)


def _load_knowledge_manifests() -> list[tuple[str, str, list[str], str, str]]:
    """Load all knowledge manifests from the knowledge base directory.

    Returns list of (knowledge_id, name, tags, summary, description) tuples.
    """
    entries = []
    if not settings.KNOWLEDGE_BASE_PATH.exists():
        return entries

    for knowledge_dir in settings.KNOWLEDGE_BASE_PATH.iterdir():
        if not knowledge_dir.is_dir():
            continue
        manifest_path = knowledge_dir / ".manifest.json"
        if manifest_path.exists():
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
            entries.append((
                knowledge_dir.name,
                manifest.get("name", ""),
                manifest.get("tags", []),
                manifest.get("summary", ""),
                manifest.get("description", ""),
            ))
    return entries


async def _update_search_index(
    knowledge_id: str,
    file_path: str,
    title: str,
    tags: list[str],
    summary: str,
    content: str,
):
    """异步更新搜索索引"""
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute(
            _SEARCH_INDEX_UPSERT,
            (knowledge_id, file_path, title, json.dumps(tags), summary, content),
        )
        await db.commit()


def update_search_index(
    knowledge_id: str,
    file_path: str,
    title: str,
    tags: list[str],
    summary: str,
    content: str,
):
    """更新搜索索引（同步包装器）"""
    import sqlite3

    try:
        with sqlite3.connect(str(DATABASE_PATH)) as db:
            db.execute(
                _SEARCH_INDEX_UPSERT,
                (knowledge_id, file_path, title, json.dumps(tags), summary, content),
            )
            db.commit()
    except Exception:
        pass


async def _rebuild_search_index():
    """异步重建搜索索引"""
    entries = _load_knowledge_manifests()
    async with aiosqlite.connect(str(DATABASE_PATH)) as db:
        await db.execute("DELETE FROM search_index")
        for kb_id, name, tags, summary, description in entries:
            await db.execute(
                _SEARCH_INDEX_UPSERT,
                (kb_id, "", name, json.dumps(tags), summary, description),
            )
        await db.commit()


def rebuild_search_index():
    """重建搜索索引（同步包装器）"""
    import sqlite3

    try:
        entries = _load_knowledge_manifests()
        with sqlite3.connect(str(DATABASE_PATH)) as db:
            db.execute("DELETE FROM search_index")
            for kb_id, name, tags, summary, description in entries:
                db.execute(
                    _SEARCH_INDEX_UPSERT,
                    (kb_id, "", name, json.dumps(tags), summary, description),
                )
            db.commit()
    except Exception:
        pass
