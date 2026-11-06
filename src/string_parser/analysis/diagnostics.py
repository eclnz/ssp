"""Structured redundancy findings without terminal or message formatting."""

from dataclasses import dataclass
from enum import Enum

from ..syntax.ast import Expr
from .matching import MatchPolicy
from .redundancy import find_and_redundancies, find_duplicate_terms, find_subsumed_branches


class DiagnosticKind(Enum):
    DUPLICATE = "duplicate"
    AND_REDUNDANCY = "and_redundancy"
    OR_REDUNDANCY = "or_redundancy"


@dataclass(frozen=True)
class Diagnostic:
    kind: DiagnosticKind
    broader: tuple[str, ...]
    narrower: tuple[str, ...] = ()
    policy: MatchPolicy = MatchPolicy.EXACT


def analyze(expr: Expr, *, policy: MatchPolicy = MatchPolicy.EXACT) -> list[Diagnostic]:
    result = [
        Diagnostic(DiagnosticKind.DUPLICATE, (term,), policy=policy)
        for term in find_duplicate_terms(expr, policy=policy)
    ]
    result += [
        Diagnostic(DiagnosticKind.AND_REDUNDANCY, (a,), (b,), policy=policy)
        for a, b in find_and_redundancies(expr, policy=policy)
    ]
    result += [
        Diagnostic(DiagnosticKind.OR_REDUNDANCY, tuple(sorted(a)), tuple(sorted(b)), policy=policy)
        for a, b in find_subsumed_branches(expr, policy=policy)
    ]
    return result
