import json
import re
import logging
from pathlib import Path
from typing import Dict, Any

import yaml

# Configuramos un logger para ver qué eventos fallan sin romper la app
logger = logging.getLogger("uvicorn")

# -------------------------------------------------------------------------
# API principal
# -------------------------------------------------------------------------

def build_event_dictionary(config: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    """
    Construye un diccionario enriquecido de eventos.
    Ahora es ROBUSTO: si un evento falla al parsearse, se salta y se loguea el warning,
    permitiendo que la aplicación arranque.
    """

    event_dict_path = Path(config["paths"]["dataset_dicctionary"])
    components_path = Path(config["paths"]["components_config"])
    
    # Percentiles cargados dinámicamente
    percentiles = config.get("percentiles", [])
    if not percentiles:
        logger.warning("⚠️ No se han encontrado percentiles en la configuración. Los colores pueden fallar.")

    event_id_to_name = _load_event_dictionary(event_dict_path)
    components_cfg = _load_components(components_path)

    n_percentiles = len(percentiles)
    enriched: Dict[int, Dict[str, Any]] = {}

    for event_id, event_name in event_id_to_name.items():
        try:
            # Intentamos parsear el nombre
            component, p_origin, p_target = _parse_event_name(event_name)

            # Validamos si los percentiles/labels existen en la configuración actual
            if p_target not in percentiles:
                # Es común que sobren eventos si filtramos el dataset, solo debug.
                # logger.debug(f"Evento {event_name} ignorado (Target {p_target} no en percentiles)")
                continue

            percentile_index = percentiles.index(p_target)
            
            # Evitamos división por cero si solo hay 1 percentil
            if n_percentiles > 0:
                intensity = (percentile_index + 1) / n_percentiles
            else:
                intensity = 1.0

            base_color = components_cfg.get(component, {}).get("color", "#999999")
            final_color = _adjust_color_intensity(base_color, intensity)

            enriched[event_id] = {
                "event_id": event_id,
                "event_name": event_name,
                "component": component,
                "percentile_origin": p_origin,
                "percentile_target": p_target,
                "percentile_index": percentile_index,
                "intensity": intensity,
                "base_color": base_color,
                "final_color": final_color,
            }

        except ValueError as e:
            # 🛡️ CAPTURA DE ERROR: Si un evento está malformado, lo ignoramos y seguimos
            logger.warning(f"⚠️ Error parseando evento '{event_name}': {e}. Se omitirá.")
            continue
        except Exception as e:
            logger.error(f"❌ Error inesperado procesando evento '{event_name}': {e}")
            continue

    return enriched


# -------------------------------------------------------------------------
# Carga de ficheros
# -------------------------------------------------------------------------

def _load_event_dictionary(path: Path) -> Dict[int, str]:
    if not path.exists():
        # Retornamos dict vacío en vez de romper, para robustez
        logger.error(f"Event dictionary no encontrado en: {path}")
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return {int(v): k for k, v in data.items()}


def _load_components(path: Path) -> Dict[str, Any]:
    if not path.exists():
        logger.warning(f"Components config no encontrado en: {path}. Se usarán colores por defecto.")
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data.get("components", {})


# -------------------------------------------------------------------------
# Parsing de eventos (Lógica Mejorada)
# -------------------------------------------------------------------------

# Regex 1: Formato Antiguo (Component_Q05_to_Q10)
_REGEX_STANDARD = re.compile(r"^(?P<component>.+?)_Q(?P<q1>\d+)(?:_to_Q(?P<q2>\d+))?$")

# Regex 2: Formato Nuevo/Range (Battery_..._0_10-to-10_25)
# Busca: Cualquier cosa (greedy) + _ + algo + -to- + algo
_REGEX_RANGE = re.compile(r"^(?P<component>.+)_(?P<q1>[a-zA-Z0-9_]+)-to-(?P<q2>[a-zA-Z0-9_]+)$")


def _parse_event_name(event_name: str) -> tuple[str, str, str]:
    """
    Intenta parsear el nombre del evento con múltiples estrategias.
    Devuelve: component, origin_label, target_label
    """
    
    # 1. Intentar formato estándar (Qxx)
    match = _REGEX_STANDARD.match(event_name)
    if match:
        component = match.group("component")
        q1 = f"Q{match.group('q1')}"
        q2 = match.group("q2")
        if q2:
            return component, q1, f"Q{q2}"
        return component, q1, q1

    # 2. Intentar formato nuevo de rangos (-to-)
    match_range = _REGEX_RANGE.match(event_name)
    if match_range:
        return match_range.group("component"), match_range.group("q1"), match_range.group("q2")

    # 3. Fallback simple (si termina en _algo)
    # Ejemplo: Component_Label
    if "_" in event_name:
        parts = event_name.rsplit("_", 1)
        if len(parts) == 2:
            return parts[0], parts[1], parts[1]

    raise ValueError("Formato no reconocido por ninguna estrategia")


# -------------------------------------------------------------------------
# Color
# -------------------------------------------------------------------------

def _adjust_color_intensity(hex_color: str, intensity: float) -> str:
    try:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return "rgb(128,128,128)" # Fallback gris
            
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        r = int(r * intensity)
        g = int(g * intensity)
        b = int(b * intensity)

        return f"rgb({r},{g},{b})"
    except Exception:
        return "rgb(128,128,128)"