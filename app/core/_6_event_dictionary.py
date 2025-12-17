# app/helpers/_6_event_dictionary.py

import json
import re
from pathlib import Path
from typing import Dict, Any

import yaml


# -------------------------------------------------------------------------
# API principal
# -------------------------------------------------------------------------

def build_event_dictionary(config: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    """
    Construye un diccionario enriquecido de eventos:

    {
      event_id: {
        event_name,
        component,
        percentile_origin,
        percentile_target,
        percentile_index,
        intensity,
        base_color,
        final_color
      }
    }
    """

    event_dict_path = Path(config["paths"]["dataset_dicctionary"])
    components_path = Path(config["paths"]["components_config"])
    percentiles = config["percentiles"]

    event_id_to_name = _load_event_dictionary(event_dict_path)
    components_cfg = _load_components(components_path)

    n_percentiles = len(percentiles)

    enriched: Dict[int, Dict[str, Any]] = {}

    for event_id, event_name in event_id_to_name.items():
        component, p_origin, p_target = _parse_event_name(event_name)

        if p_target not in percentiles:
            # Evento fuera del esquema configurado
            continue

        percentile_index = percentiles.index(p_target)
        intensity = (percentile_index + 1) / n_percentiles

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

    return enriched


# -------------------------------------------------------------------------
# Carga de ficheros
# -------------------------------------------------------------------------

def _load_event_dictionary(path: Path) -> Dict[int, str]:
    """
    Carga JSON event_name -> event_id
    y devuelve event_id -> event_name
    """
    if not path.exists():
        raise FileNotFoundError(f"Event dictionary no encontrado: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return {int(v): k for k, v in data.items()}


def _load_components(path: Path) -> Dict[str, Any]:
    """
    Carga components.yml
    """
    if not path.exists():
        raise FileNotFoundError(f"Components config no encontrado: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return data.get("components", {})


# -------------------------------------------------------------------------
# Parsing de eventos
# -------------------------------------------------------------------------

_EVENT_REGEX = re.compile(
    r"^(?P<component>.+?)_Q(?P<q1>\d+)(?:_to_Q(?P<q2>\d+))?$"
)


def _parse_event_name(event_name: str) -> tuple[str, str, str]:
    """
    Devuelve:
      component, percentile_origin, percentile_target
    """
    match = _EVENT_REGEX.match(event_name)
    if not match:
        raise ValueError(f"Formato de evento no reconocido: {event_name}")

    component = match.group("component")
    q1 = f"Q{match.group('q1')}"
    q2 = match.group("q2")

    if q2:
        q2 = f"Q{q2}"
        return component, q1, q2

    # Evento simple
    return component, q1, q1


# -------------------------------------------------------------------------
# Color
# -------------------------------------------------------------------------

def _adjust_color_intensity(hex_color: str, intensity: float) -> str:
    """
    Ajusta la intensidad del color (0..1).
    Devuelve rgb(r,g,b)
    """
    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    r = int(r * intensity)
    g = int(g * intensity)
    b = int(b * intensity)

    return f"rgb({r},{g},{b})"
