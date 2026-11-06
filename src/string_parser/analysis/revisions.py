"""Revision edits and bounded, exact Boolean effect comparison."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import product

from ..syntax.expressions import BinaryExpr, Expr, Op, Term, UnaryExpr, structural_key
from .terms import TermChanges, collect_terms, compare_terms

Path = tuple[str, ...]
Assignment = tuple[tuple[str, bool], ...]


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
    if structural_key(before) == structural_key(after):
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


def _evaluate(expr: Expr, assignment: dict[str, bool]) -> bool:
    if isinstance(expr, Term):
        return assignment[expr.value]
    if isinstance(expr, UnaryExpr):
        return not _evaluate(expr.operand, assignment)
    if expr.op is Op.AND:
        return _evaluate(expr.left, assignment) and _evaluate(expr.right, assignment)
    return _evaluate(expr.left, assignment) or _evaluate(expr.right, assignment)


def compare_revisions(
    before: Expr, after: Expr, *, assumptions: Expr | None = None, max_assignments: int = 4096
) -> RevisionComparison:
    """Compare Boolean match sets over independent raw term symbols.

    Optional assumptions restrict admissible assignments. Classification is exact
    within the enumeration budget; an exceeded budget or inconsistent assumptions
    yields UNKNOWN. Witnesses are hypothetical term matches, not retrieved records.
    """
    if max_assignments < 1:
        raise ValueError("max_assignments must be positive")
    edits, terms = structural_edits(before, after), compare_terms(before, after)
    if assumptions is None and structural_key(before) == structural_key(after):
        return RevisionComparison(before, after, edits, terms, Effect.EQUIVALENT, assumptions=assumptions)
    symbols = collect_terms(before) | collect_terms(after)
    if assumptions is not None:
        symbols |= collect_terms(assumptions)
    names = sorted(symbols)
    if 2 ** len(names) > max_assignments:
        return RevisionComparison(
            before, after, edits, terms, Effect.UNKNOWN, assumptions=assumptions, reason="assignment budget exceeded"
        )
    added = removed = None
    admissible = False
    for bits in product((False, True), repeat=len(names)):
        values = dict(zip(names, bits))
        if assumptions is not None and not _evaluate(assumptions, values):
            continue
        admissible = True
        old, new = _evaluate(before, values), _evaluate(after, values)
        if new and not old and added is None:
            added = tuple(values.items())
        if old and not new and removed is None:
            removed = tuple(values.items())
        if added is not None and removed is not None:
            break
    if not admissible:
        return RevisionComparison(
            before,
            after,
            edits,
            terms,
            Effect.UNKNOWN,
            assumptions=assumptions,
            reason="assumptions admit no assignments",
        )
    if added is None and removed is None:
        effect = Effect.EQUIVALENT
    elif removed is None:
        effect = Effect.BROADER
    elif added is None:
        effect = Effect.NARROWER
    else:
        effect = Effect.MIXED
    return RevisionComparison(before, after, edits, terms, effect, added, removed, assumptions)
