from string_parser import MatchPolicy
from string_parser.analysis.redundancy import find_duplicate_terms
from string_parser.syntax.parser import parse


class TestFindDuplicateTerms:
    def test_simple_duplicate(self) -> None:
        assert "copd" in find_duplicate_terms(parse("COPD OR (COPD AND NIV)"), policy=MatchPolicy.LEXICAL_PHRASE)

    def test_quoted_duplicate(self) -> None:
        expr = parse('"high flow" OR ("high flow" AND COPD)')
        assert "high flow" in find_duplicate_terms(expr, policy=MatchPolicy.LEXICAL_PHRASE)

    def test_no_duplicate(self) -> None:
        assert find_duplicate_terms(parse("(COPD OR AECOPD) AND NIV"), policy=MatchPolicy.LEXICAL_PHRASE) == []

    def test_case_normalised(self) -> None:
        assert "copd" in find_duplicate_terms(parse("COPD AND copd"), policy=MatchPolicy.LEXICAL_PHRASE)

    def test_deeply_nested_duplicate(self) -> None:
        expr = parse("((COPD OR NIV) AND (COPD OR oxygen))")
        assert "copd" in find_duplicate_terms(expr, policy=MatchPolicy.LEXICAL_PHRASE)

    def test_three_occurrences(self) -> None:
        expr = parse("COPD OR (COPD AND (COPD OR NIV))")
        dupes = find_duplicate_terms(expr, policy=MatchPolicy.LEXICAL_PHRASE)
        assert "copd" in dupes
        assert "niv" not in dupes
