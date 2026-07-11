from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.router import get_current_user, require_admin
from app.knowledge.access_rules import (
    AccessRuleCreate,
    AccessRuleListResponse,
    AccessRuleResponse,
    delete_access_rule,
    get_access_rules,
    set_access_rule,
)
from app.knowledge.models import (
    KnowledgeCreate,
    KnowledgeResponse,
    KnowledgeUpdate,
)
from app.knowledge.permissions import check_access, require_access
from app.knowledge.service import (
    create_knowledge,
    get_knowledge,
    list_knowledge,
    remove_knowledge,
    update_knowledge,
)

router = APIRouter()


@router.get("", response_model=list[KnowledgeResponse])
async def list_knowledge_api(
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]
    is_admin = current_user.get("role") == "admin"
    all_kb = list_knowledge()
    if is_admin:
        return all_kb
    result = []
    for kb in all_kb:
        if await check_access(user_id, kb["id"], "read"):
            result.append(kb)
    return result


@router.post("", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_api(
    knowledge: KnowledgeCreate,
    current_user: dict = Depends(get_current_user),
):
    knowledge_id = knowledge.name.lower().replace(" ", "-")
    try:
        result = create_knowledge(
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

    return result


@router.get("/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge_api(
    knowledge_id: str,
    current_user: dict = Depends(require_access("read")),
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
    current_user: dict = Depends(require_access("write")),
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
    current_user: dict = Depends(require_access("manage")),
):
    if not remove_knowledge(knowledge_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在",
        )
    return {"message": "删除成功"}


# --- Access Rules Management ---


@router.get("/{knowledge_id}/permissions", response_model=AccessRuleListResponse)
async def get_permissions_api(
    knowledge_id: str,
    admin: dict = Depends(require_admin),
):
    rules = await get_access_rules(knowledge_id)
    return AccessRuleListResponse(rules=[AccessRuleResponse(**r) for r in rules])


@router.post("/{knowledge_id}/permissions", response_model=AccessRuleResponse)
async def set_permission_api(
    knowledge_id: str,
    rule: AccessRuleCreate,
    admin: dict = Depends(require_admin),
):
    if rule.access_level not in ("manage", "write", "read", "none"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的权限级别",
        )
    await set_access_rule(knowledge_id, rule.group_id, rule.access_level)
    rules = await get_access_rules(knowledge_id)
    for r in rules:
        if r["knowledge_id"] == knowledge_id and r["group_id"] == rule.group_id:
            return AccessRuleResponse(**r)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="设置权限失败",
    )


@router.delete("/{knowledge_id}/permissions/{rule_id}")
async def delete_permission_api(
    knowledge_id: str,
    rule_id: int,
    admin: dict = Depends(require_admin),
):
    success = await delete_access_rule(rule_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="规则不存在",
        )
    return {"message": "权限已删除"}
