# api/routes.py

from fastapi import APIRouter, Depends, HTTPException, Query

import pandas as pd
import numpy as np

import json
from pathlib import Path

from api.schemas import (
    QueryRequest,
    QueryResponse,
    QueryListResponse,
)
from api.dependencies import get_query_service
from services.queries_service import QueryService


from core._6_event_dictionary import build_event_dictionary

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def run_query(
    payload: QueryRequest,
    service: QueryService = Depends(get_query_service),
):
    if not payload.src and not payload.dst:
        raise HTTPException(
            status_code=400,
            detail="Debe especificarse al menos src o dst",
        )

    return service.run(payload.src, payload.dst)


# @router.get("/queries", response_model=QueryListResponse)
# def list_queries(
#     service: QueryService = Depends(get_query_service),
# ):
#     return {"queries": service.list_queries()}


# @router.get("/queries")
# def list_queries(service: QueryService = Depends(get_query_service)):
#     return {
#         qid: vars(entry)
#         for qid, entry in service.registry.all().items()
#     }

@router.get("/queries")
def list_queries(service: QueryService = Depends(get_query_service)):
    return service.list_queries()


@router.get("/query/{query_id}")
def get_query(query_id: str, service: QueryService = Depends(get_query_service)):
    queries_dir = Path(service.config["paths"]["output_dir"])
    meta_path = queries_dir / f"{query_id}.json"

    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Query no encontrada")

    with meta_path.open("r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/query/{query_id}/data")
def get_query_data(
    query_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=2000),
    service: QueryService = Depends(get_query_service),
):
    # --------------------------------------------------
    # 1️⃣ Obtener metadata de la query
    # --------------------------------------------------
    entry = service.registry.get(query_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Query no encontrada")

    if not entry.output:
        raise HTTPException(status_code=404, detail="Query sin output")

    parquet_path = Path(entry.output)

    if not parquet_path.exists():
        raise HTTPException(status_code=404, detail="Parquet no encontrado")

    # --------------------------------------------------
    # 2️⃣ Cargar dataset
    # --------------------------------------------------
    df = pd.read_parquet(parquet_path)

    total = len(df)

    # --------------------------------------------------
    # 3️⃣ Aplicar paginación
    # --------------------------------------------------
    df_slice = df.iloc[offset : offset + limit]

    # --------------------------------------------------
    # 4️⃣ Conversión segura a JSON
    # --------------------------------------------------
    records = []
    columns = df_slice.reset_index().columns

    for row in df_slice.reset_index().itertuples(index=False):
        record = {}

        for field, value in zip(columns, row):

            if isinstance(value, (np.integer,)):
                value = int(value)
            elif isinstance(value, (np.floating,)):
                value = float(value)
            elif isinstance(value, (np.ndarray,)):
                value = value.tolist()
            elif isinstance(value, tuple):
                value = list(value)

            record[field] = value

        records.append(record)

    # --------------------------------------------------
    # 5️⃣ Respuesta estructurada
    # --------------------------------------------------
    return {
        "query_id": query_id,
        "total": total,
        "offset": offset,
        "limit": limit,
        "rows": records,
    }



@router.get("/events")
def get_event_dictionary(
    service: QueryService = Depends(get_query_service),
):
    """
    Devuelve el diccionario enriquecido de eventos
    """
    event_dict = build_event_dictionary(service.config)
    return event_dict
