from string_parser import (
    collect_terms,
    combine,
    find_absorbed_branches,
    find_and_redundancies,
    find_duplicate_terms,
    find_subsumed_branches,
    find_subsumed_terms,
    parse,
)


class TestCombineMultipleStrings:
    """Cross-string analysis: SS1, SS2, SS3 treated as a joint OR."""

    def test_combine_two(self) -> None:
        ss1 = parse("COPD AND NIV")
        ss2 = parse("COPD AND oxygen")
        expr = combine(ss1, ss2)
        # COPD appears in both — should be flagged as duplicate
        assert "copd" in find_duplicate_terms(expr)

    def test_combine_three(self) -> None:
        ss1 = parse('"high flow"')
        ss2 = parse('"high flow therapy" AND COPD')
        ss3 = parse("NIV AND COPD")
        expr = combine(ss1, ss2, ss3)
        # "high flow" subsumes "high flow therapy" across SS1 and SS2
        terms = collect_terms(ss1) | collect_terms(ss2) | collect_terms(ss3)
        assert ("high flow", "high flow therapy") in find_subsumed_terms(terms)
        # "high flow" OR ("high flow therapy" AND COPD) — SS1 absorbs SS2 branch
        assert any(a == "high flow" for a, _ in find_absorbed_branches(expr))
        # COPD appears in SS2 and SS3
        assert "copd" in find_duplicate_terms(expr)

    def test_cross_string_branch_subsumption(self) -> None:
        # SS2 is fully subsumed by SS1: "high flow" satisfies "flow", COPD=COPD
        ss1 = parse("flow AND COPD")
        ss2 = parse('"high flow" AND COPD')
        expr = combine(ss1, ss2)
        results = find_subsumed_branches(expr)
        assert any({"flow", "copd"} == s and {"high flow", "copd"} == n for s, n in results)

    def test_cross_string_no_false_and_redundancy(self) -> None:
        # find_and_redundancies should NOT flag cross-OR terms — they're not AND-connected
        ss1 = parse("flow AND COPD")
        ss2 = parse('"high flow" AND COPD')
        pairs = find_and_redundancies(combine(ss1, ss2))
        assert not any({"flow", "high flow"} == set(p) for p in pairs)

    def test_combine_single(self) -> None:
        ss = parse("COPD AND NIV")
        assert combine(ss) is ss
