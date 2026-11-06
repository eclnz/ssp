from string_parser import (
    format_string_diff,
)


class TestFormatStringDiff:
    def test_reordered_or_returns_none(self) -> None:
        assert format_string_diff("COPD OR AECOPD", "AECOPD OR COPD") is None

    def test_reordered_and_returns_none(self) -> None:
        assert format_string_diff("COPD AND NIV", "NIV AND COPD") is None

    def test_reordered_nested_returns_none(self) -> None:
        assert (
            format_string_diff(
                "(COPD OR AECOPD) AND (NIV OR BiPAP)",
                "(AECOPD OR COPD) AND (BiPAP OR NIV)",
            )
            is None
        )

    def test_genuine_addition_not_none(self) -> None:
        assert format_string_diff("COPD AND NIV", "COPD AND NIV AND BiPAP") is not None

    def test_genuine_removal_not_none(self) -> None:
        assert format_string_diff("COPD AND NIV", "COPD") is not None

    def test_or_collapse_shows_removed_term_not_whole_branch(self) -> None:
        # (COPD OR AECOPD) → COPD: AECOPD removed, COPD retained — not a wholesale replacement
        pair = format_string_diff(
            "(COPD OR AECOPD) AND (NIV OR BiPAP)",
            "COPD AND (NIV OR BiPAP)",
        )
        assert pair is not None
        was, now = pair
        assert "\033[31m" in was  # something is red
        assert "AECOPD" in was  # AECOPD flagged
        assert "COPD" in now  # COPD present in result
        # COPD should not itself be coloured green (it wasn't added)
        assert "\033[32mCOPD\033[0m" not in now

    def test_or_expansion_shows_added_term_not_whole_branch(self) -> None:
        # COPD → (COPD OR AECOPD): AECOPD added, COPD retained
        pair = format_string_diff(
            "COPD AND (NIV OR BiPAP)",
            "(COPD OR AECOPD) AND (NIV OR BiPAP)",
        )
        assert pair is not None
        was, now = pair
        assert "\033[32m" in now  # something is green
        assert "AECOPD" in now  # AECOPD flagged
        assert "\033[32mCOPD\033[0m" not in now  # COPD not falsely green
