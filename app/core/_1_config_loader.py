# core/_1_config_loader.py
import os
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Union

from dotenv import load_dotenv
import yaml

# -------------------------------------------------------------------------
# API principal
# -------------------------------------------------------------------------

def load_config(config_path: Union[Path, None] = None) -> Dict[str, Any]:
    load_dotenv()

    # 1️⃣ Resolver ruta del config.yml base
    if config_path is None:
        project_root = Path(__file__).resolve().parents[1]
        config_path = project_root / "config" / "config.yml"

    if not config_path.exists():
        potential_path = Path("app/config/config.yml")
        if potential_path.exists():
            config_path = potential_path.resolve()
        else:
            raise FileNotFoundError(f"No se encontró config.yml en {config_path}")

    # 2️⃣ Cargar YAML Base
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 3️⃣ Mezclar config_env.py (Pydantic)
    project_root = Path(__file__).resolve().parents[1]
    config_env, env_vars_raw = _load_config_env(project_root)
    
    if config_env:
        config = _merge_dicts(config, config_env)

    # 4️⃣ RESOLUCIÓN DINÁMICA DE RUTAS
    _resolve_dynamic_execution_paths(config, project_root, env_vars_raw)

    # 5️⃣ Resolver paths relativos
    project_base = config_path.parent.parent
    _resolve_paths(config, base_dir=project_base)

    # 6️⃣ Validaciones
    _validate_config(config)

    return config


# -------------------------------------------------------------------------
# Lógica de Resolución Dinámica
# -------------------------------------------------------------------------

