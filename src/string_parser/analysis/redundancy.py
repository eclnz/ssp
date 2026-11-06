"""Shared redundancy evidence, typed findings, and analysis."""

from __future__ import annotations

from dataclasses import dataclass

from ..syntax.expressions import BinaryExpr, Expr, Op, Term, UnaryExpr, flatten, walk
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


def inspect_redundancies(expr: Expr, *, matcher: TermMatcher = EXACT) -> list[RedundantOperand]:
    """Inspect every distinct group without revisiting nested same-op chains."""
    if isinstance(expr, BinaryExpr):
        findings = find_redundant_operands(expr, matcher=matcher)
        for operand in flatten(expr, expr.op):
            findings.extend(inspect_redundancies(operand, matcher=matcher))
        return findings
    if isinstance(expr, UnaryExpr):
        return inspect_redundancies(expr.operand, matcher=matcher)
    return []


def duplicate_terms(expr: Expr, *, matcher: TermMatcher = EXACT) -> list[tuple[str, int]]:
    """Raw representative term and count under mutual term coverage."""
    groups: list[tuple[str, int]] = []
    for node in walk(expr):
        if not isinstance(node, Term):
            continue
        for i, (term, count) in enumerate(groups):
            if matcher.covers_term(term, node.value) and matcher.covers_term(node.value, term):
                groups[i] = (term, count + 1)
                break
        else:
            groups.append((node.value, 1))
    return [(term, count) for term, count in groups if count > 1]


@dataclass(frozen=True)
class DuplicateTerm:
    term: str
    count: int
    matching_label: str | None = None

    def __post_init__(self) -> None:
        if self.count < 2:
            raise ValueError("Duplicate terms require at least two occurrences")


@dataclass(frozen=True)
class RedundantOperandDiagnostic:
    operator: Op
    redundant: Expr
    retained: Expr
    equivalent: bool
    matching_label: str | None = None

    def __post_init__(self) -> None:
        if self.operator not in (Op.AND, Op.OR):
            raise ValueError("Operand redundancy requires AND or OR")


Diagnostic = DuplicateTerm | RedundantOperandDiagnostic


def analyze(expr: Expr, *, matcher: TermMatcher = EXACT, matching_label: str | None = None) -> list[Diagnostic]:
    """Explain shared redundancy proofs and report repeated term occurrences.

    A label is optional display metadata; matchers only implement covers_term.
    Evidence describes the supplied tree, not all findings a later rewrite may expose.
    """
    result: list[Diagnostic] = [
        DuplicateTerm(term, count, matching_label) for term, count in duplicate_terms(expr, matcher=matcher)
    ]
    result.extend(
        RedundantOperandDiagnostic(item.operator, item.redundant, item.retained, item.equivalent, matching_label)
        for item in inspect_redundancies(expr, matcher=matcher)
    )
    return result
