from fastapi import APIRouter, Depends, Query
from app.auth.router import get_current_user
from app.search.service import search_metadata, search_content

router = APIRouter()


@router.get("")
async def search_api(
    q: str = Query(..., description="搜索关键词"),
    mode: str = Query("all", description="搜索模式: all, metadata, content"),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    results = []
    if mode in ("all", "metadata"):
        metadata_results = search_metadata(q, limit)
        for r in metadata_results:
            results.append({
                "knowledge_id": r.get("knowledge_id", ""),
                "file_path": r.get("file_path", ""),
                "title": r.get("title", ""),
                "score": 1.0,
                "snippet": r.get("summary", ""),
            })

    if mode in ("all", "content"):
        content_results = search_content(q, limit=limit)
        for r in content_results:
            results.append({
                "knowledge_id": "",
                "file_path": r.get("file", ""),
                "title": "",
                "score": 0.8,
                "snippet": r.get("content", ""),
            })

    return {"results": results[:limit], "total": len(results)}
