"""Typed diagnostic variants; matching labels are data, never matcher objects."""

from dataclasses import dataclass

from ..syntax.ast import Expr, Op
from .matching import EXACT, TermMatcher
from .redundancy import duplicate_terms, inspect_redundancies


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
    result: list[Diagnostic] = [DuplicateTerm(term, count, matching_label) for term, count in duplicate_terms(expr, matcher=matcher)]
    result.extend(
        RedundantOperandDiagnostic(item.operator, item.redundant, item.retained, item.equivalent, matching_label)
        for item in inspect_redundancies(expr, matcher=matcher)
    )
    return result
