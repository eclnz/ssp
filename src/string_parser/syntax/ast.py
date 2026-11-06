"""Operators and expression tree types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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
