from fastapi import APIRouter, Depends, HTTPException

from app.auth.router import get_current_user
from app.git.models import (
    GitCommitRequest,
    GitCommitResponse,
    GitRevertRequest,
)
from app.git.service import (
    create_git_commit,
    get_git_diff,
    get_git_log,
    init_git,
    revert_git_commit,
)

router = APIRouter()


@router.post("/{knowledge_id}/init")
async def init_git_api(
    knowledge_id: str,
    current_user: dict = Depends(get_current_user),
):
    if not init_git(knowledge_id):
        raise HTTPException(status_code=404, detail="知识库不存在")
    return {"message": "Git初始化成功"}


@router.get("/{knowledge_id}/log")
async def get_log_api(
    knowledge_id: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
):
    return get_git_log(knowledge_id, limit)


@router.get("/{knowledge_id}/diff")
async def get_diff_api(
    knowledge_id: str,
    file_path: str | None = None,
    commit: str | None = None,
    current_user: dict = Depends(get_current_user),
):
    return {"diff": get_git_diff(knowledge_id, file_path, commit)}


@router.post(
    "/{knowledge_id}/commit",
    response_model=GitCommitResponse,
)
async def commit_api(
    knowledge_id: str,
    request: GitCommitRequest,
    current_user: dict = Depends(get_current_user),
):
    result = create_git_commit(
        knowledge_id, request.message, request.file_path
    )
    if not result:
        raise HTTPException(status_code=400, detail="提交失败")
    return result


@router.post("/{knowledge_id}/revert")
async def revert_api(
    knowledge_id: str,
    request: GitRevertRequest,
    current_user: dict = Depends(get_current_user),
):
    if not revert_git_commit(knowledge_id, request.commit_hash):
        raise HTTPException(status_code=400, detail="回滚失败")
    return {"message": "回滚成功"}
