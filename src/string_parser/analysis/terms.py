"""Collect normalized terms without modifying expressions."""

from __future__ import annotations

from ..syntax.ast import Expr, Term, UnaryExpr


def collect_terms(expr: Expr) -> set[str]:
    """Return the set of all leaf terms in an expression, lowercased for comparison."""
    if isinstance(expr, Term):
        return {expr.value.lower().strip('"')}
    elif isinstance(expr, UnaryExpr):
        return collect_terms(expr.operand)
    else:
        return collect_terms(expr.left) | collect_terms(expr.right)
