"""Canonical forms and order-independent comparisons."""

from __future__ import annotations

from ..syntax.ast import Expr, Op, Term, UnaryExpr
from ..syntax.parser import parse
from ..syntax.serialization import unparse
from ..syntax.traversal import collect_and_exprs, collect_or_branches, rebuild_binary


def canonical_form(string: str) -> str:
    """Parse, canonicalize, and re-unparse a query — its order-independent normal form."""
    return unparse(canonicalize(parse(string)))


def canonically_equal(a: str, b: str) -> bool:
    """True if two query strings normalise to the same canonical form."""
    return canonical_form(a) == canonical_form(b)


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
        branches = sorted([canonicalize(b) for b in collect_or_branches(expr)], key=unparse)
        return rebuild_binary(Op.OR, branches)
    if expr.op == Op.AND:
        operands = sorted([canonicalize(e) for e in collect_and_exprs(expr)], key=unparse)
        return rebuild_binary(Op.AND, operands)
    return expr
