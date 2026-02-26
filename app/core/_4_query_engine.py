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
# app/core/_4_query_engine.py

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
                regex_parts.append(re_escape(p.canonical()))
            elif isinstance(p, AnyOne):
                regex_parts.append(r"\d+")
            elif isinstance(p, Star):
                # 🚀 SOLUCIÓN: El asterisco debe hacer match con CUALQUIER cosa (incluyendo separadores)
                # o con NADA. Usamos .* para permitir esto en la construcción final.
                regex_parts.append(r".*")
            elif isinstance(p, Or):
                or_vals = []
                def extract_or_values(or_node):
                    for item in or_node.items:
                        if isinstance(item, Value):
                            or_vals.append(item.canonical())
                        elif isinstance(item, Or):
                            extract_or_values(item)
                extract_or_values(p)
                
                if or_vals:
                    escaped_vals = [re_escape(v) for v in or_vals]
                    # No necesitamos los separadores ^|$ aquí, porque el join() de abajo se encargará de ellos
                    # en el contexto de la secuencia completa.
                    or_group = f"(?:{'|'.join(escaped_vals)})"
                    regex_parts.append(or_group)
                else:
                    regex_parts.append(r"(?!x)x")

        # 🚀 SOLUCIÓN DEFINITIVA PARA LA UNIÓN DE REGEX:
        # En lugar de intentar adivinar dónde poner los separadores opcionales, 
        # dejamos que Python haga un join() normal, pero lidiamos con el caso especial
        # donde un '.*' queda pegado a un separador (ej: '.*,49').
        #
        # Al hacer separator.join(regex_parts), si tenemos [".*", "49", ".*"], 
        # el resultado será ".*,49,.*". 
        # Como ".*" ya se come todo, exigir una coma exacta choca.
        # Lo que necesitamos es que si hay un '.*', los separadores adyacentes sean opcionales.
        
        raw_regex = separator.join(regex_parts)
        
        # Reemplazamos los separadores literales pegados a '.*' para que sean opcionales
        safe_sep = re_escape(separator)
        # Permite '.*,' o '.*'
        raw_regex = raw_regex.replace(f".*{safe_sep}", f".*(?:{safe_sep})?")
        # Permite ',.*' o '.*'
        raw_regex = raw_regex.replace(f"{safe_sep}.*", f"(?:{safe_sep})?.*")

        regex = f"^{raw_regex}$"
        return np.asarray(values.str.match(regex, na=False), dtype=bool)

    # -------------------------
    # HAS {}
    # -------------------------
    if isinstance(expr, Has):
        if isinstance(expr.expr, Or):
            masks = [evaluate_expr(Has(e), values, separator) for e in expr.expr.items]
            return np.logical_or.reduce(masks)
        else:
            val = expr.expr.canonical()
            pattern = rf"(?:^|{separator}){val}(?:{separator}|$)"
            return np.asarray(values.str.contains(pattern, regex=True, na=False), dtype=bool)

    # -------------------------
    # LÓGICOS (Nivel superior)
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