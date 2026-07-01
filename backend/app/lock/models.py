from pydantic import BaseModel


class LockRequest(BaseModel):
    knowledge_id: str
    file_path: str


class LockResponse(BaseModel):
    success: bool
    locked_by: str | None = None
    locked_at: str | None = None
    message: str = ""


class LockStatus(BaseModel):
    knowledge_id: str
    file_path: str
    locked: bool
    locked_by: str | None = None
    locked_at: str | None = None
