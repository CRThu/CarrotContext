from datetime import datetime

from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    role: str = "user"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None
    user_id: int | None = None


class UserUpdateRole(BaseModel):
    role: str  # "admin" or "user"


class UserListResponse(BaseModel):
    users: list[UserResponse]
