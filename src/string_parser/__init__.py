"""Search-string revision comparison and merge primitives."""

from .analysis.diff import ExpressionDiff, compare_expressions
from .analysis.matching import EXACT, TermMatcher
from .analysis.revisions import Edit, EditKind, Effect, RevisionComparison, compare_revisions
from .analysis.satisfiability import SolverLimits
from .analysis.terms import TermChanges, compare_terms
from .merging import MergeConflict, MergeResult, merge_revisions
from .syntax.expressions import BinaryExpr, CanonicalKey, Expr, Op, Term, UnaryExpr, canonical_key, unparse
from .syntax.parser import ImplicitAndWarning, ParseError, parse
from .transformations import canonicalize, simplify

__all__ = [
    "EXACT",
    "TermMatcher",
    "BinaryExpr",
    "Expr",
    "CanonicalKey",
    "canonical_key",
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
    "SolverLimits",
    "compare_revisions",
    "MergeConflict",
    "MergeResult",
    "merge_revisions",
]
