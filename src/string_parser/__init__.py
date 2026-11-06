"""Expression-oriented public API; string conveniences live in string_parser.api."""

from .analysis.changes import TermChanges, compare_terms
from .analysis.diagnostics import Diagnostic, DiagnosticKind, analyze
from .analysis.diff import ExpressionDiff, compare_expressions
from .analysis.matching import MatchPolicy
from .syntax.ast import BinaryExpr, Expr, Op, Term, UnaryExpr
from .syntax.errors import ParseError
from .syntax.parser import ImplicitAndWarning, parse
from .syntax.serialization import unparse
from .transformations.normalization import canonicalize
from .transformations.simplification import simplify

__all__ = [
    "TermChanges",
    "compare_terms",
    "Diagnostic",
    "DiagnosticKind",
    "analyze",
    "ExpressionDiff",
    "compare_expressions",
    "MatchPolicy",
    "BinaryExpr",
    "Expr",
    "Op",
    "Term",
    "UnaryExpr",
    "ParseError",
    "ImplicitAndWarning",
    "parse",
    "unparse",
    "canonicalize",
    "simplify",
]
