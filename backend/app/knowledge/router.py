from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.router import get_current_user, require_admin
from app.knowledge.models import (
    KnowledgeCreate,
    KnowledgeResponse,
    KnowledgeUpdate,
)
from app.knowledge.permissions import (
    delete_kb_permission,
    get_kb_permissions,
    set_kb_permission,
)
from app.knowledge.service import (
    create_knowledge,
    get_knowledge,
    list_knowledge,
    remove_knowledge,
    update_knowledge,
)

router = APIRouter()


class PermissionRequest(BaseModel):
    user_id: int | None = None  # None = anonymous
    role: str  # "admin", "editor", "viewer"


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


@router.get("/{knowledge_id}/permissions")
async def get_permissions_api(
    knowledge_id: str,
    admin: dict = Depends(require_admin),
):
    permissions = await get_kb_permissions(knowledge_id)
    return {"permissions": permissions}


@router.post("/{knowledge_id}/permissions")
async def set_permission_api(
    knowledge_id: str,
    perm: PermissionRequest,
    admin: dict = Depends(require_admin),
):
    if perm.role not in ("admin", "editor", "viewer"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的角色值",
        )
    await set_kb_permission(knowledge_id, perm.user_id, perm.role)
    return {"message": "权限已设置"}


@router.delete("/{knowledge_id}/permissions/{perm_id}")
async def delete_permission_api(
    knowledge_id: str,
    perm_id: int,
    admin: dict = Depends(require_admin),
):
    success = await delete_kb_permission(perm_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在",
        )
    return {"message": "权限已删除"}
