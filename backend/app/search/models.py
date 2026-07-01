from pydantic import BaseModel


class SearchResult(BaseModel):
    knowledge_id: str
    file_path: str
    title: str
    score: float
    snippet: str


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
