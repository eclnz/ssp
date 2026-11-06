"""Print expression trees for terminal inspection."""

from __future__ import annotations

from ..syntax.ast import BinaryExpr, Expr, Term, UnaryExpr
from ..syntax.traversal import collect_same_op


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
            children = collect_same_op(expr)
            for i, child in enumerate(children):
                _fmt_expr(child, next_indent, last=i == len(children) - 1, combine=combine)
        else:
            _fmt_expr(expr.left, next_indent, last=False, combine=combine)
            _fmt_expr(expr.right, next_indent, last=True, combine=combine)


def print_expr(expr: Expr, combine: bool = False) -> None:
    _fmt_expr(expr, combine=combine)
