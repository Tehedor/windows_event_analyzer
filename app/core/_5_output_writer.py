# app/helpers/_5_output_writer.py   
from pathlib import Path
from typing import Optional, Dict, Any, List # Añadido List
from datetime import datetime
import re
import os

import pandas as pd

from core._3_input_controller import QueryPattern

OUTPUT_MODES = ["parquet", "csv"]

def save_results(
    df: pd.DataFrame,
    src_pattern: Optional[QueryPattern],
    dst_pattern: Optional[QueryPattern],
    config: Dict[str, Any]
) -> List[Path]: # Cambiado de Path a List[Path]
    """
    Guarda el DataFrame resultado en disco en los formatos definidos en OUTPUT_MODES.
    Devuelve una lista con los Paths de los ficheros generados.
    """

    output_dir = Path(config["paths"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(output_dir, 0o775)  # Asegura permisos de lectura/escritura/ejecución
    
    output_dir_csv = Path(config["paths"]["output_dir_csv"])
    output_dir_csv.mkdir(parents=True, exist_ok=True)
    os.chmod(output_dir_csv, 0o775)  # Asegura permisos de lectura/escritura/ejecución

    # Obtenemos el nombre base sin extensión
    base_filename = _build_filename(src_pattern, dst_pattern)
    
    generated_paths = []

    # Iteramos sobre los modos configurados
    for mode in OUTPUT_MODES:
        if mode == "parquet":
            file_path = output_dir / f"{base_filename}.parquet"
            df.to_parquet(file_path)
            generated_paths.append(file_path)
            
        elif mode == "csv":
            file_path = output_dir_csv / f"{base_filename}.csv"
            # index=False suele ser preferible para no guardar el índice numérico en el CSV
            df.to_csv(file_path, index=False, encoding='utf-8') 
            generated_paths.append(file_path)

    return generated_paths


# -------------------------------------------------------------------------
# Construcción del nombre de fichero
# -------------------------------------------------------------------------

def _build_filename(
    src_pattern: Optional[QueryPattern],
    dst_pattern: Optional[QueryPattern]
) -> str:
    """
    Construye un nombre de fichero base legible y estable.
    NO incluye la extensión del archivo.
    """

    parts = []

    if src_pattern:
        parts.append(f"src_{_sanitize(src_pattern.raw)}")

    if dst_pattern:
        parts.append(f"dst_{_sanitize(dst_pattern.raw)}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    name = "__".join(parts) if parts else "query"
    
    # Hemos quitado el .parquet aquí para añadirlo dinámicamente arriba
    return name 
    # return f"{name}__{timestamp}" # Descomentar si quieres timestamp


def _sanitize(value: str) -> str:
    """
    Limpia una string para que sea segura como nombre de fichero
    y evita separadores finales.
    """

    value = value.strip().lower()

    # 🔑 eliminar separadores lógicos al final (muy importante)
    value = value.rstrip(",.-_")

    value = value.replace(" ", "")
    value = value.replace(",", "-")
    value = value.replace("*", "star")
    value = value.replace("?", "any")

    # eliminar cualquier cosa rara
    value = re.sub(r"[^a-z0-9_\-]+", "", value)

    # 🔑 evitar guiones finales
    value = value.rstrip("-")

    return value
