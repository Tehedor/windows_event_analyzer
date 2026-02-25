# app/core/_3_input_controller.py

import logging
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Union

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

logger = logging.getLogger("uvicorn")

@dataclass
class QueryPattern:
    """
    Representa un patrón de búsqueda ya procesado y convertido a AST.
    """
    raw: str
    canonical: str
    ast: Expr
    target: str

# -------------------------------------------------------------------------
# API Principal
# -------------------------------------------------------------------------
def parse_pattern(raw_pattern: str, column_type: str, config: Dict[str, Any]) -> QueryPattern:
    """
    Parsea un string de consulta (DSL) y devuelve un objeto QueryPattern compilado.
    """
    logger.info(f"🔎 parse_pattern llamado con: {raw_pattern!r} (tipo: {column_type})")
    
    # 1. Validaciones básicas
    if not isinstance(raw_pattern, str) or not raw_pattern.strip():
        # Si llega vacío, devolvemos un patrón que no hace match con nada o match con todo
        # Según tu lógica de negocio, ajusta esto. Aquí asumo error o Wildcard.
        # Para mantener compatibilidad con tu código anterior:
        return QueryPattern(raw="", canonical="", ast=Star(), target=column_type)

    assert column_type in ("observation", "prediction"), f"Tipo inválido: {column_type}"
    assert isinstance(config, dict), "Config debe ser un diccionario"

    # 2. Tokenización (Detecta números, símbolos y @Alias)
    tokens = tokenize(raw_pattern)
    logger.info(f"📝 Tokens generados: {tokens}")

    # 3. Parsing y Construcción del AST (Aquí se resuelven los Alias usando config)
    ast = parse(tokens, config)

    # 4. Generación de forma canónica (String único que representa la lógica)
    canonical = ast.canonical()

    return QueryPattern(
        raw=raw_pattern,
        canonical=canonical,
        ast=ast,
        target=column_type
    )

# -------------------------------------------------------------------------
# Tokenizer (Usando Regex para mayor robustez)
# -------------------------------------------------------------------------
TOKEN_REGEX = re.compile(r"""
    (\s+) |                      # 1. Espacios (Ignorar)
    (@[a-zA-Z0-9_\-]+) |         # 2. ALIAS: Empieza por @, permite letras, nums, _ y -
    (\d+) |                      # 3. NÚMEROS: Uno o más dígitos
    ([,]) |                      # 4. Coma (Separador de secuencia)
    ([|]) |                      # 5. OR lógico
    (&) |                        # 6. AND lógico
    (!) |                        # 7. NOT lógico
    ([{]) |                      # 8. Inicio Set
    ([}]) |                      # 9. Fin Set
    (\() |                       # 10. Inicio Paréntesis
    (\)) |                       # 11. Fin Paréntesis
    (\*) |                       # 12. Wildcard (Star)
    (\?)                         # 13. Wildcard (AnyOne)
""", re.VERBOSE)

def tokenize(text: str) -> List[Union[str, int]]:
    tokens = []
    cursor = 0
    length = len(text)

    # Bucle de escaneo regex
    while cursor < length:
        match = TOKEN_REGEX.match(text, cursor)
        if not match:
            raise ValueError(f"Carácter inválido en posición {cursor}: {text[cursor]!r}")
        
        # Grupos del regex:
        # 1: Espacios -> Ignorar
        # 2: Alias (@Name) -> Guardar como string
        # 3: Número -> Convertir a int
        # 4-13: Símbolos -> Guardar como string

        if match.group(2): # Alias
            tokens.append(match.group(2))
        elif match.group(3): # Número
            tokens.append(int(match.group(3)))
        elif match.group(1): # Espacios
            pass 
        else: # Símbolos
            tokens.append(match.group(0))
        
        cursor = match.end()

    return tokens

