# app/core/_4_query_engine.py

from typing import Optional, Dict, Any

import pandas as pd
import numpy as np

from core._3_input_controller import QueryPattern
from core.dsl_ast import (
    Expr,
    Value,
    AnyOne,
    Star,
    Sequence,
    Has,
    Or,
    And,
    Not
)


# -------------------------------------------------------------------------
# API principal
# -------------------------------------------------------------------------

def run_query(
    df: pd.DataFrame,
    src_pattern: Optional[QueryPattern],
    dst_pattern: Optional[QueryPattern],
    config: Dict[str, Any]
) -> pd.DataFrame:

    if src_pattern is None and dst_pattern is None:
        return df

    result = df
    separator = config["processing"]["separator"]

    if src_pattern is not None:
        result = _apply_pattern(result, src_pattern, 0, separator)

    if dst_pattern is not None:
        result = _apply_pattern(result, dst_pattern, 1, separator)

    return result


# -------------------------------------------------------------------------
# Aplicación de patrones
# -------------------------------------------------------------------------

def _apply_pattern(
    df: pd.DataFrame,
    pattern: QueryPattern,
    level: int,
    separator: str
) -> pd.DataFrame:

    full_index = df.index
    level_values = full_index.get_level_values(level)

    bool_mask = evaluate_expr(pattern.ast, level_values, separator)

    # bool_mask es np.ndarray → lo alineamos al índice completo
    return df[pd.Series(bool_mask, index=full_index)]


# -------------------------------------------------------------------------
# Evaluación semántica del AST
# -------------------------------------------------------------------------

def evaluate_expr(expr: Expr, values: pd.Index, separator: str) -> np.ndarray:
    """
    values: pd.Index
    returns: np.ndarray[bool]
    """

    # -------------------------
    # ATÓMICOS
    # -------------------------
    if isinstance(expr, Value):
        # Comparación exacta optimizada
        return np.asarray(values == expr.canonical(), dtype=bool)

    if isinstance(expr, Star):
        return np.ones(len(values), dtype=bool)

    if isinstance(expr, AnyOne):
        return np.ones(len(values), dtype=bool)

    # -------------------------
    # SECUENCIA
    # -------------------------
    if isinstance(expr, Sequence):
        parts = expr.parts

        # Caso exacto (solo Values)
        if all(isinstance(p, Value) for p in parts):
            full = separator.join(p.canonical() for p in parts)
            return np.asarray(values == full, dtype=bool)

        # Regex estructural
        regex_parts = []
        for p in parts:
            if isinstance(p, Value):
                regex_parts.append(re_escape(p.canonical())) # Buena práctica escapar
            elif isinstance(p, AnyOne):
                regex_parts.append(r"\d+")
            elif isinstance(p, Star):
                # CORRECCIÓN: Usar .* para permitir que el join maneje los separadores
                # y no exigir comas dobles.
                regex_parts.append(r".*")

        regex = "^" + separator.join(regex_parts) + "$"
        
        return np.asarray(values.str.match(regex, na=False), dtype=bool)

    # -------------------------
    # HAS {}
    # -------------------------
    if isinstance(expr, Has):
        val = expr.expr.canonical()
        # Regex para "contiene valor exacto": al principio, en medio o al final
        pattern = rf"(?:^|{separator}){val}(?:{separator}|$)"
        return np.asarray(values.str.contains(pattern, regex=True, na=False), dtype=bool)

    # -------------------------
    # LÓGICOS
    # -------------------------
    if isinstance(expr, Or):
        masks = [evaluate_expr(e, values, separator) for e in expr.items]
        return np.logical_or.reduce(masks)

    if isinstance(expr, And):
        masks = [evaluate_expr(e, values, separator) for e in expr.items]
        return np.logical_and.reduce(masks)

    if isinstance(expr, Not):
        return ~evaluate_expr(expr.item, values, separator)

    raise TypeError(f"Expr no soportada: {type(expr)}")

def re_escape(s: str) -> str:
    import re
    return re.escape(s)