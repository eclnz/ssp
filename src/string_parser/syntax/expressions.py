"""Expression model, structural operations, and query serialization."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import Enum
from typing import Literal, TypeAlias


class Op(Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


@dataclass(frozen=True)
class Term:
    value: str  # a search term or quoted phrase e.g. "high flow"


@dataclass(frozen=True)
class BinaryExpr:
    op: Op  # AND or OR
    left: Expr
    right: Expr

    def __post_init__(self) -> None:
        if self.op not in (Op.AND, Op.OR):
            raise ValueError("Binary expressions require AND or OR")


@dataclass(frozen=True)
class UnaryExpr:
    op: Op  # NOT
    operand: Expr

    def __post_init__(self) -> None:
        if self.op is not Op.NOT:
            raise ValueError("Unary expressions require NOT")


Expr = Term | BinaryExpr | UnaryExpr


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


TermKey: TypeAlias = tuple[Literal["term"], str]
UnaryKey: TypeAlias = tuple[Literal["not"], "CanonicalKey"]
BinaryKey: TypeAlias = tuple[Literal["AND", "OR"], tuple["CanonicalKey", ...]]
CanonicalKey: TypeAlias = TermKey | UnaryKey | BinaryKey


def canonical_key(expr: Expr) -> CanonicalKey:
    """Identity modulo AND/OR association and order, preserving raw terms.

    This is not complete Boolean equivalence: duplicate operands and other
    logical rewrites remain distinct.
    """
    if isinstance(expr, Term):
        return ("term", expr.value)
    if isinstance(expr, UnaryExpr):
        return ("not", canonical_key(expr.operand))
    operator = "AND" if expr.op is Op.AND else "OR"
    operands = sorted(canonical_key(node) for node in flatten(expr, expr.op))
    return (operator, tuple(operands))


def unparse(expr: Expr) -> str:
    """Serialize an expression tree as a Boolean query."""
    if isinstance(expr, Term):
        return expr.value  # preserves original quoting
    if isinstance(expr, UnaryExpr):
        return f"NOT {unparse(expr.operand)}"
    return f"({unparse(expr.left)} {expr.op.value} {unparse(expr.right)})"
