"""Identify duplicate terms and redundant Boolean branches."""

from __future__ import annotations

from collections import Counter

from ..syntax.ast import BinaryExpr, Expr, Op, Term, UnaryExpr
from ..syntax.traversal import _collect_and_terms, _collect_or_branches
from .phrases import _branch_subsumes, _is_subphrase


def find_and_redundancies(expr: Expr) -> list[tuple[str, str]]:
    """Return (redundant_broader, necessary_narrower) pairs within AND context.

    In 'flow AND "high flow"', 'flow' is always satisfied when 'high flow' is — it adds no constraint.
    """
    results: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def walk(e: Expr) -> None:
        if isinstance(e, BinaryExpr):
            if e.op == Op.AND:
                for lt in _collect_and_terms(e.left):
                    for rt in _collect_and_terms(e.right):
                        pair = (lt, rt) if _is_subphrase(lt, rt) else (rt, lt) if _is_subphrase(rt, lt) else None
                        if pair and pair not in seen:
                            seen.add(pair)
                            results.append(pair)
            walk(e.left)
            walk(e.right)
        elif isinstance(e, UnaryExpr):
            walk(e.operand)

    walk(expr)
    return results


def find_absorbed_branches(expr: Expr) -> list[tuple[str, set[str]]]:
    """Return (absorbing_term, absorbed_and_terms) where 'T OR (A AND B)' simplifies to T.

    T absorbs an AND branch when T is a subphrase of (or equal to) at least one term in that branch —
    meaning every document matching the AND also matches T.
    """
    results: list[tuple[str, set[str]]] = []
    seen: set[tuple[str, frozenset[str]]] = set()

    def walk(e: Expr) -> None:
        if isinstance(e, BinaryExpr):
            if e.op == Op.OR:
                branches = _collect_or_branches(e)
                or_terms = [b.value.lower().strip('"') for b in branches if isinstance(b, Term)]
                and_branches = [_collect_and_terms(b) for b in branches if isinstance(b, BinaryExpr) and b.op == Op.AND]
                for t in or_terms:
                    for and_terms in and_branches:
                        if and_terms and any(t == at or _is_subphrase(t, at) for at in and_terms):
                            key = (t, frozenset(and_terms))
                            if key not in seen:
                                seen.add(key)
                                results.append((t, and_terms))
            walk(e.left)
            walk(e.right)
        elif isinstance(e, UnaryExpr):
            walk(e.operand)

    walk(expr)
    return results


def find_duplicate_terms(expr: Expr) -> list[str]:
    """Return terms that appear more than once anywhere in the expression tree.

    collect_terms deduplicates, so (A OR B) OR (A OR C) hides the duplicate A.
    """
    all_terms: list[str] = []

    def walk(e: Expr) -> None:
        if isinstance(e, Term):
            all_terms.append(e.value.lower().strip('"'))
        elif isinstance(e, BinaryExpr):
            walk(e.left)
            walk(e.right)
        elif isinstance(e, UnaryExpr):
            walk(e.operand)

    walk(expr)
    return [t for t, n in Counter(all_terms).items() if n > 1]


def find_subsumed_branches(expr: Expr) -> list[tuple[set[str], set[str]]]:
    """Return (subsuming_terms, subsumed_terms) OR-branch pairs.

    The subsumed branch adds no coverage: every document it matches is already matched
    by the subsuming branch.  Works across single terms and AND-of-terms branches alike.

    E.g. (flow AND COPD) OR ("high flow" AND COPD) → ({'flow','copd'}, {'high flow','copd'})
    """
    results: list[tuple[set[str], set[str]]] = []
    seen: set[tuple[frozenset[str], frozenset[str]]] = set()

    def walk(e: Expr) -> None:
        if isinstance(e, BinaryExpr):
            if e.op == Op.OR:
                branch_terms = [_collect_and_terms(b) for b in _collect_or_branches(e)]
                pure = [t for t in branch_terms if t]
                for i, t1 in enumerate(pure):
                    for j, t2 in enumerate(pure):
                        if i != j and _branch_subsumes(t1, t2):
                            key = (frozenset(t1), frozenset(t2))
                            if key not in seen:
                                seen.add(key)
                                results.append((t1, t2))
            walk(e.left)
            walk(e.right)
        elif isinstance(e, UnaryExpr):
            walk(e.operand)

    walk(expr)
    return results


def find_subsumed_terms(terms: set[str]) -> list[tuple[str, str]]:
    """Return (broader, narrower) pairs where broader subsumes narrower in OR context.

    E.g. 'high flow' subsumes 'high flow therapy': any match for the latter also
    satisfies the former, so the narrower term adds no coverage.
    """
    term_list = sorted(terms)
    pairs: list[tuple[str, str]] = []
    for i, a in enumerate(term_list):
        for b in term_list[i + 1 :]:
            if _is_subphrase(a, b):
                pairs.append((a, b))
            elif _is_subphrase(b, a):
                pairs.append((b, a))
    return pairs
