"""String-in/string-out conveniences over the expression-oriented core."""

from .analysis.diagnostics import analyze
from .analysis.diff import compare_expressions
from .analysis.matching import MatchPolicy
from .presentation.diagnostics import render_diagnostic
from .presentation.diff import render_diff
from .syntax.parser import parse
from .syntax.serialization import unparse
from .transformations.normalization import canonicalize
from .transformations.simplification import simplify


def canonical_form(query: str) -> str:
    return unparse(canonicalize(parse(query)))


def canonically_equal(a: str, b: str) -> bool:
    return canonicalize(parse(a)) == canonicalize(parse(b))


def lint_string(query: str, *, policy: MatchPolicy = MatchPolicy.EXACT) -> list[str]:
    return [render_diagnostic(item) for item in analyze(parse(query), policy=policy)]


def suggest_simplification(query: str, *, policy: MatchPolicy = MatchPolicy.EXACT) -> str | None:
    original = parse(query)
    rewritten = simplify(original, policy=policy)
    return unparse(rewritten) if rewritten != original else None


def format_string_diff(old: str, new: str, *, color: bool = True) -> tuple[str, str] | None:
    diff = compare_expressions(parse(old), parse(new))
    return render_diff(diff, color=color) if diff is not None else None


def format_simplification_diff(
    query: str, *, policy: MatchPolicy = MatchPolicy.EXACT, color: bool = True
) -> str | None:
    original = parse(query)
    diff = compare_expressions(original, simplify(original, policy=policy))
    return render_diff(diff, color=color)[0] if diff is not None else None
