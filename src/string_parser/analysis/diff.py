"""Structural query comparison without styling."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum

from ..syntax.expressions import BinaryExpr, Expr, Op, flatten, structural_key, unparse


class ChangeKind(Enum):
    SAME = "same"
    REMOVED = "removed"
    ADDED = "added"


@dataclass(frozen=True)
class Fragment:
    text: str
    kind: ChangeKind = ChangeKind.SAME


@dataclass(frozen=True)
class ExpressionDiff:
    before: tuple[Fragment, ...]
    after: tuple[Fragment, ...]


def _join(parts: list[tuple[Fragment, ...]], op: Op) -> tuple[Fragment, ...]:
    result: list[Fragment] = []
    if len(parts) > 1:
        result.append(Fragment("("))
    for i, part in enumerate(parts):
        if i:
            result.append(Fragment(f" {op.value} ", part[0].kind if part else ChangeKind.SAME))
        result.extend(part)
    if len(parts) > 1:
        result.append(Fragment(")"))
    return tuple(result)


def _align(old: Expr, new: Expr) -> ExpressionDiff:
    if old == new:
        same = (Fragment(unparse(old)),)
        return ExpressionDiff(same, same)
    op = None
    if isinstance(old, BinaryExpr) and isinstance(new, BinaryExpr) and old.op is new.op:
        op = old.op
    elif isinstance(old, BinaryExpr) and not isinstance(new, BinaryExpr):
        op = old.op
    elif isinstance(new, BinaryExpr) and not isinstance(old, BinaryExpr):
        op = new.op
    if op is None:
        return ExpressionDiff(
            (Fragment(unparse(old), ChangeKind.REMOVED),), (Fragment(unparse(new), ChangeKind.ADDED),)
        )
    before, after = flatten(old, op), flatten(new, op)
    a: list[tuple[Fragment, ...]] = []
    b: list[tuple[Fragment, ...]] = []
    for code, i, end_i, j, end_j in SequenceMatcher(
        None, [unparse(x) for x in before], [unparse(x) for x in after], autojunk=False
    ).get_opcodes():
        if code == "replace" and end_i - i == end_j - j == 1:
            child = _align(before[i], after[j])
            a.append(child.before)
            b.append(child.after)
        else:
            a.extend(
                (Fragment(unparse(x), ChangeKind.SAME if code == "equal" else ChangeKind.REMOVED),)
                for x in before[i:end_i]
            )
            b.extend(
                (Fragment(unparse(x), ChangeKind.SAME if code == "equal" else ChangeKind.ADDED),)
                for x in after[j:end_j]
            )
    return ExpressionDiff(_join(a, op), _join(b, op))


def compare_expressions(old: Expr, new: Expr) -> ExpressionDiff | None:
    """Compare structure, ignoring AND/OR operand order; preserve original text in output."""
    if structural_key(old) == structural_key(new):
        return None
    return _align(old, new)
