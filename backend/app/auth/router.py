from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.models import UserCreate, LoginRequest, UserResponse, Token
from app.auth.service import (
    create_user,
    authenticate_user,
    create_access_token,
    get_user_by_id,
    decode_token,
    get_user_by_username,
)

router = APIRouter()
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_data = await decode_token(credentials.credentials)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的token")
    user = await get_user_by_id(token_data["user_id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    existing_user = await get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    created_user = await create_user(user.username, user.email, user.password)
    return created_user


@router.post("/login", response_model=Token)
async def login(user: LoginRequest):
    authenticated_user = await authenticate_user(user.username, user.password)
    if not authenticated_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    access_token = create_access_token(data={"sub": authenticated_user["username"], "user_id": authenticated_user["id"]})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
