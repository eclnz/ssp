from string_parser.analysis.terms import collect_terms
from string_parser.syntax.parser import parse


class TestCollectTerms:
    def test_single_term(self) -> None:
        assert collect_terms(parse("COPD")) == {"copd"}

    def test_and_expression(self) -> None:
        assert collect_terms(parse("COPD AND NIV")) == {"copd", "niv"}

    def test_or_expression(self) -> None:
        assert collect_terms(parse("COPD OR AECOPD")) == {"copd", "aecopd"}

    def test_not_expression(self) -> None:
        assert collect_terms(parse("COPD NOT asthma")) == {"copd", "asthma"}

    def test_quoted_phrase_stripped(self) -> None:
        terms = collect_terms(parse('"high flow nasal cannula"'))
        assert "high flow nasal cannula" in terms

    def test_nested_brackets(self) -> None:
        terms = collect_terms(parse('(COPD OR "chronic obstructive pulmonary disease") AND (NIV OR BiPAP)'))
        assert terms == {"copd", "chronic obstructive pulmonary disease", "niv", "bipap"}

    def test_deeply_nested_brackets(self) -> None:
        terms = collect_terms(parse('((COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV)) AND RCT'))
        assert terms == {"copd", "aecopd", "non-invasive ventilation", "niv", "rct"}

    def test_case_insensitive(self) -> None:
        assert collect_terms(parse("COPD AND copd")) == {"copd"}

    def test_quoted_and_unquoted_same_term(self) -> None:
        terms = collect_terms(parse('NIV AND "NIV"'))
        assert terms == {"niv"}
