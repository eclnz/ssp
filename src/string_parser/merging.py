"""Conservative three-way AST merging with explicit, contextual conflicts."""

from __future__ import annotations

from dataclasses import dataclass

from .analysis.revisions import Edit, Path, structural_edits
from .syntax.expressions import BinaryExpr, Expr, UnaryExpr, structural_key


@dataclass(frozen=True)
class MergeConflict:
    path: Path
    base: Expr
    left: Expr
    right: Expr
    reason: str


@dataclass(frozen=True)
class MergeResult:
    expression: Expr | None
    conflicts: tuple[MergeConflict, ...]
    changes: tuple[Edit, ...]


def merge_revisions(base: Expr, left: Expr, right: Expr) -> MergeResult:
    """Combine unambiguous edits to separate subtrees, without rewriting either side.

    Shape/operator changes at a concurrently edited node, distinct changes to one
    term, and reorderings with competing edits conflict. No partial expression is
    returned on conflict. Changes explain the accepted base-to-result edits.
    """
    conflicts: list[MergeConflict] = []

    def merge(base_node: Expr, left_node: Expr, right_node: Expr, path: Path) -> Expr:
        if left_node == right_node:
            return left_node
        if left_node == base_node:
            return right_node
        if right_node == base_node:
            return left_node
        if structural_key(left_node) == structural_key(base_node) or structural_key(right_node) == structural_key(
            base_node
        ):
            reason = "reordering overlaps concurrent edits"
        elif any(
            not edit.path for edit in structural_edits(base_node, left_node) + structural_edits(base_node, right_node)
        ):
            reason = "whole-subtree replacement overlaps concurrent edits"
        elif (
            isinstance(base_node, BinaryExpr)
            and isinstance(left_node, BinaryExpr)
            and isinstance(right_node, BinaryExpr)
            and base_node.op is left_node.op is right_node.op
        ):
            return BinaryExpr(
                base_node.op,
                merge(base_node.left, left_node.left, right_node.left, path + ("left",)),
                merge(base_node.right, left_node.right, right_node.right, path + ("right",)),
            )
        elif (
            isinstance(base_node, UnaryExpr) and isinstance(left_node, UnaryExpr) and isinstance(right_node, UnaryExpr)
        ):
            return UnaryExpr(
                base_node.op, merge(base_node.operand, left_node.operand, right_node.operand, path + ("operand",))
            )
        else:
            reason = "competing edits to the same term, operator, or subtree"
        conflicts.append(MergeConflict(path, base_node, left_node, right_node, reason))
        return base_node

    result = merge(base, left, right, ())
    if conflicts:
        return MergeResult(None, tuple(conflicts), ())
    return MergeResult(result, (), structural_edits(base, result))
