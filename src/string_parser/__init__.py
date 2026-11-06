"""Stable public API for Boolean search string parsing and analysis."""

from .analysis.changes import (
    classify_change,
)
from .analysis.lint import (
    lint_string,
)
from .analysis.redundancy import (
    find_absorbed_branches,
    find_and_redundancies,
    find_duplicate_terms,
    find_subsumed_branches,
    find_subsumed_terms,
)
from .analysis.terms import (
    collect_terms,
)
from .presentation.console import (
    print_expr,
)
from .presentation.diff import (
    Colour,
    format_simplification_diff,
    format_string_diff,
)
from .syntax.ast import (
    BinaryExpr,
    Expr,
    Op,
    Term,
    UnaryExpr,
)
from .syntax.composition import (
    combine,
)
from .syntax.parser import (
    ImplicitAndWarning,
    parse,
)
from .syntax.serialization import (
    unparse,
)
from .transformations.normalization import (
    canonical_form,
    canonicalize,
    canonically_equal,
)
from .transformations.simplification import (
    simplify,
    suggest_simplification,
)

__all__ = [
    "BinaryExpr",
    "Colour",
    "Expr",
    "ImplicitAndWarning",
    "Op",
    "Term",
    "UnaryExpr",
    "canonical_form",
    "canonicalize",
    "canonically_equal",
    "classify_change",
    "collect_terms",
    "combine",
    "find_absorbed_branches",
    "find_and_redundancies",
    "find_duplicate_terms",
    "find_subsumed_branches",
    "find_subsumed_terms",
    "format_simplification_diff",
    "format_string_diff",
    "lint_string",
    "parse",
    "print_expr",
    "simplify",
    "suggest_simplification",
    "unparse",
]
