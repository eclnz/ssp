from dataclasses import FrozenInstanceError

import pytest

from string_parser import BinaryExpr, Op, ParseError, Term, UnaryExpr, parse, unparse
from string_parser.syntax.expressions import rebuild


def test_precedence_and_quoted_terms():
    expr = parse('A OR B AND NOT "two words"')
    assert expr == BinaryExpr(Op.OR, Term("A"), BinaryExpr(Op.AND, Term("B"), UnaryExpr(Op.NOT, Term('"two words"'))))
    assert parse(unparse(expr)) == expr


def test_parse_errors_retain_character_offsets():
    with pytest.raises(ParseError) as error:
        parse("A AND")
    assert error.value.position == 5


def test_ast_is_immutable_and_rejects_wrong_operator_arity():
    term = Term("A")
    with pytest.raises(FrozenInstanceError):
        term.value = "B"  # pyright: ignore[reportAttributeAccessIssue] - intentional mutation attempt
    with pytest.raises(ValueError):
        BinaryExpr(Op.NOT, term, term)
    with pytest.raises(ValueError):
        UnaryExpr(Op.OR, term)
    with pytest.raises(ValueError):
        rebuild(Op.AND, [])


@pytest.mark.parametrize("lexeme", ['"two words":label', 'prefix"two words"', '"two words"{label}'])
def test_contiguous_quoted_and_unquoted_fragments_are_opaque_terms(lexeme):
    assert parse(lexeme) == Term(lexeme)
    assert unparse(parse(lexeme)) == lexeme
