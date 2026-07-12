import asyncio

from fastapi import APIRouter, Depends, HTTPException

from app.knowledge.permissions import require_access
from app.git.models import (
    GitCommitRequest,
    GitCommitResponse,
    GitRevertRequest,
)
from app.git.service import (
    create_git_commit,
    get_file_at_commit,
    get_git_diff,
    get_git_log,
    init_git,
    revert_git_commit,
)

router = APIRouter()


@router.post("/{knowledge_id}/init")
async def init_git_api(
    knowledge_id: str,
    current_user: dict = Depends(require_access("write")),
):
    result = await asyncio.to_thread(init_git, knowledge_id)
    if not result:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return {"message": "Git初始化成功"}


@router.get("/{knowledge_id}/log")
async def get_log_api(
    knowledge_id: str,
    limit: int = 10,
    file_path: str | None = None,
    current_user: dict = Depends(require_access("read")),
):
    return await asyncio.to_thread(get_git_log, knowledge_id, limit, file_path)


@router.get("/{knowledge_id}/diff")
async def get_diff_api(
    knowledge_id: str,
    file_path: str | None = None,
    commit: str | None = None,
    current_user: dict = Depends(require_access("read")),
):
    diff = await asyncio.to_thread(get_git_diff, knowledge_id, file_path, commit)
    return {"diff": diff}


@router.get("/{knowledge_id}/file-at-commit")
async def get_file_at_commit_api(
    knowledge_id: str,
    commit: str,
    path: str,
    current_user: dict = Depends(require_access("read")),
):
    content = await asyncio.to_thread(get_file_at_commit, knowledge_id, commit, path)
    if content is None:
        raise HTTPException(status_code=404, detail="文件或提交不存在")
    return {"content": content}


@router.post(
    "/{knowledge_id}/commit",
    response_model=GitCommitResponse,
)
async def commit_api(
    knowledge_id: str,
    request: GitCommitRequest,
    current_user: dict = Depends(require_access("write")),
):
    result = await asyncio.to_thread(
        create_git_commit, knowledge_id, request.message, request.file_path
    )
    if not result:
        raise HTTPException(status_code=400, detail="提交失败")
    return result


@router.post("/{knowledge_id}/revert")
async def revert_api(
    knowledge_id: str,
    request: GitRevertRequest,
    current_user: dict = Depends(require_access("write")),
):
    result = await asyncio.to_thread(revert_git_commit, knowledge_id, request.commit_hash)
    if not result:
        raise HTTPException(status_code=400, detail="回滚失败")
    return {"message": "回滚成功"}
