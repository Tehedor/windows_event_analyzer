# services/queries_service.py

import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import threading
import gc

from core._1_config_loader import load_config
from core._2_preprocessor import load_or_preprocess_dataset
from core._3_input_controller import parse_pattern
from core._4_query_engine import run_query
from core._5_output_writer import save_results
from core._7_component_dictionary import (
    build_component_dictionary,
    build_component_dictionary_compact,
)

from state.registry import query_registry, QueryStatus
from state.locks import QueryLockManager

from debug.debug import save_debug_info


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _make_query_id(src: Optional[str], dst: Optional[str]) -> str:
    raw = f"src={src or ''}|dst={dst or ''}"
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def _write_query_metadata(entry) -> None:
    if not entry.output:
        return

    parquet_path = Path(entry.output)
    meta_path = parquet_path.with_suffix(".json")

    meta_path.parent.mkdir(parents=True, exist_ok=True)

    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(entry.to_dict(), f, indent=2)


# -------------------------------------------------------------------------
# Service
# -------------------------------------------------------------------------

class QueryService:

    def __init__(self):
        self.config = load_config()
        save_debug_info(self.config, filename="config_debug", head="Configuración cargada")

        self._df = None
        self._event_dict = None

        # timer
        self._ram_timeout = self.config.get("ram_timeout", 0)
        self._timer: Optional[threading.Timer] = None

        self._component_dict = build_component_dictionary(self.config)
        self._component_dict_compact = build_component_dictionary_compact(self.config)

        self.config["components"] = self._component_dict_compact["components"]

        self.registry = query_registry
        self.locks = QueryLockManager()

        self._load_existing_queries()

    # -------------------------------------------------------
    # Public API usada por routes.py
    # -------------------------------------------------------
    def create_query(self, src: Optional[str], dst: Optional[str]) -> str:
        query_id = _make_query_id(src, dst)

        entry = self.registry.get(query_id)
        
        # 🚀 PROTECCIÓN: Si ya existe y está DONE o RUNNING → no hacemos NADA, devolvemos el ID
        if entry and entry.status in (QueryStatus.DONE, QueryStatus.RUNNING):
            return query_id

        self.registry.create(
            query_id=query_id,
            src_raw=src,
            dst_raw=dst,
            src=None,
            dst=None,
        )

        self.registry.update(query_id, status=QueryStatus.RUNNING)

        return query_id

    def execute_query(self, query_id: str) -> None:

        entry = self.registry.get(query_id)
        if not entry:
            return

        lock = self.locks.acquire(query_id)

        with lock:
            try:
                src = entry.src_raw
                dst = entry.dst_raw

                src_pattern = parse_pattern(src, "observation", self.config) if src else None
                dst_pattern = parse_pattern(dst, "prediction", self.config) if dst else None

                df = self._get_dataset()

                result_df = run_query(
                    df,
                    src_pattern,
                    dst_pattern,
                    self.config,
                )

                paths = save_results(
                    result_df,
                    src_pattern,
                    dst_pattern,
                    self.config,
                )

                parquet_path = paths[0] if paths else None

                self.registry.update(
                    query_id,
                    status=QueryStatus.DONE,
                    rows=len(result_df),
                    output=str(parquet_path) if parquet_path else None,
                )

                final_entry = self.registry.get(query_id)
                _write_query_metadata(final_entry)

            except Exception as e:
                import traceback
                traceback.print_exc()

                self.registry.update(
                    query_id,
                    status=QueryStatus.ERROR,
                    error=str(e),
                )

    def list_queries(self) -> list[dict]:
        return [entry.to_dict() for entry in self.registry.all().values()]

    # -------------------------------------------------------
    # Diccionarios
    # -------------------------------------------------------

    def get_component_dictionary(self) -> Dict[str, Any]:
        return self._component_dict

    def get_component_dictionary_compact(self) -> Dict[str, Any]:
        return self._component_dict_compact

    def get_event_dictionary(self) -> Dict[str, Any]:
        if self._event_dict is None:
            from core._6_event_dictionary import build_event_dictionary
            self._event_dict = build_event_dictionary(self.config)
        return self._event_dict

    # -------------------------------------------------------
    # Internals
    # -------------------------------------------------------
    def _load_existing_queries(self) -> None:
        queries_dir = Path(self.config["paths"]["output_dir"])

        if not queries_dir.exists():
            return

        entries = {}

        for meta_file in queries_dir.glob("*.json"):
            try:
                with meta_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                # 🔥 CLAVE: reconstruir QueryEntry correctamente
                from state.registry import QueryEntry
                entry = QueryEntry.from_dict(data)

                entries[entry.query_id] = entry

            except Exception as e:
                print(f"[WARN] No se pudo cargar {meta_file.name}: {e}")

        self.registry.load_from_disk(entries)
    
    # -------------------------------------------------------
    # Dataset lazy-load
    # -------------------------------------------------------
    def _get_dataset(self):
        if self._df is None:
            print("📦 Cargando dataset en memoria...")
            self._df = load_or_preprocess_dataset(self.config)
        self._reset_timer()
        return self._df
    


    def _reset_timer(self):
        """Reinicia el contador para liberar la RAM. Si es <= 0, es infinito."""
        if self._ram_timeout <= 0:
            return  # Configurado como indefinido, no hacemos nada

        # Si ya había un temporizador corriendo, lo cancelamos
        if self._timer is not None:
            self._timer.cancel()

        # Creamos y lanzamos uno nuevo
        self._timer = threading.Timer(self._ram_timeout, self._clear_dataset)
        self._timer.start()

    def _clear_dataset(self):
        """Libera el dataset de la RAM tras un periodo de inactividad."""
        if self._df is not None:
            print(f"🧹 Tiempo de inactividad superado ({self._ram_timeout}s). Liberando dataset de la RAM...")
            self._df = None
            gc.collect()  # Forzamos la recolección de basura para limpiar la memoria inmediatamente