from string_parser.analysis.changes import compare_terms
from string_parser.syntax.parser import parse


class TestCompareTerms:
    def test_pure_expansion(self) -> None:
        added, removed = compare_terms(
            parse('(COPD OR "chronic obstructive pulmonary disease") AND NIV'),
            parse('(COPD OR "chronic obstructive pulmonary disease") AND (NIV OR BiPAP)'),
        )
        assert added == {"bipap"}
        assert removed == set()

    def test_pure_narrowing(self) -> None:
        added, removed = compare_terms(
            parse('(COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV OR BiPAP)'),
            parse('(COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV)'),
        )
        assert added == set()
        assert removed == {"bipap"}

    def test_mixed_change(self) -> None:
        added, removed = compare_terms(
            parse('(COPD OR AECOPD) AND "non-invasive ventilation"'),
            parse('(COPD OR AECOPD) AND "high flow nasal cannula"'),
        )
        assert added == {"high flow nasal cannula"}
        assert removed == {"non-invasive ventilation"}

    def test_structural_change_same_terms(self) -> None:
        added, removed = compare_terms(parse("(COPD AND NIV)"), parse("COPD OR NIV"))
        assert added == set()
        assert removed == set()

    def test_identical_strings(self) -> None:
        added, removed = compare_terms(
            parse('(COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV)'),
            parse('(COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV)'),
        )
        assert added == set()
        assert removed == set()

    def test_quoted_phrase_expansion(self) -> None:
        added, removed = compare_terms(parse("COPD AND NIV"), parse('COPD AND (NIV OR "high flow nasal oxygen")'))
        assert added == {"high flow nasal oxygen"}
        assert removed == set()
