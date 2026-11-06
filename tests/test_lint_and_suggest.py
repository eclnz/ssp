from string_parser import (
    lint_string,
    suggest_simplification,
)


class TestLintAndSuggest:
    def test_lint_or_redundancy(self) -> None:
        issues = lint_string('"high flow" OR "high flow therapy"')
        assert any("OR redundancy" in i for i in issues)

    def test_lint_and_redundancy(self) -> None:
        issues = lint_string('flow AND "high flow" AND COPD')
        assert any("AND redundancy" in i for i in issues)

    def test_lint_duplicate(self) -> None:
        issues = lint_string("COPD OR (COPD AND NIV)")
        assert any("Duplicate" in i for i in issues)

    def test_lint_clean_string(self) -> None:
        assert lint_string("(COPD OR AECOPD) AND NIV") == []

    def test_suggest_returns_none_when_clean(self) -> None:
        assert suggest_simplification("COPD AND NIV") is None

    def test_suggest_returns_simpler_string(self) -> None:
        result = suggest_simplification('"high flow" OR "high flow therapy"')
        assert result == '"high flow"'

    def test_suggest_complex(self) -> None:
        result = suggest_simplification('"high flow" OR "high flow therapy" OR ("high flow nasal" AND COPD)')
        assert result == '"high flow"'
