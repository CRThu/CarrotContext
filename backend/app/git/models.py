from pydantic import BaseModel


class GitCommitRequest(BaseModel):
    message: str
    file_path: str | None = None


class GitRevertRequest(BaseModel):
    commit_hash: str


class GitCommitResponse(BaseModel):
    hash: str
    author: str
    email: str
    date: str
    message: str
