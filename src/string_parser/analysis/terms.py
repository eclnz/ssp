"""Term identity and complete positive-conjunction projections."""

from __future__ import annotations

from ..syntax.ast import BinaryExpr, Expr, Op, Term
from ..syntax.tree import flatten, walk


def term_key(value: str) -> str:
    """Lexical identity used by term reports and phrase matching, not structural equality."""
    return value.lower().strip('"')


def collect_terms(expr: Expr) -> set[str]:
    """Collect lexical terms regardless of polarity; not a meaning comparison."""
    return {term_key(node.value) for node in walk(expr) if isinstance(node, Term)}


def conjunction_terms(expr: Expr) -> frozenset[str] | None:
    """Return all terms for a positive conjunction, or None if it contains OR/NOT.

    None means unsupported, never an empty or partially understood branch.
    """
    if not isinstance(expr, (Term, BinaryExpr)):
        return None
    operands = flatten(expr, Op.AND)
    if not all(isinstance(node, Term) for node in operands):
        return None
    return frozenset(node.value for node in operands if isinstance(node, Term))
