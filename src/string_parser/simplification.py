"""Remove redundant branches and describe suggested changes."""

from __future__ import annotations

from ._tree import _collect_and_exprs, _collect_and_terms, _collect_or_branches, _rebuild_binary
from .analysis import (
    _branch_subsumes,
    _is_subphrase,
    find_and_redundancies,
    find_duplicate_terms,
    find_subsumed_branches,
)
from .ast import BinaryExpr, Expr, Op, Term, UnaryExpr
from .parser import parse
from .rendering import unparse


def simplify(expr: Expr) -> Expr:
    """Return a new expression with redundancies removed.

    - OR: removes branches subsumed by a sibling (including duplicate branches).
    - AND: removes broader terms made redundant by a narrower sibling term.
    """
    if isinstance(expr, UnaryExpr):
        return UnaryExpr(expr.op, simplify(expr.operand))

    if not isinstance(expr, BinaryExpr):
        return expr

    if expr.op == Op.OR:
        branches = [simplify(b) for b in _collect_or_branches(expr)]
        branch_terms = [_collect_and_terms(b) for b in branches]
        seen: set[frozenset[str]] = set()
        keep: list[Expr] = []
        for i, (b, t) in enumerate(zip(branches, branch_terms)):
            key = frozenset(t)
            if key in seen:
                continue
            if t and any(j != i and bt and _branch_subsumes(bt, t) for j, bt in enumerate(branch_terms)):
                continue
            if key:
                seen.add(key)
            keep.append(b)
        return _rebuild_binary(Op.OR, keep or branches)

    if expr.op == Op.AND:
        and_exprs = [simplify(e) for e in _collect_and_exprs(expr)]
        normed = [e.value.lower().strip('"') if isinstance(e, Term) else None for e in and_exprs]
        keep_and = [
            e
            for i, e in enumerate(and_exprs)
            if (n_i := normed[i]) is None
            or not any(
                j != i and (n_j := normed[j]) is not None and _is_subphrase(n_i, n_j) for j in range(len(and_exprs))
            )
        ]
        return _rebuild_binary(Op.AND, keep_and or and_exprs)

    return expr


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


def suggest_simplification(string: str) -> str | None:
    """Return a simplified string if redundancies were found, else None."""
    expr = parse(string)
    simplified = unparse(simplify(expr))
    original = unparse(expr)
    return simplified if simplified != original else None
