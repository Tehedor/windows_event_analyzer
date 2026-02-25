# api/routes.py

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.concurrency import run_in_threadpool

import pandas as pd
import numpy as np

from pathlib import Path
from typing import Dict, Any

from api.schemas import QueryRequest, QueryResponse
from api.dependencies import get_query_service
from services.queries_service import QueryService
from config_env import settings_env

router = APIRouter()


# =========================================================
# 🚀 EJECUCIÓN ASÍNCRONA DE QUERY
# =========================================================

@router.post("/query", response_model=QueryResponse)
async def run_query(
    payload: QueryRequest,
    background_tasks: BackgroundTasks,
    service: QueryService = Depends(get_query_service),
):
    """
    1️⃣ Crea metadata en estado 'running'
    2️⃣ Lanza ejecución en background
    3️⃣ Devuelve inmediatamente el query_id
    """

    if not payload.src and not payload.dst:
        raise HTTPException(
            status_code=400,
            detail="Debe especificarse al menos src o dst",
        )

    # 🔹 Crear metadata inicial (running)
    query_id = await run_in_threadpool(
        service.create_query,
        payload.src,
        payload.dst
    )

    # 🔹 Ejecutar en segundo plano
    background_tasks.add_task(service.execute_query, query_id)

    # 🔹 Respuesta inmediata
    return {
        "query_id": query_id,
        "rows": 0,
        "output": None,
        "cached": False,
    }


# =========================================================
# 📋 LISTAR QUERIES
# =========================================================

@router.get("/queries")
async def list_queries(
    service: QueryService = Depends(get_query_service)
):
    return await run_in_threadpool(service.list_queries)


# =========================================================
# 🔍 OBTENER METADATA DE UNA QUERY
# =========================================================

@router.get("/query/{query_id}")
async def get_query(
    query_id: str,
    service: QueryService = Depends(get_query_service),
):
    entry = service.registry.get(query_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Query no encontrada")

    return entry.to_dict()


# =========================================================
# 📊 DATOS PAGINADOS
# =========================================================

@router.get("/query/{query_id}/data")
async def get_query_data(
    query_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=2000),
    service: QueryService = Depends(get_query_service),
):
    entry = service.registry.get(query_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Query no encontrada")

    if entry.status != "done":
        raise HTTPException(status_code=400, detail="Query aún en ejecución")

    if not entry.output:
        raise HTTPException(status_code=404, detail="Query sin output")

    parquet_path = Path(entry.output)

    if not parquet_path.exists():
        raise HTTPException(status_code=404, detail="Parquet no encontrado")

    # --------------------------------------------------
    # Procesamiento pesado → threadpool
    # --------------------------------------------------

    def _process_data() -> Dict[str, Any]:

        df = pd.read_parquet(parquet_path)
        total = len(df)

        df_slice = df.iloc[offset: offset + limit]

        records = []
        columns = df_slice.reset_index().columns

        for row in df_slice.reset_index().itertuples(index=False):
            record = {}

            for field, value in zip(columns, row):

                if isinstance(value, (np.integer, int)):
                    value = int(value)

                elif isinstance(value, (np.floating, float)):
                    value = float(value) if not np.isnan(value) else None

                elif isinstance(value, (np.ndarray, list)):
                    value = value.tolist() if isinstance(value, np.ndarray) else value

                elif isinstance(value, tuple):
                    value = list(value)

                elif pd.isna(value):
                    value = None

                if field == settings_env.OBS_EVENTS_COLUMN:
                    record["obs_events"] = value

                elif field == settings_env.PRED_EVENTS_COLUMN:
                    record["pred_events"] = value

                else:
                    record[field] = value

            records.append(record)

        return {
            "query_id": query_id,
            "total": total,
            "offset": offset,
            "limit": limit,
            "rows": records,
        }

    return await run_in_threadpool(_process_data)


# =========================================================
# 📚 EVENT DICTIONARY
# =========================================================

@router.get("/events")
async def get_event_dictionary(
    service: QueryService = Depends(get_query_service),
):
    return await run_in_threadpool(service.get_event_dictionary)


# =========================================================
# 🧩 COMPONENT DICTIONARY
# =========================================================

@router.get("/componentDict")
async def get_component_dictionary(
    service: QueryService = Depends(get_query_service),
):
    return await run_in_threadpool(service.get_component_dictionary)


@router.get("/componentDictComp")
async def get_component_dictionary_compact(
    service: QueryService = Depends(get_query_service),
):
    return await run_in_threadpool(service.get_component_dictionary_compact)