"""Canonicalize operand order without changing terms or applying rewrites."""

from ..syntax.ast import Expr, Op, Term, UnaryExpr
from ..syntax.tree import flatten, rebuild, structural_key


def canonicalize(expr: Expr) -> Expr:
    """Return an equivalent expression with OR and AND branches sorted deterministically.

    Two expressions that differ only in operand order will produce identical output
    after canonicalization, enabling reliable equality checks.
    """
    if isinstance(expr, Term):
        return expr
    if isinstance(expr, UnaryExpr):
        return UnaryExpr(expr.op, canonicalize(expr.operand))
    if expr.op == Op.OR:
        branches = sorted([canonicalize(b) for b in flatten(expr, Op.OR)], key=structural_key)
        return rebuild(Op.OR, branches)
    if expr.op == Op.AND:
        operands = sorted([canonicalize(e) for e in flatten(expr, Op.AND)], key=structural_key)
        return rebuild(Op.AND, operands)
    return expr
