from string_parser import MatchPolicy
from string_parser.api import format_simplification_diff


class TestFormatSimplificationDiff:
    def test_removed_branches_highlighted(self) -> None:
        diff = format_simplification_diff('"high flow" OR "high flow therapy"', policy=MatchPolicy.LEXICAL_PHRASE)
        assert diff is not None
        assert "\x1b[31m" in diff
        assert '"high flow therapy"' in diff
        assert diff.startswith('("high flow"')

    def test_none_when_no_change(self) -> None:
        assert format_simplification_diff("COPD AND NIV", policy=MatchPolicy.LEXICAL_PHRASE) is None

    def test_kept_branch_not_highlighted(self) -> None:
        diff = format_simplification_diff(
            '"high flow" OR "high flow therapy" OR COPD', policy=MatchPolicy.LEXICAL_PHRASE
        )
        assert diff is not None
        reset = "\x1b[0m"
        red = "\x1b[31m"
        assert f"{red}COPD{reset}" not in diff and f"{red}copd{reset}" not in diff
