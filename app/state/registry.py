# state/registry.py

from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime


# -------------------------------------------------------------------------
# Estados de una query
# -------------------------------------------------------------------------

class QueryStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


# -------------------------------------------------------------------------
# Entrada de una query (registro persistente y en memoria)
# -------------------------------------------------------------------------

@dataclass
class QueryEntry:
    """
    Representa una consulta ejecutada o en ejecución.

    - src_raw / dst_raw : lo que escribió el usuario (UX, trazabilidad)
    - src / dst         : forma canónica (identidad lógica de la query)
    """

    query_id: str

    # Entrada original del usuario
    src_raw: Optional[str]
    dst_raw: Optional[str]

    # Forma canónica normalizada
    src: Optional[str]
    dst: Optional[str]

    status: QueryStatus

    rows: int = 0
    output: Optional[str] = None
    error: Optional[str] = None

    created_at: str = ""
    updated_at: str = ""

    # ------------------------------------------------------------------
    # Serialización a disco
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "query_id": self.query_id,

            # raw (UX / trazabilidad)
            "src_raw": self.src_raw,
            "dst_raw": self.dst_raw,

            # canonical (identidad)
            "src": self.src,
            "dst": self.dst,

            "status": self.status,
            "rows": self.rows,
            "output": self.output,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    # ------------------------------------------------------------------
    # Deserialización desde disco (retrocompatible)
    # ------------------------------------------------------------------

    @staticmethod
    def from_dict(data: dict) -> "QueryEntry":
        return QueryEntry(
            query_id=data["query_id"],

            src_raw=data.get("src_raw"),
            dst_raw=data.get("dst_raw"),

            src=data.get("src"),
            dst=data.get("dst"),

            status=QueryStatus(data["status"]),
            rows=data.get("rows", 0),
            output=data.get("output"),
            error=data.get("error"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


# -------------------------------------------------------------------------
# Registro en memoria de queries
# -------------------------------------------------------------------------

class QueryRegistry:
    """
    Registro en memoria de todas las queries conocidas.
    """

    def __init__(self):
        self._queries: Dict[str, QueryEntry] = {}

    # ------------------------------------------------------------------
    # Crear nueva query
    # ------------------------------------------------------------------

    def create(
        self,
        query_id: str,
        src_raw: Optional[str],
        dst_raw: Optional[str],
        src: Optional[str],
        dst: Optional[str],
    ) -> QueryEntry:
        now = datetime.utcnow().isoformat()

        entry = QueryEntry(
            query_id=query_id,
            src_raw=src_raw,
            dst_raw=dst_raw,
            src=src,
            dst=dst,
            status=QueryStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        self._queries[query_id] = entry
        return entry

    # ------------------------------------------------------------------
    # Actualizar campos de una query existente
    # ------------------------------------------------------------------

    def update(self, query_id: str, **fields) -> None:
        entry = self._queries[query_id]

        for key, value in fields.items():
            setattr(entry, key, value)

        entry.updated_at = datetime.utcnow().isoformat()

    # ------------------------------------------------------------------
    # Accesores
    # ------------------------------------------------------------------

    def get(self, query_id: str) -> Optional[QueryEntry]:
        return self._queries.get(query_id)

    def all(self) -> Dict[str, QueryEntry]:
        return self._queries

    # ------------------------------------------------------------------
    # Carga desde disco (bootstrap al arrancar)
    # ------------------------------------------------------------------

    def load_from_disk(self, entries: Dict[str, QueryEntry]) -> None:
        self._queries = entries
