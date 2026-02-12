# core/dsl_ast.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, FrozenSet


# -------------------------
# Base
# -------------------------
class Expr:
    def canonical(self) -> str:
        raise NotImplementedError


# -------------------------
# Atómicos
# -------------------------
@dataclass(frozen=True)
class Value(Expr):
    value: int

    def canonical(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class AnyOne(Expr):
    def canonical(self) -> str:
        return "any"


@dataclass(frozen=True)
class Star(Expr):
    def canonical(self) -> str:
        return "star"


# -------------------------
# Secuencia
# -------------------------
@dataclass(frozen=True)
class Sequence(Expr):
    parts: Tuple[Expr, ...]

    def canonical(self) -> str:
        return "-".join(p.canonical() for p in self.parts)


# -------------------------
# Pertenencia
# -------------------------
@dataclass(frozen=True)
class Has(Expr):
    expr: Expr

    def canonical(self) -> str:
        return f"has-{self.expr.canonical()}"


# -------------------------
# Lógicos
# -------------------------
@dataclass(frozen=True)
class Or(Expr):
    items: FrozenSet[Expr]

    def canonical(self) -> str:
        flat = []

        for expr in self.items:
            if isinstance(expr, Or):
                # Aplanar OR anidados
                flat.extend(expr.items)
            else:
                flat.append(expr)

        def key(expr: Expr):
            c = expr.canonical()
            if c.isdigit():
                return (0, int(c))
            return (1, c)

        parts = [e.canonical() for e in sorted(flat, key=key)]
        return "-or-".join(parts)



@dataclass(frozen=True)
class And(Expr):
    items: FrozenSet[Expr]

    def canonical(self) -> str:
        flat = []

        for expr in self.items:
            if isinstance(expr, And):
                flat.extend(expr.items)
            else:
                flat.append(expr)

        def key(expr: Expr):
            c = expr.canonical()
            if c.isdigit():
                return (0, int(c))
            return (1, c)

        parts = [e.canonical() for e in sorted(flat, key=key)]
        return "-and-".join(parts)


@dataclass(frozen=True)
class Not(Expr):
    item: Expr

    def canonical(self) -> str:
        return f"not-{self.item.canonical()}"
