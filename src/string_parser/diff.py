"""ANSI-colored structural query diffs."""

from __future__ import annotations

import difflib
from enum import StrEnum

from ._tree import _collect_and_exprs, _collect_and_terms, _collect_or_branches
from .ast import BinaryExpr, Expr, Op
from .normalization import canonicalize
from .parser import parse
from .rendering import unparse
from .simplification import simplify


class Colour(StrEnum):
    RED = "\033[31m"
    GREEN = "\033[32m"
    RESET = "\033[0m"


def _colour_branches(expr: Expr, highlight: set[frozenset[str]], colour: Colour) -> str:
    branches = _collect_or_branches(expr)
    result = ""
    for i, b in enumerate(branches):
        t = frozenset(_collect_and_terms(b))
        s = unparse(b)
        sep = " OR " if i > 0 else ""
        if t and t in highlight:
            result += f"{colour}{sep}{s}{Colour.RESET}"
        else:
            result += f"{sep}{s}"
    return result


def format_simplification_diff(string: str) -> str | None:
    """Original string with removed OR branches in red, or None if no change."""
    orig_expr = parse(string)
    simp_expr = simplify(orig_expr)
    if unparse(simp_expr) == unparse(orig_expr):
        return None
    simp_terms = {frozenset(_collect_and_terms(b)) for b in _collect_or_branches(simp_expr)}
    orig_terms = {frozenset(_collect_and_terms(b)) for b in _collect_or_branches(orig_expr)}
    removed = orig_terms - simp_terms
    return _colour_branches(orig_expr, removed, Colour.RED)


def _coloured_join(parts: list[str], sep: str) -> str:
    """Join parts with sep, pulling the separator into the colour span of each coloured part."""
    result = ""
    for i, part in enumerate(parts):
        if i == 0:
            result += part
        elif part.startswith("\033["):
            code = part[:5]  # \033[31m or \033[32m
            result += f"{code}{sep}{Colour.RESET}{part}"
        else:
            result += sep + part
    return result


def _tree_aware_diff(old: Expr, new: Expr) -> tuple[str, str]:
    """Recursively diff two expression trees, returning (coloured_was, coloured_now).

    Flattens same-op nodes into branch lists, aligns them with a sequence diff,
    then recurses into single-branch replacements — so shared subtrees stay plain
    and only the genuinely new/removed parts are coloured.
    """
    old_s, new_s = unparse(old), unparse(new)
    if old_s == new_s:
        return old_s, new_s

    # Infer op for branch-level diffing: works when both sides share an op, or when
    # one side collapses to a single term (e.g. (COPD OR AECOPD) → COPD).
    op: Op | None = None
    if isinstance(old, BinaryExpr) and isinstance(new, BinaryExpr) and old.op == new.op:
        op = old.op
    elif isinstance(old, BinaryExpr) and not isinstance(new, BinaryExpr):
        op = old.op
    elif isinstance(new, BinaryExpr) and not isinstance(old, BinaryExpr):
        op = new.op

    if op is not None:
        old_branches = _collect_or_branches(old) if op == Op.OR else _collect_and_exprs(old)
        new_branches = _collect_or_branches(new) if op == Op.OR else _collect_and_exprs(new)
        old_keys = [unparse(b) for b in old_branches]
        new_keys = [unparse(b) for b in new_branches]
        sep = f" {op.value} "
        was_parts: list[str] = []
        now_parts: list[str] = []

        for code, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old_keys, new_keys, autojunk=False).get_opcodes():
            if code == "equal":
                was_parts.extend(old_keys[i1:i2])
                now_parts.extend(new_keys[j1:j2])
            elif code == "delete":
                was_parts.extend(f"{Colour.RED}{k}{Colour.RESET}" for k in old_keys[i1:i2])
            elif code == "insert":
                now_parts.extend(f"{Colour.GREEN}{k}{Colour.RESET}" for k in new_keys[j1:j2])
            elif code == "replace":
                if i2 - i1 == 1 and j2 - j1 == 1:
                    w, n = _tree_aware_diff(old_branches[i1], new_branches[j1])
                    was_parts.append(w)
                    now_parts.append(n)
                else:
                    was_parts.extend(f"{Colour.RED}{k}{Colour.RESET}" for k in old_keys[i1:i2])
                    now_parts.extend(f"{Colour.GREEN}{k}{Colour.RESET}" for k in new_keys[j1:j2])

        was_joined = _coloured_join(was_parts, sep)
        now_joined = _coloured_join(now_parts, sep)
        return (
            f"({was_joined})" if len(old_branches) > 1 else was_joined,
            f"({now_joined})" if len(new_branches) > 1 else now_joined,
        )

    return f"{Colour.RED}{old_s}{Colour.RESET}", f"{Colour.GREEN}{new_s}{Colour.RESET}"


def format_string_diff(old: str, new: str) -> tuple[str, str] | None:
    """Return (coloured_was, coloured_now) with removals in red and additions in green.

    Uses tree-aware diffing so shared subtrees stay plain — only genuinely
    new or removed branches are highlighted.  Returns None if unchanged.
    """
    old_expr, new_expr = parse(old), parse(new)
    if unparse(canonicalize(old_expr)) == unparse(canonicalize(new_expr)):
        return None
    return _tree_aware_diff(old_expr, new_expr)
