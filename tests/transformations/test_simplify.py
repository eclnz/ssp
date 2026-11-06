from string_parser import MatchPolicy
from string_parser.syntax.parser import parse
from string_parser.syntax.serialization import unparse
from string_parser.transformations.simplification import simplify


class TestSimplify:
    def test_or_subsumption_removed(self) -> None:
        result = unparse(simplify(parse('"high flow" OR "high flow therapy"'), policy=MatchPolicy.LEXICAL_PHRASE))
        assert result == '"high flow"'

    def test_and_redundancy_removed(self) -> None:
        result = unparse(simplify(parse('flow AND "high flow" AND COPD'), policy=MatchPolicy.LEXICAL_PHRASE))
        assert "flow" not in result.split()
        assert "high flow" in result
        assert "COPD" in result or "copd" in result

    def test_multiple_or_branches_removed(self) -> None:
        expr = parse('"high flow" OR "high flow therapy" OR ("high flow nasal" AND COPD)')
        result = unparse(simplify(expr, policy=MatchPolicy.LEXICAL_PHRASE))
        assert result == '"high flow"'

    def test_no_change_when_clean(self) -> None:
        s = '(COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV)'
        assert unparse(simplify(parse(s), policy=MatchPolicy.LEXICAL_PHRASE)) == unparse(parse(s))

    def test_nested_and_within_or(self) -> None:
        result = unparse(
            simplify(parse('(flow AND COPD) OR ("high flow" AND COPD)'), policy=MatchPolicy.LEXICAL_PHRASE)
        )
        assert "high flow" not in result
        assert "flow" in result
        assert "COPD" in result or "copd" in result
