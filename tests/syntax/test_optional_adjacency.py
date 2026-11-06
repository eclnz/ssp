import pytest

from string_parser import ImplicitAndWarning, ParseError, parse
from string_parser.api import canonically_equal


@pytest.mark.parametrize("text", ["A B", "A NOT B", "A (B OR C)"])
def test_adjacency_requires_explicit_opt_in(text):
    with pytest.raises(ParseError):
        parse(text)
    with pytest.warns(ImplicitAndWarning):
        expr = parse(text, allow_implicit_and=True)
    assert expr is not None


def test_string_facade_forwards_the_selected_parsing_convention():
    with pytest.raises(ParseError):
        canonically_equal("A B", "A AND B")
    with pytest.warns(ImplicitAndWarning):
        assert canonically_equal("A B", "A AND B", allow_implicit_and=True)
