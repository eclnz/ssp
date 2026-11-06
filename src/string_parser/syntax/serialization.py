"""Serialize expression trees back to query text."""

from __future__ import annotations

from .ast import Expr, Term, UnaryExpr


def unparse(expr: Expr) -> str:
    """Reconstruct a PubMed search string from an expression tree."""
    if isinstance(expr, Term):
        return expr.value  # preserves original quoting
    if isinstance(expr, UnaryExpr):
        return f"NOT {unparse(expr.operand)}"
    return f"({unparse(expr.left)} {expr.op.value} {unparse(expr.right)})"
