from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.auth.router import get_current_user
from app.knowledge.models import (
    FileContent,
    KnowledgeCreate,
    KnowledgeResponse,
    KnowledgeUpdate,
    TreeNode,
)
from app.knowledge.service import (
    create_directory,
    create_knowledge,
    get_file_content,
    get_file_tree,
    get_knowledge,
    list_knowledge,
    remove_knowledge,
    update_file_content,
    update_knowledge,
)

router = APIRouter()


@router.get("", response_model=list[KnowledgeResponse])
async def list_knowledge_api(
    current_user: dict = Depends(get_current_user),
):
    return list_knowledge()


@router.post("", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_api(
    knowledge: KnowledgeCreate,
    current_user: dict = Depends(get_current_user),
):
    knowledge_id = knowledge.name.lower().replace(" ", "-")
    try:
        return create_knowledge(
            knowledge_id,
            knowledge.name,
            knowledge.description,
            knowledge.tags,
            current_user["username"],
            knowledge.category,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge_api(
    knowledge_id: str,
    current_user: dict = Depends(get_current_user),
):
    knowledge = get_knowledge(knowledge_id)
    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在",
        )
    return knowledge


@router.put("/{knowledge_id}", response_model=KnowledgeResponse)
async def update_knowledge_api(
    knowledge_id: str,
    knowledge: KnowledgeUpdate,
    current_user: dict = Depends(get_current_user),
):
    updates = knowledge.model_dump(exclude_unset=True)
    result = update_knowledge(knowledge_id, updates, current_user["username"])
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在",
        )
    return result


@router.delete("/{knowledge_id}")
async def delete_knowledge_api(
    knowledge_id: str,
    current_user: dict = Depends(get_current_user),
):
    if not remove_knowledge(knowledge_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在",
        )
    return {"message": "删除成功"}


@router.get("/{knowledge_id}/tree", response_model=list[TreeNode])
async def get_tree_api(
    knowledge_id: str,
    path: str = "",
    current_user: dict = Depends(get_current_user),
):
    return get_file_tree(knowledge_id, path)


@router.get(
    "/{knowledge_id}/file/{file_path:path}",
    response_model=FileContent,
)
async def get_file_api(
    knowledge_id: str,
    file_path: str,
    current_user: dict = Depends(get_current_user),
):
    content = get_file_content(knowledge_id, file_path)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在",
        )
    return content


@router.put("/{knowledge_id}/file/{file_path:path}")
async def update_file_api(
    knowledge_id: str,
    file_path: str,
    content: str = Body(..., media_type="text/plain"),
    current_user: dict = Depends(get_current_user),
):
    if not update_file_content(knowledge_id, file_path, content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新失败",
        )
    return {"message": "更新成功"}


@router.post("/{knowledge_id}/directory")
async def create_dir_api(
    knowledge_id: str,
    dir_path: str,
    current_user: dict = Depends(get_current_user),
):
    if not create_directory(knowledge_id, dir_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="目录已存在",
        )
    return {"message": "创建成功"}
