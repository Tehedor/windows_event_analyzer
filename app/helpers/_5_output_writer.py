# app/helpers/_5_output_writer.py   
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import re

import pandas as pd

from helpers._3_input_controller import QueryPattern


def save_results(
    df: pd.DataFrame,
    src_pattern: Optional[QueryPattern],
    dst_pattern: Optional[QueryPattern],
    config: Dict[str, Any]
) -> Path:
    """
    Guarda el DataFrame resultado en disco con un nombre dinámico.
    Devuelve el Path al fichero generado.
    """

    output_dir = Path(config["paths"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = _build_filename(src_pattern, dst_pattern)
    output_path = output_dir / filename

    df.to_parquet(output_path)

    return output_path


# -------------------------------------------------------------------------
# Construcción del nombre de fichero
# -------------------------------------------------------------------------

def _build_filename(
    src_pattern: Optional[QueryPattern],
    dst_pattern: Optional[QueryPattern]
) -> str:
    """
    Construye un nombre de fichero legible y estable a partir
    de los patrones usados en la consulta.
    """

    parts = []

    if src_pattern:
        parts.append(f"src_{_sanitize(src_pattern.raw)}")

    if dst_pattern:
        parts.append(f"dst_{_sanitize(dst_pattern.raw)}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    name = "__".join(parts) if parts else "query"
    return f"{name}.parquet"
    # return f"{name}__{timestamp}.parquet"


def _sanitize(value: str) -> str:
    """
    Limpia una string para que sea segura como nombre de fichero.
    """
    value = value.strip().lower()
    value = value.replace(" ", "")
    value = value.replace(",", "-")
    value = value.replace("*", "star")
    value = value.replace("?", "any")

    # eliminar cualquier cosa rara
    value = re.sub(r"[^a-z0-9_\-]+", "", value)

    return value
