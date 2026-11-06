import pytest

from string_parser import canonicalize, parse


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("A OR B", "B OR A"),
        ("A AND B", "B AND A"),
        ("(A OR B) AND NOT C", "NOT C AND (B OR A)"),
        ("A OR (B OR C)", "(C OR A) OR B"),
    ],
)
def test_canonicalization_is_independent_of_association_and_operand_order(a, b):
    assert canonicalize(parse(a)) == canonicalize(parse(b))


def test_canonicalization_does_not_equate_different_operators_or_symbols():
    assert canonicalize(parse("A AND B")) != canonicalize(parse("A OR B"))
    assert canonicalize(parse("A")) != canonicalize(parse("a"))
