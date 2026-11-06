"""Expression tree types for Boolean queries."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Op(Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


@dataclass
class Term:
    value: str  # a search term or quoted phrase e.g. "high flow"


@dataclass
class BinaryExpr:
    op: Op  # AND or OR
    left: Expr
    right: Expr


@dataclass
class UnaryExpr:
    op: Op  # NOT
    operand: Expr


Expr = Term | BinaryExpr | UnaryExpr
