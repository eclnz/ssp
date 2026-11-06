"""Recursive-descent grammar with NOT > AND > OR precedence."""

from __future__ import annotations

import warnings

from .ast import BinaryExpr, Expr, Op, Term, UnaryExpr
from .tokenizer import _Paren, _Token, _tokenize


class ImplicitAndWarning(UserWarning):
    """Raised when adjacent terms are implicitly AND-ed (no operator between them)."""


def _parse(tokens: list[_Token]) -> Expr:
    pos = 0

    def peek() -> _Token | None:
        return tokens[pos] if pos < len(tokens) else None

    def consume() -> _Token:
        nonlocal pos
        t = tokens[pos]
        pos += 1
        return t

    def parse_or() -> Expr:
        left = parse_and()
        while peek() is Op.OR:
            consume()
            left = BinaryExpr(Op.OR, left, parse_and())
        return left

    def parse_and() -> Expr:
        left = parse_not()
        while True:
            if peek() is Op.AND:
                consume()
            elif isinstance(peek(), Term) or peek() in (_Paren.OPEN, Op.NOT):
                warnings.warn(
                    "Adjacent terms without operator — treating as AND (PubMed behaviour)",
                    ImplicitAndWarning,
                    stacklevel=3,
                )
            else:
                break
            left = BinaryExpr(Op.AND, left, parse_not())
        return left

    def parse_not() -> Expr:
        if peek() is Op.NOT:
            consume()
            return UnaryExpr(Op.NOT, parse_not())
        return parse_atom()

    def parse_atom() -> Expr:
        t = peek()
        if t is _Paren.OPEN:
            consume()
            expr = parse_or()
            if peek() is _Paren.CLOSE:
                consume()
            return expr
        t = consume()
        if isinstance(t, Term):
            return t
        raise ValueError(f"Unexpected token in expression: {t!r}")

    return parse_or()


def parse(string: str) -> Expr:
    return _parse(_tokenize(string))
