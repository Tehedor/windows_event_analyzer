# api/routes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool

import pandas as pd
import numpy as np

import json
from pathlib import Path
from typing import List, Dict, Any

from api.schemas import (
    QueryRequest,
    QueryResponse,
    # QueryListResponse, # Descomentar si usas schemas de lista
)
from api.dependencies import get_query_service
from services.queries_service import QueryService
from core._6_event_dictionary import build_event_dictionary

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def run_query(
    payload: QueryRequest,
    service: QueryService = Depends(get_query_service),
):
    """
    Ejecuta una consulta.
    Usa run_in_threadpool para no bloquear el servidor mientras calcula.
    """
    if not payload.src and not payload.dst:
        raise HTTPException(
            status_code=400,
            detail="Debe especificarse al menos src o dst",
        )

    # service.run puede tardar, así que lo ejecutamos en un hilo aparte
    return await run_in_threadpool(service.run, payload.src, payload.dst)


@router.get("/queries")
async def list_queries(service: QueryService = Depends(get_query_service)):
    """
    Lista las consultas disponibles.
    Async para mantener consistencia, aunque sea una operación rápida.
    """
    return await run_in_threadpool(service.list_queries)


@router.get("/query/{query_id}")
async def get_query(
    query_id: str, 
    service: QueryService = Depends(get_query_service)
):
    """
    Lee los metadatos de una consulta (JSON).
    La lectura de disco se mueve a un hilo secundario.
    """
    queries_dir = Path(service.config["paths"]["output_dir"])
    meta_path = queries_dir / f"{query_id}.json"

    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Query no encontrada")

    def _read_json():
        with meta_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    return await run_in_threadpool(_read_json)


@router.get("/query/{query_id}/data")
async def get_query_data(
    query_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=2000),
    service: QueryService = Depends(get_query_service),
):
    """
    Obtiene los datos del parquet paginados.
    CRÍTICO: Pandas bloquea el CPU y el IO. Toda la lógica de lectura y
    procesamiento se encapsula en _process_data y se envía al threadpool.
    """
    # 1️⃣ Validaciones ligeras (se mantienen en el main thread)
    entry = service.registry.get(query_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Query no encontrada")

    if not entry.output:
        raise HTTPException(status_code=404, detail="Query sin output")

    parquet_path = Path(entry.output)

    if not parquet_path.exists():
        raise HTTPException(status_code=404, detail="Parquet no encontrado")

    # 2️⃣ Definir función bloqueante (IO + CPU intensivo)
    def _process_data() -> Dict[str, Any]:
        # Cargar dataset (IO Bound)
        df = pd.read_parquet(parquet_path)
        total = len(df)

        # Aplicar paginación (CPU Bound - memoria)
        df_slice = df.iloc[offset : offset + limit]

        # Conversión segura a JSON (CPU Bound - iteración)
        records = []
        columns = df_slice.reset_index().columns
        
        # Iterar eficientemente
        # Nota: iterrows o itertuples sigue siendo "lento" en Python puro,
        # pero al estar en un hilo aparte, no bloquea al resto de usuarios.
        for row in df_slice.reset_index().itertuples(index=False):
            record = {}
            for field, value in zip(columns, row):
                # Sanitización de tipos de NumPy para JSON estándar
                if isinstance(value, (np.integer, int)):
                    value = int(value)
                elif isinstance(value, (np.floating, float)):
                    value = float(value) if not np.isnan(value) else None
                elif isinstance(value, (np.ndarray, list)):
                    value = value.tolist() if isinstance(value, np.ndarray) else value
                elif isinstance(value, tuple):
                    value = list(value)
                # Manejo de NaNs generales
                elif pd.isna(value):
                    value = None
                
                record[field] = value
            records.append(record)
            
        return {
            "query_id": query_id,
            "total": total,
            "offset": offset,
            "limit": limit,
            "rows": records,
        }

    # 3️⃣ Ejecutar en Threadpool y esperar resultado sin bloquear
    return await run_in_threadpool(_process_data)


@router.get("/events")
async def get_event_dictionary(
    service: QueryService = Depends(get_query_service),
):
    """
    Devuelve el diccionario enriquecido de eventos.
    Usa caché interno del servicio para evitar reconstruirlo en cada request.
    """
    return await run_in_threadpool(service.get_event_dictionary)



@router.get("/componentDict")
async def get_component_dictionary(
    service: QueryService = Depends(get_query_service),
):
    """
    Devuelve el diccionario completo de componentes.
    """
    return await run_in_threadpool(service.get_component_dictionary)


@router.get("/componentDictComp")
async def get_component_dictionary_compact(
    service: QueryService = Depends(get_query_service),
):
    """
    Devuelve el diccionario compacto de componentes.
    """
    return await run_in_threadpool(service.get_component_dictionary_compact)
