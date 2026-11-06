from string_parser import suggest_simplification


class TestSuggestions:
    def test_suggest_returns_none_when_clean(self) -> None:
        assert suggest_simplification("COPD AND NIV") is None

    def test_suggest_returns_simpler_string(self) -> None:
        result = suggest_simplification('"high flow" OR "high flow therapy"')
        assert result == '"high flow"'

    def test_suggest_complex(self) -> None:
        result = suggest_simplification('"high flow" OR "high flow therapy" OR ("high flow nasal" AND COPD)')
        assert result == '"high flow"'
