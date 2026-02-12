# app/helpers/_3_input_controller.py
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any
from core.dsl_ast import (
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
# Normalización de entrada
# -------------------------------------------------------------------------
def parse_pattern(raw_pattern: str, column_type: str, config: dict) -> QueryPattern:
    assert isinstance(raw_pattern, str) and raw_pattern.strip(), \
        "raw_pattern debe ser un string no vacío"

    assert column_type in ("observation", "prediction"), \
        f"column_type inválido: {column_type}"

    assert isinstance(config, dict), "config debe ser un dict"

    expanded = expand_aliases(raw_pattern, config)

    assert isinstance(expanded, str) and expanded.strip(), \
        "expand_aliases debe devolver un string no vacío"

    tokens = tokenize(expanded)

    assert isinstance(tokens, list) and tokens, \
        "tokenize debe devolver una lista no vacía de tokens"

    ast = parse(tokens)

    assert isinstance(ast, Expr), \
        "parse debe devolver una instancia de Expr"

    canonical = ast.canonical()

    assert isinstance(canonical, str) and canonical, \
        "canonical debe ser un string no vacío"

    return QueryPattern(
        raw=raw_pattern,
        canonical=canonical,
        ast=ast,
        target=column_type
    )



def expand_aliases(raw: str, config: dict) -> str:
    assert isinstance(raw, str)

    components = config.get("components")
    if not components:
        return raw

    def replace_alias(match):
        name = match.group(1)

        if name not in components:
            raise ValueError(f"Alias desconocido: @{name}")

        values = components[name]

        if not values:
            raise ValueError(f"Alias vacío: @{name}")

        # un solo valor → "511"
        if len(values) == 1:
            return str(values[0])

        # varios valores → "(475 | 612)"
        inner = " | ".join(str(v) for v in values)
        return f"({inner})"

    # @AliasName
    return re.sub(r"@([A-Za-z0-9_\-]+)", replace_alias, raw)


def tokenize(expr: str) -> list:
    assert isinstance(expr, str)
    assert expr.strip(), "tokenize recibió string vacío"

    tokens = []
    i = 0
    n = len(expr)

    SYMBOLS = set("(),{}|&!*?,")

    while i < n:
        ch = expr[i]

        # Ignorar espacios y puntos
        if ch.isspace() or ch == ".":
            i += 1
            continue

        # Número (uno o más dígitos)
        if ch.isdigit():
            start = i
            while i < n and expr[i].isdigit():
                i += 1
            tokens.append(int(expr[start:i]))
            continue

        # Símbolos del DSL
        if ch in SYMBOLS:
            tokens.append(ch)
            i += 1
            continue

        # Cualquier otra cosa es error
        raise ValueError(f"Carácter no válido en DSL: {ch!r}")

    return tokens


def parse(tokens: list) -> Expr:
    assert isinstance(tokens, list)
    assert tokens, "parse recibió lista de tokens vacía"

    # --------------------------------------------------
    # Paréntesis (azúcar sintáctico)
    # --------------------------------------------------
    if tokens[0] == "(" and tokens[-1] == ")":
        if len(tokens) <= 2:
            raise ValueError("Paréntesis vacíos no permitidos")
        return parse(tokens[1:-1])

    # --------------------------------------------------
    # OR lógico (menor prioridad, SOLO a nivel 0)
    # --------------------------------------------------
    or_parts = split_top_level(tokens, "|")
    if len(or_parts) > 1:
        return Or(frozenset(parse(p) for p in or_parts))

    # --------------------------------------------------
    # AND lógico (prioridad media, SOLO a nivel 0)
    # --------------------------------------------------
    and_parts = split_top_level(tokens, "&")
    if len(and_parts) > 1:
        return And(frozenset(parse(p) for p in and_parts))

    # --------------------------------------------------
    # HAS { ... }
    # --------------------------------------------------
    if tokens[0] == "{":
        if tokens[-1] != "}":
            raise ValueError("Bloque '{' debe cerrarse con '}'")
        if len(tokens) <= 2:
            raise ValueError("Bloque '{}' no puede estar vacío")

        inner_expr = parse(tokens[1:-1])
        return Has(inner_expr)

    # --------------------------------------------------
    # NOT unario
    # --------------------------------------------------
    if tokens[0] == "!":
        if len(tokens) == 1:
            raise ValueError("El operador '!' debe ir seguido de una expresión")
        return Not(parse(tokens[1:]))

    # --------------------------------------------------
    # Secuencia simple: valor , valor , valor
    # --------------------------------------------------
    parts = []
    expect_value = True

    for tok in tokens:
        if expect_value:
            if isinstance(tok, int):
                parts.append(Value(tok))
            elif tok == "*":
                parts.append(Star())
            elif tok == "?":
                parts.append(AnyOne())
            else:
                raise ValueError(f"Token inesperado en secuencia: {tok!r}")
            expect_value = False
        else:
            if tok != ",":
                raise ValueError(f"Se esperaba ',' y se recibió {tok!r}")
            expect_value = True

    if expect_value:
        raise ValueError("La secuencia no puede terminar en ','")

    if len(parts) == 1:
        return parts[0]

    return Sequence(tuple(parts))



def split_top_level(tokens, operator):
    parts = []
    current = []
    level = 0

    for tok in tokens:
        if tok in ("(", "{"):
            level += 1
        elif tok in (")", "}"):
            level -= 1

        if tok == operator and level == 0:
            if not current:
                raise ValueError(f"{operator} mal formado: lado vacío")
            parts.append(current)
            current = []
        else:
            current.append(tok)

    if level != 0:
        raise ValueError("Paréntesis o llaves desbalanceados")

    if not current:
        raise ValueError(f"{operator} mal formado: lado vacío")

    parts.append(current)
    return parts
