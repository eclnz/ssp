from string_parser import lint_string


class TestLint:
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
