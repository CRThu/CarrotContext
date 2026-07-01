import subprocess
import json
from pathlib import Path
from app.config import settings


def search_metadata(query: str, limit: int = 20) -> list[dict]:
    """使用BM25搜索元数据"""
    try:
        import aiosqlite
        import asyncio

        async def _search():
            async with aiosqlite.connect("./data/carrotcontext.db") as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM search_index WHERE title LIKE ? OR tags LIKE ? OR summary LIKE ?",
                    (f"%{query}%", f"%{query}%", f"%{query}%"),
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows[:limit]]

        return asyncio.run(_search())
    except Exception:
        return []


def search_content(query: str, knowledge_id: str | None = None, limit: int = 20) -> list[dict]:
    """使用ripgrep搜索文件内容"""
    search_path = settings.KNOWLEDGE_BASE_PATH
    if knowledge_id:
        search_path = settings.KNOWLEDGE_BASE_PATH / knowledge_id

    if not search_path.exists():
        return []

    try:
        cmd = ["rg", "--json", "--max-count", "3", query, str(search_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        results = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                if data.get("type") == "match":
                    match = data["data"]
                    results.append({
                        "file": match["path"]["text"].replace(str(search_path) + "\\", ""),
                        "line": match["line_number"],
                        "content": match["lines"]["text"].strip(),
                    })
            except json.JSONDecodeError:
                continue
        return results[:limit]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def update_search_index(knowledge_id: str, file_path: str, title: str, tags: list[str], summary: str, content: str):
    """更新搜索索引"""
    import aiosqlite
    import asyncio
    import json

    async def _update():
        async with aiosqlite.connect("./data/carrotcontext.db") as db:
            await db.execute(
                """INSERT OR REPLACE INTO search_index 
                   (knowledge_id, file_path, title, tags, summary, content, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                (knowledge_id, file_path, title, json.dumps(tags), summary, content),
            )
            await db.commit()

    asyncio.run(_update())


def rebuild_search_index():
    """重建搜索索引"""
    import aiosqlite
    import asyncio
    import json

    async def _rebuild():
        async with aiosqlite.connect("./data/carrotcontext.db") as db:
            await db.execute("DELETE FROM search_index")

            if not settings.KNOWLEDGE_BASE_PATH.exists():
                return

            for knowledge_dir in settings.KNOWLEDGE_BASE_PATH.iterdir():
                if not knowledge_dir.is_dir():
                    continue
                manifest_path = knowledge_dir / ".manifest.json"
                if manifest_path.exists():
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                    await db.execute(
                        """INSERT OR REPLACE INTO search_index 
                           (knowledge_id, file_path, title, tags, summary, content, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                        (
                            knowledge_dir.name,
                            "",
                            manifest.get("name", ""),
                            json.dumps(manifest.get("tags", [])),
                            manifest.get("summary", ""),
                            manifest.get("description", ""),
                        ),
                    )

            await db.commit()

    asyncio.run(_rebuild())
