"""Recursive-descent grammar: NOT > AND > OR, with explicit errors."""

from __future__ import annotations

import warnings

from .ast import BinaryExpr, Expr, Op, Term, UnaryExpr
from .errors import ParseError
from .tokenizer import TokenKind, tokenize


class ImplicitAndWarning(UserWarning):
    """Adjacent operands have been joined with an implicit AND."""


def parse(text: str) -> Expr:
    """Parse a complete query or raise ParseError; retain implicit AND support."""
    tokens = tokenize(text)
    pos = 0

    def kind() -> TokenKind | None:
        return tokens[pos].kind if pos < len(tokens) else None

    def error(message: str) -> ParseError:
        return ParseError(message, tokens[pos].start if pos < len(tokens) else len(text))

    def parse_or() -> Expr:
        nonlocal pos
        left = parse_and()
        while kind() is TokenKind.OR:
            pos += 1
            left = BinaryExpr(Op.OR, left, parse_and())
        return left

    def parse_and() -> Expr:
        nonlocal pos
        left = parse_not()
        while True:
            if kind() is TokenKind.AND:
                pos += 1
            elif kind() in (TokenKind.TERM, TokenKind.OPEN, TokenKind.NOT):
                warnings.warn("Adjacent operands treated as AND", ImplicitAndWarning, stacklevel=3)
            else:
                break
            left = BinaryExpr(Op.AND, left, parse_not())
        return left

    def parse_not() -> Expr:
        nonlocal pos
        if kind() is TokenKind.NOT:
            pos += 1
            return UnaryExpr(Op.NOT, parse_not())
        return parse_atom()

    def parse_atom() -> Expr:
        nonlocal pos
        if kind() is TokenKind.OPEN:
            pos += 1
            result = parse_or()
            if kind() is not TokenKind.CLOSE:
                raise error("Expected closing parenthesis")
            pos += 1
            return result
        if kind() is not TokenKind.TERM:
            raise error("Expected a term or parenthesized expression")
        result = Term(tokens[pos].text)
        pos += 1
        return result

    result = parse_or()
    if pos != len(tokens):
        raise error("Unexpected trailing token")
    return result
