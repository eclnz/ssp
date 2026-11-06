from string_parser import MatchPolicy
from string_parser.analysis.redundancy import find_and_redundancies
from string_parser.syntax.parser import parse


class TestFindAndRedundancies:
    def test_basic(self) -> None:
        pairs = find_and_redundancies(parse('flow AND "high flow"'), policy=MatchPolicy.LEXICAL_PHRASE)
        assert ("flow", "high flow") in pairs

    def test_quoted_phrase_vs_quoted_phrase(self) -> None:
        pairs = find_and_redundancies(parse('"high flow" AND "high flow therapy"'), policy=MatchPolicy.LEXICAL_PHRASE)
        assert ("high flow", "high flow therapy") in pairs

    def test_no_redundancy(self) -> None:
        assert find_and_redundancies(parse("COPD AND NIV AND oxygen"), policy=MatchPolicy.LEXICAL_PHRASE) == []

    def test_nested_and(self) -> None:
        pairs = find_and_redundancies(parse('COPD AND (flow AND "high flow")'), policy=MatchPolicy.LEXICAL_PHRASE)
        assert ("flow", "high flow") in pairs

    def test_or_boundary_respected(self) -> None:
        pairs = find_and_redundancies(parse('flow OR "high flow"'), policy=MatchPolicy.LEXICAL_PHRASE)
        assert pairs == []

    def test_complex_nested(self) -> None:
        expr = parse('(COPD OR AECOPD) AND (flow AND "high flow nasal")')
        pairs = find_and_redundancies(expr, policy=MatchPolicy.LEXICAL_PHRASE)
        assert ("flow", "high flow nasal") in pairs
        assert not any(("copd" in p for p in pairs))

    def test_multi_word_phrases_no_false_positive(self) -> None:
        pairs = find_and_redundancies(parse('"nasal cannula" AND "high flow"'), policy=MatchPolicy.LEXICAL_PHRASE)
        assert pairs == []
