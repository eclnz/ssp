"""Apply the same proven operand removals exposed by redundancy analysis."""

from ..analysis.matching import EXACT, TermMatcher
from ..analysis.redundancy import find_redundant_operands
from ..syntax.ast import BinaryExpr, Expr, UnaryExpr
from ..syntax.tree import flatten, rebuild


def simplify(expr: Expr, *, matcher: TermMatcher = EXACT) -> Expr:
    """Return a new tree; matching defaults to exact raw-term identity."""
    if isinstance(expr, UnaryExpr):
        return UnaryExpr(expr.op, simplify(expr.operand, matcher=matcher))
    if not isinstance(expr, BinaryExpr):
        return expr
    group = rebuild(expr.op, (simplify(node, matcher=matcher) for node in flatten(expr, expr.op)))
    if not isinstance(group, BinaryExpr):
        return group
    removed = {item.redundant_index for item in find_redundant_operands(group, matcher=matcher)}
    return rebuild(group.op, (node for i, node in enumerate(flatten(group, group.op)) if i not in removed))
