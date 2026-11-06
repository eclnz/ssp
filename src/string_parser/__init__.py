"""Search-string revision comparison and merge primitives."""

from .analysis.diff import ExpressionDiff, compare_expressions
from .analysis.matching import EXACT, TermMatcher
from .analysis.revisions import Edit, EditKind, Effect, RevisionComparison, compare_revisions
from .analysis.terms import TermChanges, compare_terms
from .merging import MergeConflict, MergeResult, merge_revisions
from .syntax.expressions import BinaryExpr, Expr, Op, Term, UnaryExpr, unparse
from .syntax.parser import ImplicitAndWarning, parse
from .syntax.tokens import ParseError
from .transformations import canonicalize, simplify

__all__ = [
    "EXACT",
    "TermMatcher",
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
    "ExpressionDiff",
    "compare_expressions",
    "TermChanges",
    "compare_terms",
    "Edit",
    "EditKind",
    "Effect",
    "RevisionComparison",
    "compare_revisions",
    "MergeConflict",
    "MergeResult",
    "merge_revisions",
]
