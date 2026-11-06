"""Term coverage contracts and conservative expression implication."""

from __future__ import annotations

from typing import Protocol

from ..syntax.expressions import BinaryExpr, Expr, Op, Term, flatten, structural_key


class TermMatcher(Protocol):
    """Sound, reflexive, transitive coverage; false may conservatively mean unknown."""

    def covers_term(self, broader: str, narrower: str) -> bool: ...


class ExactMatcher:
    def covers_term(self, broader: str, narrower: str) -> bool:
        return broader == narrower


EXACT = ExactMatcher()


def implies(premise: Expr, conclusion: Expr, *, matcher: TermMatcher = EXACT) -> bool:
    """Prove premise implies conclusion under the selected term policy.

    False means unproved, not a proof that implication is impossible. Negations
    are opaque except for structural equality, including reordered operands.
    """
    if structural_key(premise) == structural_key(conclusion):
        return True
    if isinstance(conclusion, Term) and isinstance(premise, Term):
        return matcher.covers_term(conclusion.value, premise.value)
    if isinstance(conclusion, BinaryExpr) and conclusion.op is Op.AND:
        return all(implies(premise, node, matcher=matcher) for node in flatten(conclusion, Op.AND))
    if isinstance(premise, BinaryExpr) and premise.op is Op.OR:
        return all(implies(node, conclusion, matcher=matcher) for node in flatten(premise, Op.OR))
    if isinstance(conclusion, BinaryExpr) and conclusion.op is Op.OR:
        return any(implies(premise, node, matcher=matcher) for node in flatten(conclusion, Op.OR))
    if isinstance(premise, BinaryExpr) and premise.op is Op.AND:
        return any(implies(node, conclusion, matcher=matcher) for node in flatten(premise, Op.AND))
    return False
