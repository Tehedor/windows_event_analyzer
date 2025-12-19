# services/queries_service.py

import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any

from core._1_config_loader import load_config
from core._2_preprocessor import load_or_preprocess_dataset
from core._3_input_controller import QueryPattern, parse_pattern
from core._4_query_engine import run_query
from core._5_output_writer import save_results

from state.registry import QueryRegistry, QueryStatus, QueryEntry
from state.locks import QueryLockManager



# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _make_query_id(src: Optional[QueryPattern],
                   dst: Optional[QueryPattern]) -> str:
    raw = f"src={src.canonical if src else ''}|dst={dst.canonical if dst else ''}"
    return hashlib.sha1(raw.encode()).hexdigest()[:12]

def _write_query_metadata(entry) -> None:
    if not entry.output:
        return

    # output puede ser string o lista
    if isinstance(entry.output, list):
        parquet_path = Path(entry.output[0])
    else:
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
        # self.df = load_or_preprocess_dataset(self.config)
        self._df = None

        self.registry = QueryRegistry()
        self.locks = QueryLockManager()

        # 🆕 reconstruir estado desde disco
        self._load_existing_queries()

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

        self.registry.load_from_disk(entries)

    def _get_dataset(self):
        if self._df is None:
            print("📦 Cargando dataset en memoria...")
            self._df = load_or_preprocess_dataset(self.config)
        return self._df


    def list_queries(self) -> list[dict]:
        queries_dir = Path(self.config["paths"]["output_dir"])
        results = []

        if not queries_dir.exists():
            return results

        for meta_file in sorted(queries_dir.glob("*.json")):
            try:
                with meta_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    results.append(data)
            except Exception as e:
                print(f"[WARN] No se pudo leer {meta_file.name}: {e}")

        return results


    def run(self, src: Optional[str], dst: Optional[str]) -> Dict[str, Any]:

        src_pattern = parse_pattern(src, "observation", self.config) if src else None
        dst_pattern = parse_pattern(dst, "prediction", self.config) if dst else None

        query_id = _make_query_id(src_pattern, dst_pattern)
        lock = self.locks.acquire(query_id)

        with lock:
            entry = self.registry.get(query_id)
            if entry and entry.status == QueryStatus.DONE:
                return {
                    "query_id": query_id,
                    "rows": entry.rows,
                    "output": entry.output,
                    "cached": True,
                }

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

                paths = save_results(
                    result_df,
                    src_pattern,
                    dst_pattern,
                    self.config,
                )

                parquet_path = paths[0]   # el parquet es el output principal

                self.registry.update(
                    query_id,
                    status=QueryStatus.DONE,
                    rows=len(result_df),
                    output=str(parquet_path),
                )


            except Exception as e:
                self.registry.update(
                    query_id,
                    status=QueryStatus.ERROR,
                    error=str(e),
                )

            final_entry = self.registry.get(query_id)
            _write_query_metadata(final_entry)

            if final_entry.status == QueryStatus.ERROR:
                raise RuntimeError(final_entry.error)

            return {
                "query_id": query_id,
                "rows": final_entry.rows,
                "output": final_entry.output,
                "cached": False,
            }
