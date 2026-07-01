from datetime import datetime
from pydantic import BaseModel


class KnowledgeCreate(BaseModel):
    name: str
    description: str = ""
    tags: list[str] = []


class KnowledgeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    summary: str | None = None


class KnowledgeResponse(BaseModel):
    id: str
    name: str
    description: str
    created_by: str
    created_at: str
    updated_by: str
    updated_at: str
    tags: list[str]
    summary: str
    version: int


class TreeNode(BaseModel):
    name: str
    path: str
    is_dir: bool
    children: list["TreeNode"] = []


class FileContent(BaseModel):
    path: str
    content: str
    size: int
    modified_at: str
