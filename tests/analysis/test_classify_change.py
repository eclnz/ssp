from string_parser import (
    classify_change,
)


class TestClassifyChange:
    def test_pure_expansion(self) -> None:
        added, removed = classify_change(
            '(COPD OR "chronic obstructive pulmonary disease") AND NIV',
            '(COPD OR "chronic obstructive pulmonary disease") AND (NIV OR BiPAP)',
        )
        assert added == {"bipap"}
        assert removed == set()

    def test_pure_narrowing(self) -> None:
        added, removed = classify_change(
            '(COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV OR BiPAP)',
            '(COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV)',
        )
        assert added == set()
        assert removed == {"bipap"}

    def test_mixed_change(self) -> None:
        added, removed = classify_change(
            '(COPD OR AECOPD) AND "non-invasive ventilation"',
            '(COPD OR AECOPD) AND "high flow nasal cannula"',
        )
        assert added == {"high flow nasal cannula"}
        assert removed == {"non-invasive ventilation"}

    def test_structural_change_same_terms(self) -> None:
        added, removed = classify_change(
            "(COPD AND NIV)",
            "COPD OR NIV",
        )
        assert added == set()
        assert removed == set()

    def test_identical_strings(self) -> None:
        added, removed = classify_change(
            '(COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV)',
            '(COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV)',
        )
        assert added == set()
        assert removed == set()

    def test_quoted_phrase_expansion(self) -> None:
        added, removed = classify_change(
            "COPD AND NIV",
            'COPD AND (NIV OR "high flow nasal oxygen")',
        )
        assert added == {"high flow nasal oxygen"}
        assert removed == set()
