from dataclasses import FrozenInstanceError

import pytest

from string_parser import BinaryExpr, Op, ParseError, Term, UnaryExpr, parse, unparse
from string_parser.syntax.expressions import rebuild
from string_parser.syntax.tokens import TokenKind, tokenize


def test_precedence_and_quoted_field_suffix():
    expr = parse('A OR B AND NOT "high flow"[tiab]')
    assert expr == BinaryExpr(
        Op.OR, Term("A"), BinaryExpr(Op.AND, Term("B"), UnaryExpr(Op.NOT, Term('"high flow"[tiab]')))
    )
    assert parse(unparse(expr)) == expr


def test_error_and_token_offsets():
    with pytest.raises(ParseError) as error:
        parse("A AND")
    assert error.value.position == 5
    token = tokenize('  "high flow"[tiab]')[0]
    assert token.kind is TokenKind.TERM
    assert (token.start, token.end) == (2, 19)


def test_ast_is_immutable_and_rejects_wrong_operator_arity():
    term = Term("A")
    with pytest.raises(FrozenInstanceError):
        term.value = "B"
    with pytest.raises(ValueError):
        BinaryExpr(Op.NOT, term, term)
    with pytest.raises(ValueError):
        UnaryExpr(Op.OR, term)
    with pytest.raises(ValueError):
        rebuild(Op.AND, [])
