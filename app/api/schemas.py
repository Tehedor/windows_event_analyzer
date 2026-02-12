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
    query_id: str      # ✅ AÑADIR ESTE CAMPO
    rows: int
    output: str
    cached: bool = False  # ✅ OPCIONAL pero útil


class QueryListResponse(BaseModel):
    queries: list[str]
