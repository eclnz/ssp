import pytest

from string_parser import EXACT, BinaryExpr, TermMatcher, parse, simplify
from string_parser.analysis.redundancy import find_redundant_operands
from string_parser.conventions.lexical import LEXICAL_PHRASE
from string_parser.syntax.expressions import flatten


class CasefoldMatcher:
    def covers_term(self, broader: str, narrower: str) -> bool:
        return broader.casefold() == narrower.casefold()


@pytest.mark.parametrize("matcher", [EXACT, LEXICAL_PHRASE, CasefoldMatcher()])
def test_matcher_substitution_requires_only_coverage(matcher: TermMatcher):
    assert simplify(parse("A AND (A OR B)"), matcher=matcher) == parse("A")


@pytest.mark.parametrize(
    "query",
    [
        "(A AND B AND C) OR (A AND B) OR A",
        "A AND (A OR B) AND (A OR B OR C)",
    ],
)
def test_evidence_names_witnesses_that_survive_the_entire_group(query):
    expr = parse(query)
    assert isinstance(expr, BinaryExpr)
    findings = find_redundant_operands(expr)
    assert len(findings) == 2
    removed = {item.redundant_index for item in findings}
    assert all(item.retained_index not in removed for item in findings)
    survivors = [node for i, node in enumerate(flatten(expr, expr.op)) if i not in removed]
    assert survivors == [parse("A")]
    assert simplify(expr) == parse("A")
