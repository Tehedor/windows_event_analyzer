# core/_1_config_loader.py
import os
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Union

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
    "PERCENTILES": ("percentiles"),

}

# -------------------------------------------------------------------------
# API principal
# -------------------------------------------------------------------------

def load_config(config_path: Union[Path, None] = None) -> Dict[str, Any]:
    """
    Carga la configuración del proyecto siguiendo esta prioridad:
      1. Variables de entorno (si tienen valor real).
      2. config.yml (valor por defecto).
    """

    load_dotenv()

    # 1️⃣ Resolver ruta del config.yml
    if config_path is None:
        # Asumiendo que este script está en app/core/, subimos a app/
        project_root = Path(__file__).resolve().parents[1]
        config_path = project_root / "config" / "config.yml"

    if not config_path.exists():
        # Fallback de seguridad por si la estructura cambia en Docker
        potential_path = Path("app/config/config.yml")
        if potential_path.exists():
            config_path = potential_path.resolve()
        else:
            raise FileNotFoundError(f"No se encontró config.yml en {config_path}")

    # 2️⃣ Cargar YAML
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("config.yml no contiene un diccionario válido")

    # 3️⃣ Mezclar config_env.py con prioridad
    project_root = Path(__file__).resolve().parents[1]
    config_env = _load_config_env(project_root)
    if config_env:
        config = _merge_dicts(config, config_env)

    # 4️⃣ Aplicar overrides simples de entorno (SOLO SI NO ESTÁN VACÍOS)
    _apply_env_overrides(config)

    # 5️⃣ Aplicar percentiles desde ENV (si existen y no están vacíos)
    _apply_percentiles_override(config)

    # 6️⃣ Normalizar paths
    # Usamos el directorio padre de 'app' como base para resolver paths relativos
    project_base = config_path.parent.parent
    _resolve_paths(config, base_dir=project_base)

    # 7️⃣ Validaciones mínimas
    _validate_config(config)

    return config


# -------------------------------------------------------------------------
# Helpers internos
# -------------------------------------------------------------------------

def _apply_env_overrides(config: Dict[str, Any]) -> None:
    """
    Sobrescribe valores del config con variables de entorno.
    CRÍTICO: Ignora valores None o cadenas vacías "" (común en Docker).
    """
    for env_var, key_path in ENV_OVERRIDES.items():
        value = os.getenv(env_var)
        
        # FIX: Verificamos que no sea None y que no sea una cadena vacía o espacios
        if value and value.strip():
            _set_nested_key(config, key_path, value)


def _load_config_env(project_root: Path) -> Dict[str, Any]:
    """
    Carga config_env.py si existe y lo convierte al formato del config.yml.
    Prioridad: CONFIG/config dict > settings_env (Pydantic) > Settings()
    """
    env_path = project_root / "config_env.py"
    if not env_path.exists():
        return {}

    spec = importlib.util.spec_from_file_location("config_env", env_path)
    if spec is None or spec.loader is None:
        return {}

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for name in ("CONFIG", "config"):
        value = getattr(module, name, None)
        if isinstance(value, dict):
            return value

    settings_env = getattr(module, "settings_env", None)
    if settings_env is not None:
        settings_dict = _settings_to_dict(settings_env)
        return _config_env_to_dict(settings_dict)

    settings_cls = getattr(module, "Settings", None)
    if settings_cls is not None:
        try:
            settings_dict = _settings_to_dict(settings_cls())
            return _config_env_to_dict(settings_dict)
        except Exception:
            return {}

    return {}


def _settings_to_dict(settings_obj: Any) -> Dict[str, Any]:
    """Convierte instancia de Pydantic Settings a dict compatible."""
    if hasattr(settings_obj, "model_dump"):
        return settings_obj.model_dump()
    if hasattr(settings_obj, "dict"):
        return settings_obj.dict()
    return dict(settings_obj)


def _config_env_to_dict(settings_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Mapea Settings a la estructura del config.yml."""
    paths = {
        "dataset_raw": settings_dict.get("DATASET_RAW_PATH"),
        "dataset_processed": settings_dict.get("DATASET_PROCESSED_PATH"),
        "output_dir": settings_dict.get("OUTPUT_DIR"),
        "output_dir_csv": settings_dict.get("OUTPUT_DIR_CSV"),
        "dataset_dicctionary": settings_dict.get("DATASET_DICTIONARY_PATH"),
    }

    columns = {
        "observation": {
            "events": settings_dict.get("OBS_EVENTS_COLUMN"),
        },
        "prediction": {
            "events": settings_dict.get("PRED_EVENTS_COLUMN"),
        },
    }

    config_env: Dict[str, Any] = {
        "paths": {k: v for k, v in paths.items() if v is not None},
        "columns": columns,
    }

    percentiles = settings_dict.get("PERCENTILES")
    if percentiles is not None:
        config_env["percentiles"] = percentiles

    return config_env


def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Mezcla recursiva: override tiene prioridad sobre base."""
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = _merge_dicts(base[k], v)
        else:
            base[k] = v
    return base


def _apply_percentiles_override(config: Dict[str, Any]) -> None:
    """
    Sobrescribe percentiles desde ENV:
    PERCENTILES=Q05,Q10,Q20,...
    """
    raw = os.getenv("PERCENTILES")
    
    # FIX: Ignorar si es None o vacío
    if not raw or not raw.strip():
        return

    percentiles = [p.strip() for p in raw.split(",") if p.strip()]
    
    if percentiles:
        config["percentiles"] = percentiles
    else:
        # Si la variable existe pero tras limpiar está vacía (ej: ",,"), advertimos o ignoramos
        pass 


def _resolve_paths(config: Dict[str, Any], base_dir: Path) -> None:
    """
    Convierte paths relativos a absolutos.
    """
    paths = config.get("paths", {})
    for key, value in paths.items():
        if not value: continue  # Skip si el path en config es nulo/vacío

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
        val = _get_nested_key(config, key_path)
        if not val:
             # Falla si la configuración final (tras merge) está vacía
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


# Bloque para testear rápidamente
if __name__ == "__main__":
    try:
        cfg = load_config()
        print("✅ Configuración cargada correctamente.")
        print(f"📂 Output Dir: {cfg['paths']['output_dir']}")
    except Exception as e:
        print(f"❌ Error: {e}")