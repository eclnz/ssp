"""Compose expressions into larger queries."""

from __future__ import annotations

from .ast import BinaryExpr, Expr, Op


def combine(*exprs: Expr) -> Expr:
    """OR together multiple expressions — use when analysing a set of search strings jointly."""
    if not exprs:
        raise ValueError("At least one expression required")
    result = exprs[0]
    for e in exprs[1:]:
        result = BinaryExpr(Op.OR, result, e)
    return result
