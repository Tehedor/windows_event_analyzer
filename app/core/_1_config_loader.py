# app/helpers/_1_config_loader.py
# app/helpers/_1_config_loader.py

import os
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv
import yaml


# -------------------------------------------------------------------------
# Variables de entorno soportadas (ENV -> ruta en config)
# -------------------------------------------------------------------------

ENV_OVERRIDES = {
    "DATASET_RAW_PATH": ("paths", "dataset_raw"),
    "DATASET_PROCESSED_PATH": ("paths", "dataset_processed"),
    "OUTPUT_DIR": ("paths", "output_dir"),
    "OUTPUT_DIR_CSV": ("paths", "output_dir_csv"),
    "DATASET_DICTIONARY_PATH": ("paths", "dataset_dicctionary"),

    "OBS_EVENTS_COLUMN": ("columns", "observation", "events"),
    "PRED_EVENTS_COLUMN": ("columns", "prediction", "events"),
}


# -------------------------------------------------------------------------
# API principal
# -------------------------------------------------------------------------

def load_config(config_path: Path | None = None) -> Dict[str, Any]:
    """
    Carga la configuración del proyecto siguiendo esta prioridad:
      1. Variables de entorno (.env)
      2. config.yml
    """

    load_dotenv()

    # 1️⃣ Resolver ruta del config.yml
    if config_path is None:
        project_root = Path(__file__).resolve().parents[1]
        config_path = project_root / "config" / "config.yml"

    if not config_path.exists():
        raise FileNotFoundError(f"No se encontró config.yml en {config_path}")

    # 2️⃣ Cargar YAML
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("config.yml no contiene un diccionario válido")

    # 3️⃣ Aplicar overrides simples de entorno
    _apply_env_overrides(config)

    # 4️⃣ Aplicar percentiles desde ENV (si existen)
    _apply_percentiles_override(config)

    # 5️⃣ Normalizar paths
    _resolve_paths(config, base_dir=config_path.parent.parent)

    # 6️⃣ Validaciones mínimas
    _validate_config(config)

    return config


# -------------------------------------------------------------------------
# Helpers internos
# -------------------------------------------------------------------------

def _apply_env_overrides(config: Dict[str, Any]) -> None:
    """
    Sobrescribe valores simples del config con variables de entorno.
    """
    for env_var, key_path in ENV_OVERRIDES.items():
        value = os.getenv(env_var)
        if value is not None:
            _set_nested_key(config, key_path, value)


def _apply_percentiles_override(config: Dict[str, Any]) -> None:
    """
    Sobrescribe percentiles desde ENV:
    PERCENTILES=Q05,Q10,Q20,...
    """
    raw = os.getenv("PERCENTILES")
    if not raw:
        return

    percentiles = [p.strip() for p in raw.split(",") if p.strip()]
    if not percentiles:
        raise ValueError("PERCENTILES en .env está vacío o mal formado")

    config["percentiles"] = percentiles


def _resolve_paths(config: Dict[str, Any], base_dir: Path) -> None:
    """
    Convierte paths relativos a absolutos.
    """
    paths = config.get("paths", {})
    for key, value in paths.items():
        p = Path(value)
        if not p.is_absolute():
            paths[key] = str((base_dir / p).resolve())


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validación mínima para MVP.
    """
    required_paths = [
        ("paths", "dataset_raw"),
        ("paths", "dataset_processed"),
        ("paths", "output_dir"),
        ("paths", "output_dir_csv"),
        ("paths", "dataset_dicctionary"),
        ("paths", "components_config"),
    ]

    for key_path in required_paths:
        if _get_nested_key(config, key_path) is None:
            raise ValueError(f"Falta configuración obligatoria: {'.'.join(key_path)}")

    required_columns = [
        ("columns", "observation", "events"),
        ("columns", "prediction", "events"),
    ]

    for key_path in required_columns:
        if _get_nested_key(config, key_path) is None:
            raise ValueError(f"Falta columna obligatoria: {'.'.join(key_path)}")

    percentiles = config.get("percentiles")
    if not isinstance(percentiles, list) or not percentiles:
        raise ValueError("percentiles debe ser una lista no vacía")


def _set_nested_key(d: Dict[str, Any], keys: tuple, value: Any) -> None:
    """
    Asigna un valor en un diccionario anidado.
    """
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


def _get_nested_key(d: Dict[str, Any], keys: tuple) -> Any:
    """
    Obtiene un valor de un diccionario anidado.
    """
    for key in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(key)
    return d
