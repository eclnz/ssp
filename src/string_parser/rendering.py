"""Render queries and print expression trees."""

from __future__ import annotations

from ._tree import _collect_same_op
from .ast import BinaryExpr, Expr, Term, UnaryExpr


def unparse(expr: Expr) -> str:
    """Reconstruct a PubMed search string from an expression tree."""
    if isinstance(expr, Term):
        return expr.value  # preserves original quoting
    if isinstance(expr, UnaryExpr):
        return f"NOT {unparse(expr.operand)}"
    return f"({unparse(expr.left)} {expr.op.value} {unparse(expr.right)})"


def _fmt_expr(expr: Expr, indent: str = "", last: bool = True, combine: bool = False) -> None:
    connector = "└── " if last else "├── "
    next_indent = indent + ("    " if last else "│   ")

    if isinstance(expr, Term):
        print(f"{indent}{connector}Term({expr.value!r})")
    elif isinstance(expr, UnaryExpr):
        print(f"{indent}{connector}{expr.op.value}")
        _fmt_expr(expr.operand, next_indent, last=True, combine=combine)
    elif isinstance(expr, BinaryExpr):
        print(f"{indent}{connector}{expr.op.value}")
        if combine:
            children = _collect_same_op(expr)
            for i, child in enumerate(children):
                _fmt_expr(child, next_indent, last=i == len(children) - 1, combine=combine)
        else:
            _fmt_expr(expr.left, next_indent, last=False, combine=combine)
            _fmt_expr(expr.right, next_indent, last=True, combine=combine)


def print_expr(expr: Expr, combine: bool = False) -> None:
    _fmt_expr(expr, combine=combine)
