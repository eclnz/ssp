"""Term comparison and lexical redundancy analysis."""

from __future__ import annotations

from collections import Counter

from ._tree import _collect_and_terms, _collect_or_branches
from .ast import BinaryExpr, Expr, Op, Term, UnaryExpr
from .parser import parse


def collect_terms(expr: Expr) -> set[str]:
    """Return the set of all leaf terms in an expression, lowercased for comparison."""
    if isinstance(expr, Term):
        return {expr.value.lower().strip('"')}
    elif isinstance(expr, UnaryExpr):
        return collect_terms(expr.operand)
    else:
        return collect_terms(expr.left) | collect_terms(expr.right)


def classify_change(old: str, new: str) -> tuple[set[str], set[str]]:
    """Return (added_terms, removed_terms) between two search strings."""
    old_terms = collect_terms(parse(old))
    new_terms = collect_terms(parse(new))
    return new_terms - old_terms, old_terms - new_terms


def _phrase_words(term: str) -> list[str]:
    return term.lower().strip('"').split()


def _is_subphrase(broader: str, narrower: str) -> bool:
    """True if broader's words appear as a contiguous run inside narrower's words.

    In OR context broader already captures every hit narrower would — narrower is redundant.
    """
    bw = _phrase_words(broader)
    nw = _phrase_words(narrower)
    n = len(bw)
    if n >= len(nw):
        return False
    return any(nw[i : i + n] == bw for i in range(len(nw) - n + 1))


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


def combine(*exprs: Expr) -> Expr:
    """OR together multiple expressions — use when analysing a set of search strings jointly."""
    if not exprs:
        raise ValueError("At least one expression required")
    result = exprs[0]
    for e in exprs[1:]:
        result = BinaryExpr(Op.OR, result, e)
    return result


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


def _branch_subsumes(e1: set[str], e2: set[str]) -> bool:
    """True if every document matching e2 (AND of e2 terms) also matches e1 (AND of e1 terms).

    This holds when every term in e1 has a broader-or-equal counterpart in e2.
    """
    if e1 == e2:
        return False
    return all(any(t1 == t2 or _is_subphrase(t1, t2) for t2 in e2) for t1 in e1)


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
