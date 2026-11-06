"""Structural traversal and composition, independent of matching semantics."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from .ast import BinaryExpr, Expr, Op, UnaryExpr


def walk(expr: Expr) -> Iterator[Expr]:
    """Preorder traversal, retaining repeated occurrences."""
    yield expr
    if isinstance(expr, BinaryExpr):
        yield from walk(expr.left)
        yield from walk(expr.right)
    elif isinstance(expr, UnaryExpr):
        yield from walk(expr.operand)


def flatten(expr: Expr, op: Op) -> list[Expr]:
    """Flatten only adjacent occurrences of a binary operator."""
    if op not in (Op.AND, Op.OR):
        raise ValueError("A binary operator is required")
    if isinstance(expr, BinaryExpr) and expr.op is op:
        return flatten(expr.left, op) + flatten(expr.right, op)
    return [expr]


def rebuild(op: Op, operands: Iterable[Expr]) -> Expr:
    """Build a left-associated nonempty AND/OR expression."""
    if op not in (Op.AND, Op.OR):
        raise ValueError("A binary operator is required")
    items = iter(operands)
    try:
        result = next(items)
    except StopIteration:
        raise ValueError("At least one operand is required") from None
    for operand in items:
        result = BinaryExpr(op, result, operand)
    return result


def combine(*exprs: Expr) -> Expr:
    """Join expressions with OR."""
    return rebuild(Op.OR, exprs)


def structural_key(expr: Expr) -> tuple:
    """Hashable identity ignoring associative operand order, preserving raw terms."""
    if isinstance(expr, UnaryExpr):
        return ("not", structural_key(expr.operand))
    if isinstance(expr, BinaryExpr):
        return (expr.op.value, tuple(sorted(structural_key(node) for node in flatten(expr, expr.op))))
    return ("term", expr.value)
