import pytest

from string_parser import ImplicitAndWarning, ParseError, parse


@pytest.mark.parametrize("text", ["A B", "A NOT B", "A (B OR C)"])
def test_adjacency_requires_explicit_opt_in(text):
    with pytest.raises(ParseError):
        parse(text)
    with pytest.warns(ImplicitAndWarning):
        expr = parse(text, allow_implicit_and=True)
    assert expr is not None
