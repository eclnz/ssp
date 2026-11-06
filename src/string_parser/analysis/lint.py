"""Describe query redundancies as human-readable diagnostics."""

from __future__ import annotations

from ..syntax.parser import parse
from .redundancy import find_and_redundancies, find_duplicate_terms, find_subsumed_branches


def lint_string(string: str) -> list[str]:
    """Return human-readable warnings about redundancies in a search string."""
    expr = parse(string)
    issues: list[str] = []

    for term in find_duplicate_terms(expr):
        issues.append(f"Duplicate term: {term!r} appears more than once")

    for broader, narrower in find_and_redundancies(expr):
        issues.append(
            f"AND redundancy: {broader!r} is always satisfied when {narrower!r} matches — {broader!r} can be removed"
        )

    for subsuming, subsumed in find_subsumed_branches(expr):
        issues.append(
            f"OR redundancy: ({' AND '.join(sorted(subsumed))}) is fully captured by "
            f"({' AND '.join(sorted(subsuming))}) — the narrower branch adds no coverage"
        )

    return issues
