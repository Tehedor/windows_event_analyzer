# app/core/_7_component_dictionary.py

from typing import Dict, Any
from collections import defaultdict

from core._6_event_dictionary import build_event_dictionary
from debug.debug import save_debug_info


def build_component_dictionary(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Construye el diccionario de componentes agrupando eventos por componente
    y lo devuelve (sin exportar a JSON).
    """
    # save_debug_info(config, filename="config_for_component_dictionary.json", head="Config used for Component Dictionary")
    # 1️⃣ Obtener event dictionary enriquecido
    event_dict = build_event_dictionary(config)
    # save_debug_info(event_dict, filename="event_dictionary_for_component_dictionary.json", head="Event Dictionary used for Component Dictionary")
    # 2️⃣ Agrupar por componente
    components: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "component": "",
        "events": [],
        "base_color": "#999999"
    })
    
    for event_id, event_data in event_dict.items():
        component = event_data["component"]
        
        components[component]["component"] = component
        components[component]["base_color"] = event_data["base_color"]
        components[component]["events"].append({
            "event_id": event_id,
            "event_name": event_data["event_name"],
            "percentile_origin": event_data["percentile_origin"],
            "percentile_target": event_data["percentile_target"],
            "final_color": event_data["final_color"],
            "intensity": event_data["intensity"],
        })
    save_debug_info(components, filename="component_dictionary_raw.json", head="Raw Component Dictionary before sorting")
    
    # 3️⃣ Convertir a dict normal y devolver
    return {k: dict(v) for k, v in components.items()}


def build_component_dictionary_compact(config: Dict[str, Any]) -> Dict[str, Dict[str, list[int]]]:
        """
        Construye un diccionario compacto con componente -> lista de event_id.

        Formato:
        {
            "components": {
                "Outlet_Temperature": [576, 577, ...],
                "MG-LV-MSB_Frequency": [504, 505, ...]
            }
        }
        """

        event_dict = build_event_dictionary(config)

        components: Dict[str, list[int]] = defaultdict(list)

        for event_id, event_data in event_dict.items():
                component = event_data["component"]
                components[component].append(event_id)

        # Ordenar ids y componentes
        for component in components:
                components[component].sort()

        return {"components": dict(sorted(components.items()))}
        # return {k: dict(v) for k, v in components.items()}