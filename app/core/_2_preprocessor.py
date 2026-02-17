# app/helpers/_2_preprocessor.py 
from pathlib import Path
from typing import Dict, Any

import os
import ast
import pandas as pd
import numpy as np  # <--- IMPORTANTE: Necesario para detectar el array

def load_or_preprocess_dataset(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Carga el dataset procesado si existe.
    Si no existe, carga el raw, lo preprocesa y lo guarda.
    Devuelve siempre un DataFrame listo para consulta.
    """

    processed_path = Path(config["paths"]["dataset_processed"])
    raw_path = Path(config["paths"]["dataset_raw"])

    if processed_path.exists():
        return _load_processed_dataset(processed_path)

    # Si no existe el procesado → preprocesar
    df_raw = _load_raw_dataset(raw_path)
    df_processed = _preprocess_dataframe(df_raw, config)

    _save_processed_dataset(df_processed, processed_path)

    return df_processed


# -------------------------------------------------------------------------
# Carga de datasets
# -------------------------------------------------------------------------

def _load_processed_dataset(path: Path) -> pd.DataFrame:
    """
    Carga el dataset ya procesado.
    """
    return pd.read_parquet(path)


def _load_raw_dataset(path: Path) -> pd.DataFrame:
    """
    Carga el dataset raw.
    """
    if not path.exists():
        raise FileNotFoundError(f"Dataset raw no encontrado: {path}")

    return pd.read_parquet(path)


# -------------------------------------------------------------------------
# Preprocesamiento
# -------------------------------------------------------------------------

def _normalize_events(value):
    """
    Convierte el campo de eventos a list[int].
    Acepta:
    - list[int]
    - numpy.ndarray (NUEVO)
    - string "[1, 2, 3]"
    """
    # 1. Si ya es lista, devolver tal cual
    if isinstance(value, list):
        return value

    # 2. Si es Array de Numpy (el error que te daba)
    if isinstance(value, np.ndarray):
        return value.tolist()

    # 3. Si es String, intentar parsear
    if isinstance(value, str):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
    
    # 4. Manejo de nulos (opcional, por seguridad)
    if pd.isna(value):
        return []

    raise ValueError(f"Formato de eventos no soportado: {value!r} (Tipo: {type(value)})")


def _preprocess_dataframe(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()

    separator = config["processing"]["separator"]

    # Leemos los nombres de columnas configurados en .env o defaults
    obs_events_col = config["columns"]["observation"]["events"]
    pred_events_col = config["columns"]["prediction"]["events"]

    obs_index_col = config["processing"]["index_columns"]["observation"]
    pred_index_col = config["processing"]["index_columns"]["prediction"]

    # Validar que las columnas existen antes de procesar
    if obs_events_col not in df.columns:
        raise KeyError(f"La columna '{obs_events_col}' no existe en el dataset. Columnas disponibles: {df.columns.tolist()}")
    
    if pred_events_col not in df.columns:
        raise KeyError(f"La columna '{pred_events_col}' no existe en el dataset.")

    # 🔧 NORMALIZACIÓN CLAVE
    # Convertimos strings o arrays a listas de python puras
    df[obs_events_col] = df[obs_events_col].apply(_normalize_events)
    df[pred_events_col] = df[pred_events_col].apply(_normalize_events)

    # ✅ Representación canónica CORRECTA
    # Generamos el string separado por guiones (ej: "63-45") para el índice
    df[obs_index_col] = df[obs_events_col].apply(
        lambda x: separator.join(map(str, x))
    )

    df[pred_index_col] = df[pred_events_col].apply(
        lambda x: separator.join(map(str, x))
    )

    # MultiIndex
    df = df.set_index([obs_index_col, pred_index_col])

    return df


# -------------------------------------------------------------------------
# Persistencia
# -------------------------------------------------------------------------

def _save_processed_dataset(df: pd.DataFrame, path: Path) -> None:
    """
    Guarda el dataset procesado en disco.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o777)
    df.to_parquet(path)
    os.chmod(path, 0o666)