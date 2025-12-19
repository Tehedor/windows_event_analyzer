# api/dependencies.py

from services.queries_service import QueryService

_query_service: QueryService | None = None


def get_query_service() -> QueryService:
    global _query_service

    if _query_service is None:
        _query_service = QueryService()

    return _query_service
