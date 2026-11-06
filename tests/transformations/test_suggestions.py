from string_parser import MatchPolicy
from string_parser.api import suggest_simplification


class TestSuggestions:
    def test_suggest_returns_none_when_clean(self) -> None:
        assert suggest_simplification("COPD AND NIV", policy=MatchPolicy.LEXICAL_PHRASE) is None

    def test_suggest_returns_simpler_string(self) -> None:
        result = suggest_simplification('"high flow" OR "high flow therapy"', policy=MatchPolicy.LEXICAL_PHRASE)
        assert result == '"high flow"'

    def test_suggest_complex(self) -> None:
        result = suggest_simplification(
            '"high flow" OR "high flow therapy" OR ("high flow nasal" AND COPD)', policy=MatchPolicy.LEXICAL_PHRASE
        )
        assert result == '"high flow"'
