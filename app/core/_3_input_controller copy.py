# app/helpers/_3_input_controller.py
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any
from dsl_ast import (
    Expr,
    Value,
    AnyOne,
    Star,
    Sequence,
    Has,
    Or,
    And,
    Not,
)


@dataclass
class QueryPattern:
    """
    Representa un patrón de búsqueda ya procesado.
    """
    raw: str
    canonical: str
    ast: Expr
    target: str

# -------------------------------------------------------------------------
# API principal
# -------------------------------------------------------------------------
def parse_pattern(raw_pattern: str, column_type: str, config: dict) -> QueryPattern:
    expanded = expand_aliases(raw_pattern, config)
    tokens = tokenize(expanded)
    ast = parse(tokens)
    canonical = ast.canonical()

    return QueryPattern(
        raw=raw_pattern,
        canonical=canonical,
        ast=ast,
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

