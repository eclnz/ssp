from string_parser import (
    format_simplification_diff,
)


class TestFormatSimplificationDiff:
    def test_removed_branches_highlighted(self) -> None:
        diff = format_simplification_diff('"high flow" OR "high flow therapy"')
        assert diff is not None
        assert "\033[31m" in diff  # red escape present
        assert '"high flow therapy"' in diff  # removed term shown
        assert diff.startswith('"high flow"')  # kept term comes first, unstyled

    def test_none_when_no_change(self) -> None:
        assert format_simplification_diff("COPD AND NIV") is None

    def test_kept_branch_not_highlighted(self) -> None:
        diff = format_simplification_diff('"high flow" OR "high flow therapy" OR COPD')
        assert diff is not None
        # COPD is not subsumed by "high flow" — should not be in red
        reset = "\033[0m"
        red = "\033[31m"
        # find COPD segment — should not be preceded by red code
        assert f"{red}COPD{reset}" not in diff and f"{red}copd{reset}" not in diff
