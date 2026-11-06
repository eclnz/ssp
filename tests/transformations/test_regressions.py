import pytest

from string_parser import MatchPolicy, parse, simplify, unparse


@pytest.mark.parametrize("query", ["(A AND NOT B) OR A", "(A AND (B OR C)) OR A"])
def test_partial_conjunctions_never_replace_the_broader_branch(query):
    assert unparse(simplify(parse(query), policy=MatchPolicy.LEXICAL_PHRASE)) == "A"
