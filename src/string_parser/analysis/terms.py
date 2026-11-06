"""Raw term inventories and their comparison."""

from __future__ import annotations

from collections.abc import Callable
from typing import NamedTuple

from ..syntax.expressions import Expr, Term, walk


def collect_terms(expr: Expr, *, key: Callable[[str], str] | None = None) -> set[str]:
    """Collect raw terms regardless of polarity; optional identity is caller-owned."""
    terms = {node.value for node in walk(expr) if isinstance(node, Term)}
    return {key(term) for term in terms} if key is not None else terms


class TermChanges(NamedTuple):
    added: set[str]
    removed: set[str]


def compare_terms(old: Expr, new: Expr, *, key: Callable[[str], str] | None = None) -> TermChanges:
    """Compare inventories only; operators and negation do not affect this report."""
    before, after = collect_terms(old, key=key), collect_terms(new, key=key)
    return TermChanges(after - before, before - after)
