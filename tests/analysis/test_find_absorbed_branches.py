from string_parser import MatchPolicy
from string_parser.analysis.redundancy import find_absorbed_branches
from string_parser.syntax.parser import parse


class TestFindAbsorbedBranches:
    def test_basic_absorption(self) -> None:
        results = find_absorbed_branches(
            parse('"high flow" OR ("high flow therapy" AND COPD)'), policy=MatchPolicy.LEXICAL_PHRASE
        )
        assert len(results) == 1
        absorber, and_terms = results[0]
        assert absorber == "high flow"
        assert "high flow therapy" in and_terms

    def test_exact_term_match_absorbed(self) -> None:
        results = find_absorbed_branches(parse("COPD OR (COPD AND NIV)"), policy=MatchPolicy.LEXICAL_PHRASE)
        assert any((a == "copd" and "copd" in t for a, t in results))

    def test_no_absorption(self) -> None:
        assert find_absorbed_branches(parse("COPD OR (NIV AND oxygen)"), policy=MatchPolicy.LEXICAL_PHRASE) == []

    def test_nested_or_absorption(self) -> None:
        expr = parse("COPD OR AECOPD OR (COPD AND NIV)")
        results = find_absorbed_branches(expr, policy=MatchPolicy.LEXICAL_PHRASE)
        assert any((a == "copd" for a, _ in results))

    def test_complex_quoted_absorption(self) -> None:
        expr = parse('"high flow" OR ("high flow nasal" AND "high flow therapy")')
        results = find_absorbed_branches(expr, policy=MatchPolicy.LEXICAL_PHRASE)
        assert any((a == "high flow" for a, _ in results))

    def test_partial_subsumption_sufficient(self) -> None:
        expr = parse('"high flow" OR ("high flow therapy" AND "nasal cannula")')
        results = find_absorbed_branches(expr, policy=MatchPolicy.LEXICAL_PHRASE)
        assert any((a == "high flow" for a, _ in results))

    def test_no_false_positive_and_only(self) -> None:
        assert (
            find_absorbed_branches(parse('"high flow" AND "high flow therapy"'), policy=MatchPolicy.LEXICAL_PHRASE)
            == []
        )
