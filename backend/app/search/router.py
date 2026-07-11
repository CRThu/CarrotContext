from fastapi import APIRouter, Depends, Query

from app.auth.router import get_current_user
from app.knowledge.permissions import check_access
from app.search.service import search_content, search_metadata

router = APIRouter()


@router.get("")
async def search_api(
    q: str = Query(..., description="搜索关键词"),
    mode: str = Query("all", description="搜索模式: all, metadata, content"),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]
    results = []

    # Cache permission checks per knowledge_id
    perm_cache: dict[str, bool] = {}

    async def has_access(kb_id: str) -> bool:
        if kb_id not in perm_cache:
            perm_cache[kb_id] = await check_access(user_id, kb_id, "read")
        return perm_cache[kb_id]

    if mode in ("all", "metadata"):
        metadata_results = search_metadata(q, limit)
        for r in metadata_results:
            kb_id = r.get("knowledge_id", "")
            if kb_id and await has_access(kb_id):
                results.append({
                    "knowledge_id": kb_id,
                    "file_path": r.get("file_path", ""),
                    "title": r.get("title", ""),
                    "score": 1.0,
                    "snippet": r.get("summary", ""),
                })

    if mode in ("all", "content"):
        content_results = search_content(q, limit=limit)
        for r in content_results:
            file_path = r.get("file", "")
            # Extract knowledge_id from file path (first component)
            kb_id = file_path.split("/")[0] if "/" in file_path else ""
            if kb_id and await has_access(kb_id):
                results.append({
                    "knowledge_id": kb_id,
                    "file_path": file_path,
                    "title": "",
                    "score": 0.8,
                    "snippet": r.get("content", ""),
                })

    return {"results": results[:limit], "total": len(results)}
