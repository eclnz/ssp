"""Boolean grammar with explicit parsing conventions."""

from __future__ import annotations

import warnings
from dataclasses import dataclass

from .expressions import BinaryExpr, Expr, Op, Term, UnaryExpr
from .tokens import ParseError, Token, TokenKind, tokenize


class ImplicitAndWarning(UserWarning):
    """Adjacent operands have been joined with an implicit AND."""


@dataclass
class _Parser:
    tokens: list[Token]
    end_position: int
    allow_implicit_and: bool = False
    position: int = 0

    def parse(self) -> Expr:
        result = self._parse_or()
        if self.position != len(self.tokens):
            raise self._error("Unexpected trailing token")
        return result

    def _kind(self) -> TokenKind | None:
        return self.tokens[self.position].kind if self.position < len(self.tokens) else None

    def _error(self, message: str) -> ParseError:
        offset = self.tokens[self.position].start if self.position < len(self.tokens) else self.end_position
        return ParseError(message, offset)

    def _parse_or(self) -> Expr:
        left = self._parse_and()
        while self._kind() is TokenKind.OR:
            self.position += 1
            left = BinaryExpr(Op.OR, left, self._parse_and())
        return left

    def _parse_and(self) -> Expr:
        left = self._parse_not()
        while True:
            if self._kind() is TokenKind.AND:
                self.position += 1
            elif self.allow_implicit_and and self._kind() in (TokenKind.TERM, TokenKind.OPEN, TokenKind.NOT):
                warnings.warn("Adjacent operands treated as AND", ImplicitAndWarning, stacklevel=3)
            else:
                break
            left = BinaryExpr(Op.AND, left, self._parse_not())
        return left

    def _parse_not(self) -> Expr:
        if self._kind() is TokenKind.NOT:
            self.position += 1
            return UnaryExpr(Op.NOT, self._parse_not())
        return self._parse_atom()

    def _parse_atom(self) -> Expr:
        if self._kind() is TokenKind.OPEN:
            self.position += 1
            result = self._parse_or()
            if self._kind() is not TokenKind.CLOSE:
                raise self._error("Expected closing parenthesis")
            self.position += 1
            return result
        if self._kind() is not TokenKind.TERM:
            raise self._error("Expected a term or parenthesized expression")
        result = Term(self.tokens[self.position].text)
        self.position += 1
        return result


def parse(text: str, *, allow_implicit_and: bool = False) -> Expr:
    """Parse a complete query or raise ParseError; implicit AND requires opt-in."""
    return _Parser(tokenize(text), len(text), allow_implicit_and).parse()
