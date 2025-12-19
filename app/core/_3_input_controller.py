# app/helpers/_3_input_controller.py
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class QueryPattern:
    """
    Representa un patrón de búsqueda ya procesado.
    """
    raw: str          # lo que escribió el usuario (solo informativo)
    canonical: str    # representación canónica ÚNICA
    regex: str
    prefix: Optional[str]
    target: str

# -------------------------------------------------------------------------
# API principal
# -------------------------------------------------------------------------

def parse_pattern(
    raw_pattern: str,
    column_type: str,
    config: Dict[str, Any]
) -> QueryPattern:
    """
    Procesa un patrón introducido por el usuario y devuelve
    una estructura QueryPattern lista para usar.
    """

    if column_type not in ("observation", "prediction"):
        raise ValueError(f"column_type inválido: {column_type}")

    separator = config["processing"]["separator"]

    canonical = _normalize_input(raw_pattern, separator)
    regex, prefix = _build_regex_and_prefix(canonical, separator)

    return QueryPattern(
        raw=raw_pattern,
        canonical=canonical,
        regex=regex,
        prefix=prefix,
        target=column_type
    )


# -------------------------------------------------------------------------
# Normalización de entrada
# -------------------------------------------------------------------------

def _normalize_input(raw: str, separator: str) -> str:
    """
    Normaliza distintas formas de entrada del usuario a un formato común.
    Ejemplos aceptados:
      - "12,3,*"
      - "12 3 *"
      - "12.3.*"
    """

    s = raw.strip()

    # Separadores alternativos → separator oficial
    s = re.sub(r"[.\s]+", separator, s)

    # Eliminar separadores duplicados
    s = re.sub(rf"{re.escape(separator)}+", separator, s)

    # Quitar separadores al inicio/final
    s = s.strip(separator)

    return s


# -------------------------------------------------------------------------
# Construcción de regex / prefijo
# -------------------------------------------------------------------------
def _build_regex_and_prefix(normalized: str, separator: str):
    parts = normalized.split(separator)

    regex_parts = []
    prefix_parts = []

    has_star = False

    for part in parts:
        if part == "*":
            has_star = True
            break
        elif part == "?":
            regex_parts.append(r"\d+")
            prefix_parts.append(None)  # marcador
        else:
            regex_parts.append(re.escape(part))
            prefix_parts.append(part)

    # Parte base del patrón
    base_regex = separator.join(regex_parts)

    if has_star:
        # Prefijo estructural (solo hasta antes del *)
        prefix = separator.join(
            p for p in prefix_parts if p is not None
        ) if prefix_parts else None

        regex = f"^{base_regex}(?:{separator}.*)?$"
    else:
        # Match exacto
        prefix = None
        regex = f"^{base_regex}$"

    return regex, prefix
