from string_parser import MatchPolicy
from string_parser.api import lint_string


class TestLint:
    def test_lint_or_redundancy(self) -> None:
        issues = lint_string('"high flow" OR "high flow therapy"', policy=MatchPolicy.LEXICAL_PHRASE)
        assert any(("OR redundancy" in i for i in issues))

    def test_lint_and_redundancy(self) -> None:
        issues = lint_string('flow AND "high flow" AND COPD', policy=MatchPolicy.LEXICAL_PHRASE)
        assert any(("AND redundancy" in i for i in issues))

    def test_lint_duplicate(self) -> None:
        issues = lint_string("COPD OR (COPD AND NIV)", policy=MatchPolicy.LEXICAL_PHRASE)
        assert any(("Duplicate" in i for i in issues))

    def test_lint_clean_string(self) -> None:
        assert lint_string("(COPD OR AECOPD) AND NIV", policy=MatchPolicy.LEXICAL_PHRASE) == []
