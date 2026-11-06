"""Revision edits and SAT-backed Boolean effect comparison."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..syntax.expressions import BinaryExpr, Expr, Op, Term, UnaryExpr, canonical_key
from .satisfiability import Assignment, SatSolver, SolverLimits
from .terms import TermChanges, compare_terms

Path = tuple[str, ...]


class EditKind(Enum):
    REARRANGE = "rearrange_operands"
    TERM = "replace_term"
    OPERATOR = "change_operator"
    ADD_NEGATION = "add_negation"
    REMOVE_NEGATION = "remove_negation"
    ADD_BRANCH = "add_branch"
    REMOVE_BRANCH = "remove_branch"
    SUBTREE = "replace_subtree"


@dataclass(frozen=True)
class Edit:
    path: Path
    kind: EditKind
    before: Expr | Op
    after: Expr | Op


class Effect(Enum):
    EQUIVALENT = "equivalent"
    BROADER = "broader"
    NARROWER = "narrower"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RevisionComparison:
    before: Expr
    after: Expr
    edits: tuple[Edit, ...]
    terms: TermChanges
    effect: Effect
    added_witness: Assignment | None = None
    removed_witness: Assignment | None = None
    assumptions: Expr | None = None
    reason: str | None = None


def structural_edits(before: Expr, after: Expr, path: Path = ()) -> tuple[Edit, ...]:
    """Describe occurrence-level AST edits; paths address the supplied before tree.

    A branch/negation edit replaces the whole node at its path. Operator edits
    address its op field. No term matching or normalization is implicit.
    """
    if before == after:
        return ()
    if canonical_key(before) == canonical_key(after):
        return (Edit(path, EditKind.REARRANGE, before, after),)
    if isinstance(after, UnaryExpr) and after.operand == before:
        return (Edit(path, EditKind.ADD_NEGATION, before, after),)
    if isinstance(before, UnaryExpr) and before.operand == after:
        return (Edit(path, EditKind.REMOVE_NEGATION, before, after),)
    if isinstance(after, BinaryExpr) and before in (after.left, after.right):
        return (Edit(path, EditKind.ADD_BRANCH, before, after),)
    if isinstance(before, BinaryExpr) and after in (before.left, before.right):
        return (Edit(path, EditKind.REMOVE_BRANCH, before, after),)
    if isinstance(before, Term) and isinstance(after, Term):
        return (Edit(path, EditKind.TERM, before, after),)
    if isinstance(before, UnaryExpr) and isinstance(after, UnaryExpr):
        return structural_edits(before.operand, after.operand, path + ("operand",))
    if isinstance(before, BinaryExpr) and isinstance(after, BinaryExpr):
        operator = () if before.op is after.op else (Edit(path + ("op",), EditKind.OPERATOR, before.op, after.op),)
        return (
            operator
            + structural_edits(before.left, after.left, path + ("left",))
            + structural_edits(before.right, after.right, path + ("right",))
        )
    return (Edit(path, EditKind.SUBTREE, before, after),)


def compare_revisions(
    before: Expr, after: Expr, *, assumptions: Expr | None = None, limits: SolverLimits = SolverLimits()
) -> RevisionComparison:
    """Compare possible gains/losses over independent raw term symbols using SAT.

    Optional assumptions restrict admissible matches. Unfinished checks or
    inconsistent assumptions yield UNKNOWN, never inferred equivalence. Solver
    witnesses contain raw symbols only, and describe hypothetical term matches.
    """
    edits, terms = structural_edits(before, after), compare_terms(before, after)
    if assumptions is None and canonical_key(before) == canonical_key(after):
        return RevisionComparison(before, after, edits, terms, Effect.EQUIVALENT)
    expressions = [before, after] + ([assumptions] if assumptions is not None else [])
    with SatSolver(expressions, limits) as solver:
        old, new = solver.roots[:2]
        scope = list(solver.roots[2:])
        gains = solver.check(scope + [new, -old])
        losses = solver.check(scope + [old, -new])
        if gains.satisfiable is None or losses.satisfiable is None:
            return RevisionComparison(
                before,
                after,
                edits,
                terms,
                Effect.UNKNOWN,
                gains.witness,
                losses.witness,
                assumptions,
                "SAT solver work limit reached",
            )
        # A gain/loss witness already proves the assumption context is nonempty.
        if assumptions is not None and gains.satisfiable is False and losses.satisfiable is False:
            context = solver.check(scope)
            if context.satisfiable is not True:
                reason = (
                    "assumptions admit no assignments"
                    if context.satisfiable is False
                    else "SAT solver work limit reached checking assumptions"
                )
                return RevisionComparison(
                    before, after, edits, terms, Effect.UNKNOWN, assumptions=assumptions, reason=reason
                )
    if gains.satisfiable and losses.satisfiable:
        effect = Effect.MIXED
    elif gains.satisfiable:
        effect = Effect.BROADER
    elif losses.satisfiable:
        effect = Effect.NARROWER
    else:
        effect = Effect.EQUIVALENT
    return RevisionComparison(before, after, edits, terms, effect, gains.witness, losses.witness, assumptions)
