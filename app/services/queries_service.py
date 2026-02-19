# services/queries_service.py

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

from core._1_config_loader import load_config
from core._2_preprocessor import load_or_preprocess_dataset
from core._3_input_controller import QueryPattern, parse_pattern
from core._4_query_engine import run_query
from core._5_output_writer import save_results
from core._7_component_dictionary import build_component_dictionary, build_component_dictionary_compact

# Importamos la instancia GLOBAL 'query_registry'
from state.registry import query_registry, QueryStatus, QueryEntry
from state.locks import QueryLockManager

from debug.debug import save_debug_info

# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _make_query_id(src: Optional[QueryPattern], dst: Optional[QueryPattern]) -> str:
    # Genera un ID único basado en el contenido canónico
    raw = f"src={src.canonical if src else ''}|dst={dst.canonical if dst else ''}"
    return hashlib.sha1(raw.encode()).hexdigest()[:12]

def _write_query_metadata(entry) -> None:
    if not entry.output:
        return

    # output puede ser string o lista, normalizamos
    if isinstance(entry.output, list):
        if not entry.output: return
        parquet_path = Path(entry.output[0])
    else:
        parquet_path = Path(entry.output)

    meta_path = parquet_path.with_suffix(".json")
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(meta_path.parent, 0o777)
    for parent in meta_path.parent.parents:
        try:
            os.chmod(parent, 0o777)
        except:
            pass

    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(entry.to_dict(), f, indent=2)
    
    os.chmod(meta_path, 0o666)


# -------------------------------------------------------------------------
# Service
# -------------------------------------------------------------------------

class QueryService:

    def __init__(self):
        self.config = load_config()
        save_debug_info(self.config, filename="config_debug", head="Configuración cargada")
        
        self._df = None
        self._event_dict = None  

        try:
            self._component_dict = build_component_dictionary(self.config)
            self._component_dict_compact = build_component_dictionary_compact(self.config)
            self.config["components"] = self._component_dict_compact["components"]
        except Exception as e:
            print(f"⚠️ Error generando component dictionary: {e}")

        # Guardamos debug info
        save_debug_info(self._component_dict, filename="component_dictionary_debug.json", head="Component Dictionary")
        
        # Usamos la instancia GLOBAL del registry para mantener estado
        self.registry = query_registry
        self.locks = QueryLockManager()

        # Cargamos estado previo
        self._load_existing_queries()

    def get_component_dictionary(self) -> Dict[str, Any]:
        return self._component_dict

    def get_component_dictionary_compact(self) -> Dict[str, Any]:
        return self._component_dict_compact

    def get_event_dictionary(self) -> Dict[str, Any]:
        if self._event_dict is None:
            print("📚 Cargando event dictionary...")
            from core._6_event_dictionary import build_event_dictionary
            self._event_dict = build_event_dictionary(self.config)
        return self._event_dict

    def _load_existing_queries(self) -> None:
        queries_dir = Path(self.config["paths"]["output_dir"])

        if not queries_dir.exists():
            return

        entries: Dict[str, QueryEntry] = {}

        for meta_file in queries_dir.glob("*.json"):
            try:
                with meta_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                entry = QueryEntry.from_dict(data)
                entries[entry.query_id] = entry

            except Exception as e:
                print(f"[WARN] No se pudo cargar {meta_file.name}: {e}")

        # Cargamos en el registro global
        self.registry.load_from_disk(entries)

    def _get_dataset(self):
        if self._df is None:
            print("📦 Cargando dataset en memoria...")
            self._df = load_or_preprocess_dataset(self.config)
        return self._df

    def list_queries(self) -> list[dict]:
        # Retorna el estado actual en memoria
        return [entry.to_dict() for entry in self.registry.all().values()]

    def run(self, src: Optional[str], dst: Optional[str]) -> Dict[str, Any]:
        
        src_pattern = parse_pattern(src, "observation", self.config) if src else None
        dst_pattern = parse_pattern(dst, "prediction", self.config) if dst else None

        query_id = _make_query_id(src_pattern, dst_pattern)
        lock = self.locks.acquire(query_id)

        with lock:
            # 1. Chequear caché en memoria
            entry = self.registry.get(query_id)
            if entry and entry.status == QueryStatus.DONE:
                return {
                    "query_id": query_id,
                    "rows": entry.rows,
                    "output": entry.output,
                    "cached": True,
                }

            # 2. Crear nueva entrada
            entry = self.registry.create(
                query_id=query_id,
                src_raw=src,
                dst_raw=dst,
                src=src_pattern.canonical if src_pattern else None,
                dst=dst_pattern.canonical if dst_pattern else None,
            )

            self.registry.update(query_id, status=QueryStatus.RUNNING)

            try:
                df = self._get_dataset()

                result_df = run_query(
                    df,
                    src_pattern,
                    dst_pattern,
                    self.config,
                )

                # save_results devuelve una lista de Paths
                paths = save_results(
                    result_df,
                    src_pattern,
                    dst_pattern,
                    self.config,
                )

                # Tomamos el primer archivo (parquet) como referencia principal
                parquet_path = paths[0] if paths else None

                self.registry.update(
                    query_id,
                    status=QueryStatus.DONE,
                    rows=len(result_df),
                    output=str(parquet_path) if parquet_path else None,
                )

            except Exception as e:
                # Importante: Capturar el traceback para debug si falla
                import traceback
                traceback.print_exc()
                
                self.registry.update(
                    query_id,
                    status=QueryStatus.ERROR,
                    error=str(e),
                )

            final_entry = self.registry.get(query_id)
            
            # Persistir metadata json
            if final_entry.status == QueryStatus.DONE:
                _write_query_metadata(final_entry)

            if final_entry.status == QueryStatus.ERROR:
                raise RuntimeError(final_entry.error)

            return {
                "query_id": query_id,
                "rows": final_entry.rows,
                "output": final_entry.output,
                "cached": False,
            }