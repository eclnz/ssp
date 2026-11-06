"""Public expression API for generic Boolean queries."""

from .analysis.diff import ExpressionDiff, compare_expressions
from .analysis.matching import EXACT, TermMatcher
from .analysis.redundancy import Diagnostic, DuplicateTerm, RedundantOperandDiagnostic, analyze
from .analysis.terms import TermChanges, compare_terms
from .syntax.expressions import BinaryExpr, Expr, Op, Term, UnaryExpr, unparse
from .syntax.parser import ImplicitAndWarning, parse
from .syntax.tokens import ParseError
from .transformations import canonicalize, simplify

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
