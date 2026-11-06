"""Shared redundancy evidence, typed findings, and analysis."""

from __future__ import annotations

from dataclasses import dataclass

from ..syntax.expressions import BinaryExpr, Expr, Op, flatten
from .matching import EXACT, TermMatcher, implies


@dataclass(frozen=True)
class RedundantOperand:
    """An operand removable from this flattened AND/OR group, with its witness."""

    operator: Op
    redundant_index: int
    retained_index: int
    redundant: Expr
    retained: Expr
    equivalent: bool


def find_redundant_operands(expr: BinaryExpr, *, matcher: TermMatcher = EXACT) -> list[RedundantOperand]:
    """Prove removals at one group; ties retain the first equivalent operand.

    Both diagnostics and transformations consume these exact decisions. Indices
    refer to flatten(expr, expr.op); evidence applies to this original group. Retained indices always survive.
    """
    operands = flatten(expr, expr.op)
    active = set(range(len(operands)))
    replacements: dict[int, tuple[int, bool]] = {}
    for i, operand in enumerate(operands):
        for j in sorted(active):
            if i == j:
                continue
            other = operands[j]
            premise, conclusion = (operand, other) if expr.op is Op.OR else (other, operand)
            if not implies(premise, conclusion, matcher=matcher):
                continue
            equivalent = implies(conclusion, premise, matcher=matcher)
            if not equivalent or j < i:
                active.remove(i)
                replacements[i] = (j, equivalent)
                break
    findings = []
    for i, (j, equivalent) in replacements.items():
        # Follow proven transitive coverage to a witness that really survives.
        # Each link points to an operand removed later, so chains cannot cycle.
        while j in replacements:
            j, next_equivalent = replacements[j]
            equivalent = equivalent and next_equivalent
        findings.append(RedundantOperand(expr.op, i, j, operands[i], operands[j], equivalent))
    return findings
