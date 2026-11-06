"""Sufficient implication rules; an unknown relationship returns False."""

from ..syntax.ast import BinaryExpr, Expr, Op, Term
from ..syntax.tree import flatten, structural_key
from .matching import MatchPolicy


def implies(premise: Expr, conclusion: Expr, *, policy: MatchPolicy = MatchPolicy.EXACT) -> bool:
    """Prove premise implies conclusion under the selected term policy.

    False means unproved, not a proof that implication is impossible. Negations
    are opaque except for structural equality, including reordered operands.
    """
    if structural_key(premise) == structural_key(conclusion):
        return True
    if isinstance(conclusion, Term) and isinstance(premise, Term):
        return policy.covers_term(conclusion.value, premise.value)
    if isinstance(conclusion, BinaryExpr) and conclusion.op is Op.AND:
        return all(implies(premise, node, policy=policy) for node in flatten(conclusion, Op.AND))
    if isinstance(premise, BinaryExpr) and premise.op is Op.OR:
        return all(implies(node, conclusion, policy=policy) for node in flatten(premise, Op.OR))
    if isinstance(conclusion, BinaryExpr) and conclusion.op is Op.OR:
        return any(implies(premise, node, policy=policy) for node in flatten(conclusion, Op.OR))
    if isinstance(premise, BinaryExpr) and premise.op is Op.AND:
        return any(implies(node, conclusion, policy=policy) for node in flatten(premise, Op.AND))
    return False
