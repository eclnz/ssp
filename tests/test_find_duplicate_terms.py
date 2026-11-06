from string_parser import (
    find_duplicate_terms,
    parse,
)


class TestFindDuplicateTerms:
    def test_simple_duplicate(self) -> None:
        assert "copd" in find_duplicate_terms(parse("COPD OR (COPD AND NIV)"))

    def test_quoted_duplicate(self) -> None:
        expr = parse('"high flow" OR ("high flow" AND COPD)')
        assert "high flow" in find_duplicate_terms(expr)

    def test_no_duplicate(self) -> None:
        assert find_duplicate_terms(parse("(COPD OR AECOPD) AND NIV")) == []

    def test_case_normalised(self) -> None:
        # COPD and copd should count as one repeated term
        assert "copd" in find_duplicate_terms(parse("COPD AND copd"))

    def test_deeply_nested_duplicate(self) -> None:
        expr = parse("((COPD OR NIV) AND (COPD OR oxygen))")
        assert "copd" in find_duplicate_terms(expr)

    def test_three_occurrences(self) -> None:
        expr = parse("COPD OR (COPD AND (COPD OR NIV))")
        dupes = find_duplicate_terms(expr)
        assert "copd" in dupes
        assert "niv" not in dupes
