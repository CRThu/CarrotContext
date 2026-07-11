from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.models import (
    GroupCreate,
    GroupListResponse,
    GroupMemberRequest,
    GroupMemberResponse,
    GroupResponse,
    LoginRequest,
    Token,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdateRole,
)
from app.auth.service import (
    add_user_to_group,
    authenticate_user,
    create_access_token,
    create_group,
    create_user,
    delete_group,
    delete_user,
    get_all_groups,
    get_all_users,
    get_current_user_from_token,
    get_group,
    get_group_members,
    get_user_by_id,
    get_user_by_username,
    remove_user_from_group,
    update_user_role,
)

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user = await get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token或用户不存在",
        )
    return user


async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    existing_user = await get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    created_user = await create_user(user.username, user.email, user.password)
    return created_user


@router.post("/login", response_model=Token)
async def login(user: LoginRequest):
    authenticated_user = await authenticate_user(user.username, user.password)
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    access_token = create_access_token(
        data={
            "sub": authenticated_user["username"],
            "user_id": authenticated_user["id"],
        }
    )
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=UserListResponse)
async def list_users(admin: dict = Depends(require_admin)):
    users = await get_all_users()
    return UserListResponse(users=users)


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: int,
    role_update: UserUpdateRole,
    admin: dict = Depends(require_admin),
):
    if role_update.role not in ("admin", "user"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的角色值",
        )
    if user_id == admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的角色",
        )
    user = await update_user_role(user_id, role_update.role)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return user


@router.delete("/users/{user_id}")
async def remove_user(
    user_id: int,
    admin: dict = Depends(require_admin),
):
    if user_id == admin["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己",
        )
    success = await delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return {"message": "用户已删除"}


# --- Group Management ---


@router.get("/groups", response_model=GroupListResponse)
async def list_groups(admin: dict = Depends(require_admin)):
    groups = await get_all_groups()
    return GroupListResponse(groups=groups)


@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group_api(
    group: GroupCreate,
    admin: dict = Depends(require_admin),
):
    existing = await get_all_groups()
    for g in existing:
        if g["name"] == group.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="组名已存在",
            )
    return await create_group(group.name, group.description)


@router.delete("/groups/{group_id}")
async def delete_group_api(
    group_id: int,
    admin: dict = Depends(require_admin),
):
    success = await delete_group(group_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组不存在",
        )
    return {"message": "组已删除"}


@router.get("/groups/{group_id}/members", response_model=list[GroupMemberResponse])
async def list_group_members(
    group_id: int,
    admin: dict = Depends(require_admin),
):
    group = await get_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组不存在",
        )
    return await get_group_members(group_id)


@router.post("/groups/{group_id}/members", response_model=GroupMemberResponse)
async def add_group_member(
    group_id: int,
    member: GroupMemberRequest,
    admin: dict = Depends(require_admin),
):
    group = await get_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="组不存在",
        )
    user = await get_user_by_id(member.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    success = await add_user_to_group(member.user_id, group_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已在该组中",
        )
    return GroupMemberResponse(user_id=user["id"], username=user["username"])


@router.delete("/groups/{group_id}/members/{user_id}")
async def remove_group_member(
    group_id: int,
    user_id: int,
    admin: dict = Depends(require_admin),
):
    success = await remove_user_from_group(user_id, group_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不在该组中",
        )
    return {"message": "已从组中移除"}
