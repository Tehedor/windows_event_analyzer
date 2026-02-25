# app/helpers/_5_output_writer.py   
from pathlib import Path
from typing import Optional, Dict, Any, List # Añadido List
from datetime import datetime
import re
import os

import pandas as pd

from core._3_input_controller import QueryPattern

OUTPUT_MODES = ["parquet", "csv"]
MAX_CSV_ROWS = 100000

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
    os.chmod(output_dir, 0o777)  # Asegura permisos de lectura/escritura/ejecución
    for parent in output_dir.parents:
        try:
            os.chmod(parent, 0o777)
        except:
            pass
    print(f"📁 Guardando resultados en: {output_dir}")
    output_dir_csv = Path(config["paths"]["output_dir_csv"])
    output_dir_csv.mkdir(parents=True, exist_ok=True)
    os.chmod(output_dir_csv, 0o777)  # Asegura permisos de lectura/escritura/ejecución
    for parent in output_dir_csv.parents:
        try:
            os.chmod(parent, 0o777)
        except:
            pass

    # Obtenemos el nombre base sin extensión
    base_filename = _build_filename(src_pattern, dst_pattern)
    generated_paths = []

    for mode in OUTPUT_MODES:
        if mode == "parquet":
            file_path = output_dir / f"{base_filename}.parquet"
            df.to_parquet(file_path)
            os.chmod(file_path, 0o666)
            generated_paths.append(file_path)
            
        elif mode == "csv":
            # 🚀 PROTECCIÓN: Si el resultado es muy grande, nos saltamos el CSV
            if len(df) <= MAX_CSV_ROWS:
                file_path = output_dir_csv / f"{base_filename}.csv"
                df.to_csv(file_path, index=False, encoding='utf-8') 
                os.chmod(file_path, 0o666)
                generated_paths.append(file_path)
            else:
                print(f"⚠️ Resultado demasiado grande ({len(df)} filas). Omitiendo creación de archivo CSV para evitar saturar el servidor.")

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


# def _sanitize(value: str) -> str:
#     """
#     Limpia una string para que sea segura como nombre de fichero
#     y evita separadores finales.
#     """

#     value = value.strip().lower()

#     # 🔑 eliminar separadores lógicos al final (muy importante)
#     value = value.rstrip(",.-_")

#     value = value.replace(" ", "")
#     value = value.replace(",", "-")
#     value = value.replace("*", "star")
#     value = value.replace("?", "any")

#     # eliminar cualquier cosa rara
#     value = re.sub(r"[^a-z0-9_\-]+", "", value)

#     # 🔑 evitar guiones finales
#     value = value.rstrip("-")

#     return value
def _sanitize(value: str) -> str:
    """
    Limpia una string para que sea segura como nombre de fichero,
    traduciendo símbolos lógicos y marcando explícitamente el inicio y fin de los grupos.
    """
    value = value.strip().lower()

    # 1. Eliminar espacios
    value = value.replace(" ", "")

    # 2. Traducir símbolos lógicos y comodines
    value = value.replace("*", "star")
    value = value.replace("?", "any")
    value = value.replace("|", "_or_")
    value = value.replace("&", "_and_")
    value = value.replace("!", "not_")
    
    # 3. Manejar pertenencia (llaves)
    value = value.replace("{", "has_")
    value = value.replace("}", "")  # Si quisieras, podrías poner "_endhas", pero suele recargar mucho el nombre
    
    # 4. Manejar agrupaciones (paréntesis) con la nomenclatura que prefieres
    value = value.replace("(", "set_")
    value = value.replace(")", "_endset")

    # 5. Separadores de secuencia (comas se vuelven guiones)
    value = value.replace(",", "-")

    # 6. Eliminar cualquier carácter extraño que quede
    value = re.sub(r"[^a-z0-9_\-]+", "", value)

    # 7. Limpiar guiones o barras bajas duplicadas y combinaciones raras (estética)
    value = re.sub(r"_+", "_", value)
    value = re.sub(r"-+", "-", value)
    value = value.replace("-_", "_").replace("_-", "_") # Limpia casos como "148-_endset" a "148_endset"

    # 8. Evitar separadores al principio o al final
    value = value.strip(".-_")

    return value