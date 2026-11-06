"""Shared internal tree traversal and reconstruction helpers."""

from __future__ import annotations

from .ast import BinaryExpr, Expr, Op, Term


def _collect_and_terms(expr: Expr) -> set[str]:
    """Terms reachable through AND-only paths; stops (returns empty) at OR/NOT nodes."""
    if isinstance(expr, Term):
        return {expr.value.lower().strip('"')}
    if isinstance(expr, BinaryExpr) and expr.op == Op.AND:
        return _collect_and_terms(expr.left) | _collect_and_terms(expr.right)
    return set()


def _collect_or_branches(expr: Expr) -> list[Expr]:
    """Flatten consecutive OR nodes into a flat list of branches."""
    if isinstance(expr, BinaryExpr) and expr.op == Op.OR:
        return _collect_or_branches(expr.left) + _collect_or_branches(expr.right)
    return [expr]


def _collect_and_exprs(expr: Expr) -> list[Expr]:
    """Flatten consecutive AND nodes into a list of operands."""
    if isinstance(expr, BinaryExpr) and expr.op == Op.AND:
        return _collect_and_exprs(expr.left) + _collect_and_exprs(expr.right)
    return [expr]


def _rebuild_binary(op: Op, exprs: list[Expr]) -> Expr:
    result = exprs[0]
    for e in exprs[1:]:
        result = BinaryExpr(op, result, e)
    return result


def _collect_same_op(expr: BinaryExpr) -> list[Expr]:
    """Flatten left-associative same-operator nesting into a single operand list."""
    result: list[Expr] = []

    def collect(e: Expr) -> None:
        if isinstance(e, BinaryExpr) and e.op == expr.op:
            collect(e.left)
            collect(e.right)
        else:
            result.append(e)

    collect(expr.left)
    collect(expr.right)
    return result
