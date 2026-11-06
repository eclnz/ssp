from string_parser import (
    find_subsumed_terms,
)


class TestFindSubsumedTerms:
    def test_basic_subphrase(self) -> None:
        # "high flow" subsumes "high flow therapy"
        pairs = find_subsumed_terms({"high flow", "high flow therapy", "copd"})
        assert ("high flow", "high flow therapy") in pairs

    def test_middle_subphrase(self) -> None:
        # "flow nasal" appears inside "high flow nasal cannula"
        pairs = find_subsumed_terms({"flow nasal", "high flow nasal cannula"})
        assert ("flow nasal", "high flow nasal cannula") in pairs

    def test_no_subsumption(self) -> None:
        assert find_subsumed_terms({"copd", "niv", "bipap"}) == []

    def test_exact_match_not_flagged(self) -> None:
        # same term twice would be a duplicate, not a subphrase
        assert find_subsumed_terms({"high flow"}) == []

    def test_multiple_subsumed_by_one(self) -> None:
        pairs = find_subsumed_terms({"high flow", "high flow therapy", "high flow nasal cannula"})
        broader = {p[0] for p in pairs}
        narrower = {p[1] for p in pairs}
        assert broader == {"high flow"}
        assert narrower == {"high flow therapy", "high flow nasal cannula"}
