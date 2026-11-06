"""Conservative expression rewrites under an explicit term-matching policy."""

from ..analysis.implication import implies
from ..analysis.matching import MatchPolicy
from ..syntax.ast import BinaryExpr, Expr, Op, UnaryExpr
from ..syntax.tree import flatten, rebuild


def simplify(expr: Expr, *, policy: MatchPolicy = MatchPolicy.EXACT) -> Expr:
    """Remove duplicates and absorbed operands without mutating the input.

    The default treats terms as exact symbols. Phrase-based rewrites require an
    explicit LEXICAL_PHRASE policy. Negation is simplified only within its operand.
    """
    if isinstance(expr, UnaryExpr):
        return UnaryExpr(expr.op, simplify(expr.operand, policy=policy))
    if not isinstance(expr, BinaryExpr):
        return expr
    operands = [simplify(node, policy=policy) for node in flatten(expr, expr.op)]
    keep: list[Expr] = []
    for i, operand in enumerate(operands):
        redundant = False
        for j, other in enumerate(operands):
            if i == j:
                continue
            # OR retains the broader operand; AND retains the narrower one.
            forward = (
                implies(operand, other, policy=policy) if expr.op is Op.OR else implies(other, operand, policy=policy)
            )
            reverse = (
                implies(other, operand, policy=policy) if expr.op is Op.OR else implies(operand, other, policy=policy)
            )
            if forward and (not reverse or j < i):
                redundant = True
                break
        if not redundant:
            keep.append(operand)
    return rebuild(expr.op, keep)
