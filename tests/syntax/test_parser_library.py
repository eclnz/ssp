import pytest

from string_parser import ImplicitAndWarning, ParseError, Term, parse


@pytest.mark.parametrize(
    ("text", "position"),
    [
        ("", 0),
        ("  ", 2),
        ("A AND", 5),
        ("(A", 2),
        ("A)", 1),
        ("A B", 2),
        ('"unterminated', 0),
        ("A AND )", 6),
    ],
)
def test_library_errors_keep_the_public_absolute_character_offset(text, position):
    with pytest.raises(ParseError) as error:
        parse(text)
    assert error.value.position == position


@pytest.mark.parametrize("text", ["AND", "OR", "A AND OR B", "NOT"])
def test_reserved_operators_are_not_reinterpreted_as_terms_by_parser_context(text):
    with pytest.raises(ParseError):
        parse(text)


@pytest.mark.parametrize("text", ["ORBIT", "SAND", "NOTHING", 'AND"two words"', '"AND"'])
def test_keywords_do_not_split_opaque_terms(text):
    assert parse(text) == Term(text)


def test_optional_adjacency_keeps_boolean_precedence_and_does_not_leak_between_modes():
    with pytest.warns(ImplicitAndWarning):
        permissive = parse("A B OR NOT C", allow_implicit_and=True)
    assert permissive == parse("(A AND B) OR NOT C")
    with pytest.raises(ParseError):
        parse("A B OR NOT C")