def _resolve_dynamic_execution_paths(config: Dict[str, Any], project_root: Path, env_vars: Dict[str, Any]):
    paths = config.get("paths", {})
    version = env_vars.get("WINDOW_VERSION", "v001")
    
    # ---------------------------------------------------------
    # 1. OUTPUTS DINÁMICOS (NUEVO)
    # ---------------------------------------------------------
    # Leemos la base (ej: "output")
    output_base_str = paths.get("output_base", "output")
    output_base_path = Path(output_base_str)
    
    if not output_base_path.is_absolute():
        output_base_path = project_root / output_base_path

    # Construimos la estructura: output/v001/queries y output/v001/queries_csv
    versioned_path = output_base_path / version
    
    final_output_dir = versioned_path / "queries"
    final_output_dir_csv = versioned_path / "queries_csv"

    # Inyectamos las rutas finales en el config para que el resto de la app las use
    config["paths"]["output_dir"] = str(final_output_dir)
    config["paths"]["output_dir_csv"] = str(final_output_dir_csv)

    # ---------------------------------------------------------
    # 2. DATASETS (INPUTS)
    # ---------------------------------------------------------
    raw_path_input = paths.get("dataset_raw")
    if not raw_path_input or not raw_path_input.strip():
        raw_path_input = "executions/03_preparewindowsds"
        
    base_raw_path = Path(raw_path_input)
    
    if not base_raw_path.is_absolute():
        base_raw_path = project_root / base_raw_path

    current_variant_path = base_raw_path / version
    
    # A. Dataset RAW
    parquet_name = paths.get("parquet_name", "03_preparewindowsds_dataset.parquet")
    raw_parquet_path = current_variant_path / parquet_name
    
    if not raw_parquet_path.exists():
        raise FileNotFoundError(
            f"No se encuentra el dataset.\n"
            f"Ruta buscada: {raw_parquet_path}\n"
            f"Verifica la versión '{version}' y el montaje de volúmenes."
        )
    
    config["paths"]["dataset_raw"] = str(raw_parquet_path)

    # B. Params del stage actual (f03)
    params_path = current_variant_path / "params.yaml"
    if not params_path.exists():
        raise FileNotFoundError(f"No se encuentra params.yaml en: {params_path}")
    
    with open(params_path, "r", encoding="utf-8") as f:
        params_data = yaml.safe_load(f)
    
    # Compatibilidad: acepta el parent en raíz o dentro de parameters.parent_variant
    parent_variant_f02 = params_data.get("parent")
    if not parent_variant_f02:
        parent_variant_f02 = params_data.get("parameters", {}).get("parent_variant")
    if not parent_variant_f02:
        raise ValueError(
            f"params.yaml en {version} no contiene 'parent' ni 'parameters.parent_variant'"
        )

    # C. Diccionario de eventos: se toma directamente desde el stage f03 actual
    dict_name = paths.get("dictionary_name", "03_events_catalog.json")
    dict_path = current_variant_path / dict_name
    if not dict_path.exists():
        raise FileNotFoundError(
            f"No se encuentra el catálogo de eventos para {version}.\n"
            f"Ruta buscada: {dict_path}"
        )
    config["paths"]["dataset_dicctionary"] = str(dict_path)

    # D. Bands: se extraen de executions/f02_events/<parent_f02>/params.yaml
    executions_root = base_raw_path.parent
    f02_params_path = executions_root / "f02_events" / parent_variant_f02 / "params.yaml"
    if not f02_params_path.exists():
        raise FileNotFoundError(
            f"No se encuentra params.yaml del parent f02 para {version}.\n"
            f"Ruta buscada: {f02_params_path}"
        )

    with f02_params_path.open("r", encoding="utf-8") as f:
        f02_params_data = yaml.safe_load(f) or {}

    bands = f02_params_data.get("parameters", {}).get("bands")
    if bands is None:
        bands = f02_params_data.get("bands")

    if bands is not None:
        config["bands"] = bands

    # E. Output Procesado (Cache del dataset indexado)
    processed_base = Path(paths.get("dataset_processed", "datasets/processed"))
    if str(processed_base) == "." or str(processed_base) == "":
        processed_base = project_root / "datasets/processed"

    if not processed_base.suffix: 
        processed_filename = f"03_windows_{version}_indexed.parquet"
        config["paths"]["dataset_processed"] = str(processed_base / processed_filename)
    
    print(
        f"✅ Configuración Dinámica Cargada: Versión {version} "
        f"(Parent f02: {parent_variant_f02})"
    )
    print(f"📂 Outputs configurados en: {versioned_path}")


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _load_config_env(project_root: Path):
    env_path = project_root / "config_env.py"
    if not env_path.exists():
        return {}, {}

    spec = importlib.util.spec_from_file_location("config_env", env_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    settings_env = getattr(module, "settings_env", None)
    
    if settings_env:
        raw_dict = _settings_to_dict(settings_env)
        return _config_env_to_dict(raw_dict), raw_dict
        
    return {}, {}

def _settings_to_dict(settings_obj: Any) -> Dict[str, Any]:
    if hasattr(settings_obj, "model_dump"):
        return settings_obj.model_dump()
    return settings_obj.dict()

def _config_env_to_dict(settings_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mapea Settings a la estructura del config.yml.
    """
    
    def get_val(key, default=None):
        val = settings_dict.get(key)
        if val is None or (isinstance(val, str) and not val.strip()):
            return default
        return val

    paths = {
        "dataset_raw": get_val("DATASET_RAW_PATH"),
        "dataset_processed": get_val("DATASET_PROCESSED_PATH"),
        "components_config": get_val("COMPONENTS_CTRL"),
        
        # Mapeamos la nueva variable base
        "output_base": get_val("OUTPUT_DIR", "output"),
    }

    filenames = {
        "parquet_name": get_val("PARQUET_NAME"),
        "metadata_name": get_val("METADATA_NAME"),
        "dictionary_name": get_val("DICTIONARY_NAME"),
    }

    columns = {
        "observation": {
            "events": get_val("OBS_EVENTS_COLUMN", "observation_events"),
        },
        "prediction": {
            "events": get_val("PRED_EVENTS_COLUMN", "prediction_events"),
        },
    }

    config_env: Dict[str, Any] = {
        "paths": {k: v for k, v in {**paths, **filenames}.items() if v is not None},
        "columns": columns,
        "ram_timeout": get_val("DATASET_RAM_TIMEOUT", 0),
    }
    
    return config_env

def _resolve_paths(config: Dict[str, Any], base_dir: Path) -> None:
    # Excluir nombres de archivo (no son rutas)
    exclude_keys = {"parquet_name", "metadata_name", "dictionary_name", "output_base"}
    
    paths = config.get("paths", {})
    for key, value in paths.items():
        if not value or key in exclude_keys: continue
        p = Path(value)
        if not p.is_absolute():
            paths[key] = str((base_dir / p).resolve())

def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = _merge_dicts(base[k], v)
        else:
            base[k] = v
    return base

def _validate_config(config: Dict[str, Any]) -> None:
    required_paths = [
        ("paths", "dataset_raw"),
        ("paths", "dataset_processed"),
        ("paths", "dataset_dicctionary"),
        # Validamos que existan tras la resolución dinámica
        ("paths", "output_dir"),
        ("paths", "output_dir_csv"),
    ]
    for key_path in required_paths:
        val = _get_nested_key(config, key_path)
        if not val:
            raise ValueError(f"Falta configuración obligatoria: {'.'.join(key_path)}")

def _get_nested_key(d: Dict[str, Any], keys: tuple) -> Any:
    for key in keys:
        if not isinstance(d, dict): return None
        d = d.get(key)
    return d