# -------------------------------------------------------------------------
# Parser (Recursive Descent + Alias Resolution)
# -------------------------------------------------------------------------
def parse(tokens: List[Union[str, int]], config: Dict[str, Any]) -> Expr:
    if not tokens:
        raise ValueError("No se puede parsear una lista de tokens vacía")

    # 1. Paréntesis externos (Azúcar sintáctico)
    # --------------------------------------------------
    # Nota: Chequeamos balanceo básico para no quitar paréntesis que no envuelven todo
    if tokens[0] == "(" and tokens[-1] == ")":
        # Verificamos si los paréntesis externos realmente envuelven toda la expresión
        # y no son casos como "(1,2), (3,4)"
        depth = 0
        covers_all = True
        for i, t in enumerate(tokens[:-1]):
            if t == "(": depth += 1
            elif t == ")": depth -= 1
            if depth == 0: 
                covers_all = False
                break
        
        if covers_all:
             return parse(tokens[1:-1], config)

    # 2. OR Lógico (Nivel 0)
    # --------------------------------------------------
    or_parts = split_top_level(tokens, "|")
    if len(or_parts) > 1:
        return Or(frozenset(parse(p, config) for p in or_parts))

    # 3. AND Lógico (Nivel 0)
    # --------------------------------------------------
    and_parts = split_top_level(tokens, "&")
    if len(and_parts) > 1:
        return And(frozenset(parse(p, config) for p in and_parts))

    # 4. HAS { ... } (Sets)
    # --------------------------------------------------
    if tokens[0] == "{":
        if tokens[-1] != "}":
            raise ValueError("Bloque '{' debe cerrarse con '}'")
        # Parseamos lo de adentro recursivamente (permite lógica dentro del set)
        inner_expr = parse(tokens[1:-1], config)
        return Has(inner_expr)

    # 5. NOT Unario
    # --------------------------------------------------
    if tokens[0] == "!":
        return Not(parse(tokens[1:], config))

    # 6. Secuencia o Atómico
    # --------------------------------------------------
    return parse_sequence(tokens, config)


def parse_sequence(tokens: List[Union[str, int]], config: Dict[str, Any]) -> Expr:
    """
    Maneja secuencias separadas por comas.
    Aquí es donde resolvemos los ALIAS y los valores atómicos.
    """
    parts = []
    
    # Dividimos por comas respetando paréntesis/llaves anidados
    current_segment = []
    depth = 0
    
    segments = []
    for tok in tokens:
        if tok == "(": depth += 1
        elif tok == ")": depth -= 1
        elif tok == "{": depth += 1
        elif tok == "}": depth -= 1
        
        if tok == "," and depth == 0:
            if not current_segment:
                raise ValueError("Segmento vacío en secuencia (coma extra?)")
            segments.append(current_segment)
            current_segment = []
        else:
            current_segment.append(tok)
            
    if current_segment:
        segments.append(current_segment)

    # Procesar cada segmento
    for seg in segments:
        if len(seg) == 1:
            item = seg[0]
            if isinstance(item, int):
                parts.append(Value(item))
            elif item == "*":
                parts.append(Star())
            elif item == "?":
                parts.append(AnyOne())
            elif isinstance(item, str) and item.startswith("@"):
                # --- RESOLUCIÓN DE ALIAS ---
                alias_node = resolve_alias(item, config)
                parts.append(alias_node)
            else:
                # Si es un segmento de un solo token pero no es atómico conocido
                # (ej: un sub-bloque malformado), intentamos parsearlo general
                parts.append(parse(seg, config))
        else:
            # Si el segmento tiene varios tokens (ej: "(1|2)" o "!{511}")
            # llamamos a parse recursivamente
            parts.append(parse(seg, config))

    if len(parts) == 1:
        return parts[0]
    
    return Sequence(tuple(parts))


def resolve_alias(alias_token: str, config: Dict[str, Any]) -> Expr:
    """
    Busca el alias en la configuración y devuelve un nodo AST.
    @Alias -> Value(x)  O  Or(Value(x), Value(y)...)
    """
    name = alias_token[1:] # Quitar '@'

    logger.info(f"🔍 Resolviendo alias: {alias_token} (componente: {name})")
    
    # Busca en config['components'] o config['datasets']['components'] según estructura
    components = config.get("components")
    if not components:
        # Intento de fallback por si la estructura de config es distinta
        components = config.get("datasets", {}).get("components")

    if not components or name not in components:
        logger.error(f"❌ Alias desconocido: {alias_token}")
        raise ValueError(f"Alias desconocido o configuración vacía: {alias_token}")

    values = components[name]
    if not values:
        logger.error(f"❌ Alias vacío: {alias_token}")
        raise ValueError(f"El alias {alias_token} está vacío en la configuración")

    logger.info(f"✅ Alias {alias_token} expandido a {len(values)} valores: {values}")

    # Convertir lista de ints a nodos Value
    value_nodes = [Value(v) for v in values]

    if len(value_nodes) == 1:
        logger.debug(f"   → Resultado: Value({values[0]})")
        return value_nodes[0]
    
    # Si hay múltiples valores, es un OR lógico (uno de estos valores)
    logger.debug(f"   → Resultado: Or({', '.join(str(v) for v in values)})")
    return Or(frozenset(value_nodes))


def split_top_level(tokens: List, operator: str) -> List[List]:
    """Helper para dividir tokens por un operador solo en nivel 0 de paréntesis."""
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
                raise ValueError(f"Operador '{operator}' con lado vacío")
            parts.append(current)
            current = []
        else:
            current.append(tok)

    if level != 0:
        raise ValueError("Paréntesis o llaves desbalanceados")

    if not current:
        raise ValueError(f"Operador '{operator}' con lado final vacío")

    parts.append(current)
    return parts