"""Raw term inventories with caller-selected normalization."""

from __future__ import annotations

from collections.abc import Callable

from ..syntax.ast import Expr, Term
from ..syntax.tree import walk


def collect_terms(expr: Expr, *, key: Callable[[str], str] | None = None) -> set[str]:
    """Collect raw terms regardless of polarity; optional identity is caller-owned."""
    terms = {node.value for node in walk(expr) if isinstance(node, Term)}
    return {key(term) for term in terms} if key is not None else terms
