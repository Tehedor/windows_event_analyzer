# api/schemas.py

from typing import Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    src: Optional[str] = None
    dst: Optional[str] = None


# class QueryResponse(BaseModel):
#     rows: int
#     output: str
class QueryResponse(BaseModel):
    query_id: str
    rows: int
    output: Optional[str] = None
    cached: bool = False

class QueryListResponse(BaseModel):
    queries: list[str]
