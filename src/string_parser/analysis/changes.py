"""Term inventory comparison, explicitly separate from structural comparison."""

from collections.abc import Callable
from typing import NamedTuple

from ..syntax.ast import Expr
from .terms import collect_terms


class TermChanges(NamedTuple):
    added: set[str]
    removed: set[str]


def compare_terms(old: Expr, new: Expr, *, key: Callable[[str], str] | None = None) -> TermChanges:
    """Compare inventories only; operators and negation do not affect this report."""
    before, after = collect_terms(old, key=key), collect_terms(new, key=key)
    return TermChanges(after - before, before - after)
