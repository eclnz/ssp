"""String-in/string-out conveniences over the expression-oriented core."""

from .analysis.diagnostics import analyze
from .analysis.diff import compare_expressions
from .analysis.matching import EXACT, TermMatcher
from .presentation.diagnostics import render_diagnostic
from .presentation.diff import render_diff
from .syntax.parser import parse
from .syntax.serialization import unparse
from .transformations.normalization import canonicalize
from .transformations.simplification import simplify


def canonical_form(query: str, *, allow_implicit_and: bool = False) -> str:
    return unparse(canonicalize(parse(query, allow_implicit_and=allow_implicit_and)))


def canonically_equal(a: str, b: str, *, allow_implicit_and: bool = False) -> bool:
    return canonicalize(parse(a, allow_implicit_and=allow_implicit_and)) == canonicalize(
        parse(b, allow_implicit_and=allow_implicit_and)
    )


def lint_string(
    query: str, *, matcher: TermMatcher = EXACT, matching_label: str | None = None, allow_implicit_and: bool = False
) -> list[str]:
    return [
        render_diagnostic(item)
        for item in analyze(
            parse(query, allow_implicit_and=allow_implicit_and), matcher=matcher, matching_label=matching_label
        )
    ]


def suggest_simplification(query: str, *, matcher: TermMatcher = EXACT, allow_implicit_and: bool = False) -> str | None:
    original = parse(query, allow_implicit_and=allow_implicit_and)
    rewritten = simplify(original, matcher=matcher)
    return unparse(rewritten) if rewritten != original else None


def format_string_diff(
    old: str, new: str, *, color: bool = True, allow_implicit_and: bool = False
) -> tuple[str, str] | None:
    diff = compare_expressions(
        parse(old, allow_implicit_and=allow_implicit_and), parse(new, allow_implicit_and=allow_implicit_and)
    )
    return render_diff(diff, color=color) if diff is not None else None


def format_simplification_diff(
    query: str, *, matcher: TermMatcher = EXACT, color: bool = True, allow_implicit_and: bool = False
) -> str | None:
    original = parse(query, allow_implicit_and=allow_implicit_and)
    diff = compare_expressions(original, simplify(original, matcher=matcher))
    return render_diff(diff, color=color)[0] if diff is not None else None
