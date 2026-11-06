import pytest

from string_parser import ParseError, parse


@pytest.mark.parametrize("query", ["", "A AND", "A)", "(A OR B", '"unterminated'])
def test_malformed_queries_have_one_error_contract(query):
    with pytest.raises(ParseError):
        parse(query)
