from string_parser import MatchPolicy
from string_parser.analysis.redundancy import find_subsumed_terms


class TestFindSubsumedTerms:
    def test_basic_subphrase(self) -> None:
        pairs = find_subsumed_terms({"high flow", "high flow therapy", "copd"}, policy=MatchPolicy.LEXICAL_PHRASE)
        assert ("high flow", "high flow therapy") in pairs

    def test_middle_subphrase(self) -> None:
        pairs = find_subsumed_terms({"flow nasal", "high flow nasal cannula"}, policy=MatchPolicy.LEXICAL_PHRASE)
        assert ("flow nasal", "high flow nasal cannula") in pairs

    def test_no_subsumption(self) -> None:
        assert find_subsumed_terms({"copd", "niv", "bipap"}, policy=MatchPolicy.LEXICAL_PHRASE) == []

    def test_exact_match_not_flagged(self) -> None:
        assert find_subsumed_terms({"high flow"}, policy=MatchPolicy.LEXICAL_PHRASE) == []

    def test_multiple_subsumed_by_one(self) -> None:
        pairs = find_subsumed_terms(
            {"high flow", "high flow therapy", "high flow nasal cannula"}, policy=MatchPolicy.LEXICAL_PHRASE
        )
        broader = {p[0] for p in pairs}
        narrower = {p[1] for p in pairs}
        assert broader == {"high flow"}
        assert narrower == {"high flow therapy", "high flow nasal cannula"}
