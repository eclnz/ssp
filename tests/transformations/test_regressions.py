import pytest

from string_parser import parse, simplify, unparse
from string_parser.conventions.lexical import LEXICAL_PHRASE


@pytest.mark.parametrize("query", ["(A AND NOT B) OR A", "(A AND (B OR C)) OR A"])
def test_partial_conjunctions_never_replace_the_broader_branch(query):
    assert unparse(simplify(parse(query), matcher=LEXICAL_PHRASE)) == "A"
