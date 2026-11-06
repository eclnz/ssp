"""Identify duplicate terms and redundant Boolean branches."""

from __future__ import annotations

from collections import Counter

from ..syntax.ast import BinaryExpr, Expr, Op, Term, UnaryExpr
from ..syntax.tree import flatten
from .matching import MatchPolicy
from .terms import conjunction_terms


def project_conjunction(expr: Expr, *, policy: MatchPolicy) -> frozenset[str] | None:
    terms = conjunction_terms(expr)
    return frozenset(policy.key(term) for term in terms) if terms is not None else None


def branch_subsumes(a: frozenset[str], b: frozenset[str], *, policy: MatchPolicy) -> bool:
    return a != b and all((any((policy.covers_term(x, y) for y in b)) for x in a))


def is_strict_subphrase(a: str, b: str, *, policy: MatchPolicy) -> bool:
    return a != b and policy.covers_term(a, b)


def find_and_redundancies(expr: Expr, *, policy: MatchPolicy = MatchPolicy.EXACT) -> list[tuple[str, str]]:
    """Return (redundant_broader, necessary_narrower) pairs under the chosen policy.

    In 'flow AND "high flow"', 'flow' is always satisfied when 'high flow' is — it adds no constraint.
    """
    results: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def walk(e: Expr) -> None:
        if isinstance(e, BinaryExpr):
            if e.op == Op.AND:
                for lt in project_conjunction(e.left, policy=policy) or ():
                    for rt in project_conjunction(e.right, policy=policy) or ():
                        pair = (
                            (lt, rt)
                            if is_strict_subphrase(lt, rt, policy=policy)
                            else (rt, lt)
                            if is_strict_subphrase(rt, lt, policy=policy)
                            else None
                        )
                        if pair and pair not in seen:
                            seen.add(pair)
                            results.append(pair)
            walk(e.left)
            walk(e.right)
        elif isinstance(e, UnaryExpr):
            walk(e.operand)

    walk(expr)
    return results


def find_absorbed_branches(expr: Expr, *, policy: MatchPolicy = MatchPolicy.EXACT) -> list[tuple[str, set[str]]]:
    """Return (absorbing_term, absorbed_and_terms) where 'T OR (A AND B)' simplifies to T.

    T absorbs an AND branch when T is a subphrase of (or equal to) at least one term in that branch —
    meaning every document matching the AND also matches T.
    """
    results: list[tuple[str, set[str]]] = []
    seen: set[tuple[str, frozenset[str]]] = set()

    def walk(e: Expr) -> None:
        if isinstance(e, BinaryExpr):
            if e.op == Op.OR:
                branches = flatten(e, Op.OR)
                or_terms = [policy.key(b.value) for b in branches if isinstance(b, Term)]
                and_branches = [
                    project_conjunction(b, policy=policy)
                    for b in branches
                    if isinstance(b, BinaryExpr) and b.op == Op.AND
                ]
                for t in or_terms:
                    for and_terms in and_branches:
                        if and_terms and any(
                            (t == at or is_strict_subphrase(t, at, policy=policy) for at in and_terms)
                        ):
                            key = (t, frozenset(and_terms))
                            if key not in seen:
                                seen.add(key)
                                results.append((t, set(and_terms)))
            walk(e.left)
            walk(e.right)
        elif isinstance(e, UnaryExpr):
            walk(e.operand)

    walk(expr)
    return results


def find_duplicate_terms(expr: Expr, *, policy: MatchPolicy = MatchPolicy.EXACT) -> list[str]:
    """Return terms that appear more than once anywhere in the expression tree.

    collect_terms deduplicates, so (A OR B) OR (A OR C) hides the duplicate A.
    """
    all_terms: list[str] = []

    def walk(e: Expr) -> None:
        if isinstance(e, Term):
            all_terms.append(policy.key(e.value))
        elif isinstance(e, BinaryExpr):
            walk(e.left)
            walk(e.right)
        elif isinstance(e, UnaryExpr):
            walk(e.operand)

    walk(expr)
    return [t for t, n in Counter(all_terms).items() if n > 1]


def find_subsumed_branches(expr: Expr, *, policy: MatchPolicy = MatchPolicy.EXACT) -> list[tuple[set[str], set[str]]]:
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
                branch_terms = [project_conjunction(b, policy=policy) for b in flatten(e, Op.OR)]
                pure = [t for t in branch_terms if t]
                for i, t1 in enumerate(pure):
                    for j, t2 in enumerate(pure):
                        if i != j and branch_subsumes(t1, t2, policy=policy):
                            key = (frozenset(t1), frozenset(t2))
                            if key not in seen:
                                seen.add(key)
                                results.append((set(t1), set(t2)))
            walk(e.left)
            walk(e.right)
        elif isinstance(e, UnaryExpr):
            walk(e.operand)

    walk(expr)
    return results


def find_subsumed_terms(terms: set[str], *, policy: MatchPolicy = MatchPolicy.EXACT) -> list[tuple[str, str]]:
    """Return (broader, narrower) pairs where broader subsumes narrower in OR context.

    E.g. 'high flow' subsumes 'high flow therapy': any match for the latter also
    satisfies the former, so the narrower term adds no coverage.
    """
    term_list = sorted(terms)
    pairs: list[tuple[str, str]] = []
    for i, a in enumerate(term_list):
        for b in term_list[i + 1 :]:
            if is_strict_subphrase(a, b, policy=policy):
                pairs.append((a, b))
            elif is_strict_subphrase(b, a, policy=policy):
                pairs.append((b, a))
    return pairs
