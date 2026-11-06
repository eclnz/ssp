from string_parser import MatchPolicy
from string_parser.analysis.redundancy import (
    find_absorbed_branches,
    find_and_redundancies,
    find_duplicate_terms,
    find_subsumed_branches,
    find_subsumed_terms,
)
from string_parser.analysis.terms import collect_terms
from string_parser.syntax.parser import parse
from string_parser.syntax.tree import combine


class TestCombineMultipleStrings:
    """Cross-string analysis: SS1, SS2, SS3 treated as a joint OR."""

    def test_combine_two(self) -> None:
        ss1 = parse("COPD AND NIV")
        ss2 = parse("COPD AND oxygen")
        expr = combine(ss1, ss2)
        assert "copd" in find_duplicate_terms(expr, policy=MatchPolicy.LEXICAL_PHRASE)

    def test_combine_three(self) -> None:
        ss1 = parse('"high flow"')
        ss2 = parse('"high flow therapy" AND COPD')
        ss3 = parse("NIV AND COPD")
        expr = combine(ss1, ss2, ss3)
        terms = collect_terms(ss1) | collect_terms(ss2) | collect_terms(ss3)
        assert ("high flow", "high flow therapy") in find_subsumed_terms(terms, policy=MatchPolicy.LEXICAL_PHRASE)
        assert any((a == "high flow" for a, _ in find_absorbed_branches(expr, policy=MatchPolicy.LEXICAL_PHRASE)))
        assert "copd" in find_duplicate_terms(expr, policy=MatchPolicy.LEXICAL_PHRASE)

    def test_cross_string_branch_subsumption(self) -> None:
        ss1 = parse("flow AND COPD")
        ss2 = parse('"high flow" AND COPD')
        expr = combine(ss1, ss2)
        results = find_subsumed_branches(expr, policy=MatchPolicy.LEXICAL_PHRASE)
        assert any(({"flow", "copd"} == s and {"high flow", "copd"} == n for s, n in results))

    def test_cross_string_no_false_and_redundancy(self) -> None:
        ss1 = parse("flow AND COPD")
        ss2 = parse('"high flow" AND COPD')
        pairs = find_and_redundancies(combine(ss1, ss2), policy=MatchPolicy.LEXICAL_PHRASE)
        assert not any(({"flow", "high flow"} == set(p) for p in pairs))

    def test_combine_single(self) -> None:
        ss = parse("COPD AND NIV")
        assert combine(ss) is ss
