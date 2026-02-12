# app/helpers/_4_query_engine.py
import re
from typing import Optional, Dict, Any

import pandas as pd

from core._3_input_controller import QueryPattern



# -------------------------------------------------------------------------
# API principal
# -------------------------------------------------------------------------

def run_query(
    df: pd.DataFrame,
    src_pattern: Optional[QueryPattern],
    dst_pattern: Optional[QueryPattern],
    config: Dict[str, Any]
) -> pd.DataFrame:
    """
    Ejecuta la consulta sobre el DataFrame preprocesado usando
    patrones de observación (src) y/o predicción (dst).
    """

    if src_pattern is None and dst_pattern is None:
        return df

    result = df

    separator = config["processing"]["separator"]

    if src_pattern is not None:
        result = _apply_pattern(
            result,
            pattern=src_pattern,
            level=0,  # obs_seq
            separator=separator
        )

    if dst_pattern is not None:
        result = _apply_pattern(
            result,
            pattern=dst_pattern,
            level=1,  # pred_seq
            separator=separator
        )

    return result


# -------------------------------------------------------------------------
# Aplicación de patrones
# -------------------------------------------------------------------------

def _apply_pattern(
    df: pd.DataFrame,
    pattern: QueryPattern,
    level: int,
    separator: str
) -> pd.DataFrame:
    """
    Aplica un patrón a un nivel del MultiIndex.

    level = 0 -> obs_seq
    level = 1 -> pred_seq
    """

    index_values = df.index.get_level_values(level)

    # 1️⃣ Prefijo ESTRUCTURAL (solo si el usuario ha puesto *)
    prefix = _extract_prefix(pattern, separator)

    if prefix is not None:
        mask = index_values.str.startswith(prefix)
        return df[mask]

    # 2️⃣ Regex (match exacto o con ?)
    regex = re.compile(pattern.regex)
    mask = index_values.str.match(regex)
    return df[mask]


# -------------------------------------------------------------------------
# Prefijo semántico CORRECTO
# -------------------------------------------------------------------------

def _extract_prefix(
    pattern: QueryPattern,
    separator: str
) -> Optional[str]:
    """
    Extrae un prefijo SOLO cuando el usuario usa '*'
    y SOLO como secuencia completa, no como substring.

    Ejemplos:
    - "475,*"       -> "475,"
    - "1,2,*"       -> "1,2,"
    - "1,?,2,*"     -> None (tiene wildcard estructural)
    - "1,2"         -> None
    """

    raw = pattern.raw.replace(" ", "").replace(".", separator)

    # Prefijo SOLO si termina en *
    if not raw.endswith("*"):
        return None

    # Quitar el *
    base = raw[:-1]

    # Si hay '?' en el prefijo, no es estructural → usar regex
    if "?" in base:
        return None

    # El prefijo debe acabar en separador
    if not base.endswith(separator):
        base += separator

    return base
