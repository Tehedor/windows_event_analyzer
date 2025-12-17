# app/helpers/_6_event_dictionary.py
import json
from pathlib import Path
from typing import Dict


def load_event_dictionary(path: Path) -> Dict[int, str]:
    """
    Carga el diccionario de eventos desde JSON.
    Devuelve: {event_id: event_name}
    """
    if not path.exists():
        raise FileNotFoundError(f"Event dictionary no encontrado: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Asegurar claves int
    return {int(v): k for k, v in data.items()}
