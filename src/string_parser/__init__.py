"""Public expression API for generic Boolean queries."""

from .analysis.changes import TermChanges, compare_terms
from .analysis.diagnostics import Diagnostic, DuplicateTerm, RedundantOperandDiagnostic, analyze
from .analysis.diff import ExpressionDiff, compare_expressions
from .analysis.matching import EXACT, TermMatcher
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
    "DuplicateTerm",
    "RedundantOperandDiagnostic",
    "TermMatcher",
    "analyze",
    "ExpressionDiff",
    "compare_expressions",
    "EXACT",
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
