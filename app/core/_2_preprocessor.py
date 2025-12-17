# app/helpers/_2_preprocessor.py 
from pathlib import Path
from typing import Dict, Any

import pandas as pd


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
import ast


def _normalize_events(value):
    """
    Convierte el campo de eventos a list[int].
    Acepta:
    - list[int]
    - string "[1, 2, 3]"
    """
    if isinstance(value, list):
        return value

    if isinstance(value, str):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

    raise ValueError(f"Formato de eventos no soportado: {value!r}")


def _preprocess_dataframe(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    df = df.copy()

    separator = config["processing"]["separator"]

    obs_events_col = config["columns"]["observation"]["events"]
    pred_events_col = config["columns"]["prediction"]["events"]

    obs_index_col = config["processing"]["index_columns"]["observation"]
    pred_index_col = config["processing"]["index_columns"]["prediction"]

    # 🔧 NORMALIZACIÓN CLAVE
    df[obs_events_col] = df[obs_events_col].apply(_normalize_events)
    df[pred_events_col] = df[pred_events_col].apply(_normalize_events)

    # ✅ Representación canónica CORRECTA
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
    df.to_parquet(path)
