"""Canonicalization and proven expression rewrites."""

from __future__ import annotations

from .analysis.matching import EXACT, TermMatcher
from .analysis.redundancy import find_redundant_operands
from .syntax.expressions import BinaryExpr, Expr, Op, Term, UnaryExpr, canonical_key, flatten, rebuild


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
        branches = sorted([canonicalize(b) for b in flatten(expr, Op.OR)], key=canonical_key)
        return rebuild(Op.OR, branches)
    if expr.op == Op.AND:
        operands = sorted([canonicalize(e) for e in flatten(expr, Op.AND)], key=canonical_key)
        return rebuild(Op.AND, operands)
    return expr


def simplify(expr: Expr, *, matcher: TermMatcher = EXACT) -> Expr:
    """Return a new tree; matching defaults to exact raw-term identity."""
    if isinstance(expr, UnaryExpr):
        return UnaryExpr(expr.op, simplify(expr.operand, matcher=matcher))
    if not isinstance(expr, BinaryExpr):
        return expr
    group = rebuild(expr.op, (simplify(node, matcher=matcher) for node in flatten(expr, expr.op)))
    if not isinstance(group, BinaryExpr):
        return group
    removed = {item.redundant_index for item in find_redundant_operands(group, matcher=matcher)}
    return rebuild(group.op, (node for i, node in enumerate(flatten(group, group.op)) if i not in removed))
