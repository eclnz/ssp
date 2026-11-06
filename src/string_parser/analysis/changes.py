"""Classify added and removed terms between queries."""

from __future__ import annotations

from ..syntax.parser import parse
from .terms import collect_terms


def classify_change(old: str, new: str) -> tuple[set[str], set[str]]:
    """Return (added_terms, removed_terms) between two search strings."""
    old_terms = collect_terms(parse(old))
    new_terms = collect_terms(parse(new))
    return new_terms - old_terms, old_terms - new_terms
