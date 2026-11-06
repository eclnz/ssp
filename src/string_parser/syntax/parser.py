"""Database-neutral Boolean grammar backed by Lark."""

from __future__ import annotations

import warnings
from functools import lru_cache

from lark import Lark, Token, Transformer_NonRecursive, UnexpectedInput, UnexpectedToken

from .expressions import BinaryExpr, Expr, Op, Term, UnaryExpr


class ParseError(ValueError):
    """Invalid query syntax at a zero-based character offset."""

    def __init__(self, message: str, position: int):
        self.position = position
        super().__init__(f"{message} at character {position}")


class ImplicitAndWarning(UserWarning):
    """Adjacent operands have been joined with an implicit AND."""


_GRAMMAR = r"""
?start: disjunction
?disjunction: disjunction _OR conjunction -> disjoin
            | conjunction
?conjunction: conjunction _AND unary -> conjoin
              IMPLICIT_AND
            | unary
?unary: _NOT unary -> negate
      | atom
?atom: TERM -> term
     | "(" disjunction ")"
_AND.2: /AND(?=$|[\s()])/
_OR.2: /OR(?=$|[\s()])/
_NOT.2: /NOT(?=$|[\s()])/
TERM: /(?:"[^"\n]*"|[^"\s()])+/
%ignore /\s+/
"""


class _Expressions(Transformer_NonRecursive[Token, Expr]):
    def term(self, tokens: list[Token]) -> Expr:
        return Term(str(tokens[0]))

    def disjoin(self, operands: list[Expr]) -> Expr:
        return BinaryExpr(Op.OR, operands[0], operands[1])

    def conjoin(self, operands: list[Expr]) -> Expr:
        return BinaryExpr(Op.AND, operands[0], operands[1])

    def negate(self, operands: list[Expr]) -> Expr:
        return UnaryExpr(Op.NOT, operands[0])

    def implicit_conjoin(self, operands: list[Expr]) -> Expr:
        warnings.warn("Adjacent operands treated as AND", ImplicitAndWarning, stacklevel=2)
        return self.conjoin(operands)


@lru_cache(maxsize=2)
def _parser(allow_implicit_and: bool) -> Lark:
    implicit = "| conjunction unary -> implicit_conjoin" if allow_implicit_and else ""
    return Lark(_GRAMMAR.replace("IMPLICIT_AND", implicit), parser="lalr", lexer="basic")


def parse(text: str, *, allow_implicit_and: bool = False) -> Expr:
    """Parse a complete query into SSP expressions; implicit AND requires opt-in."""
    try:
        tree = _parser(allow_implicit_and).parse(text)
    except UnexpectedInput as error:
        at_end = isinstance(error, UnexpectedToken) and error.token.type == "$END"
        offset = error.pos_in_stream
        position = len(text) if at_end or offset is None or offset < 0 else offset
        raise ParseError("Invalid Boolean query", position) from error
    return _Expressions().transform(tree)
