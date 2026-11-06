from string_parser import (
    find_subsumed_branches,
    parse,
)


class TestFindSubsumedBranches:
    def test_bare_term_subsumes_and_branch(self) -> None:
        # "high flow" OR ("high flow therapy" AND COPD) — first branch subsumes second
        expr = parse('"high flow" OR ("high flow therapy" AND COPD)')
        results = find_subsumed_branches(expr)
        assert any({"high flow"} == s and {"high flow therapy", "copd"} == n for s, n in results)

    def test_and_branch_subsumes_and_branch(self) -> None:
        # (flow AND COPD) OR ("high flow" AND COPD) — first subsumes second
        expr = parse('(flow AND COPD) OR ("high flow" AND COPD)')
        results = find_subsumed_branches(expr)
        assert any({"flow", "copd"} == s and {"high flow", "copd"} == n for s, n in results)

    def test_extra_term_in_subsumed_still_subsumed(self) -> None:
        # ("high flow" AND COPD) OR ("high flow therapy" AND COPD AND NIV)
        # second branch has extra NIV but is still subsumed — any match of it satisfies the first
        expr = parse('("high flow" AND COPD) OR ("high flow therapy" AND COPD AND NIV)')
        results = find_subsumed_branches(expr)
        assert any({"high flow", "copd"} == s for s, _ in results)

    def test_no_subsumption_disjoint_terms(self) -> None:
        expr = parse("(COPD AND oxygen) OR (NIV AND BiPAP)")
        assert find_subsumed_branches(expr) == []

    def test_not_symmetric(self) -> None:
        # "high flow" subsumes "high flow therapy", not the other way round
        expr = parse('"high flow" OR "high flow therapy"')
        results = find_subsumed_branches(expr)
        subsuming = [s for s, _ in results]
        subsumed = [n for _, n in results]
        assert {"high flow"} in subsuming
        assert {"high flow therapy"} in subsumed
        assert not any(n == {"high flow"} for n in subsumed)

    def test_three_branches_transitive(self) -> None:
        # "flow" subsumes "high flow" subsumes "high flow therapy"
        expr = parse('flow OR "high flow" OR "high flow therapy"')
        results = find_subsumed_branches(expr)
        subsumed = {frozenset(n) for _, n in results}
        assert frozenset({"high flow"}) in subsumed
        assert frozenset({"high flow therapy"}) in subsumed

    def test_identical_branches_not_flagged(self) -> None:
        # identical branches are duplicates, not subsumptions
        expr = parse("COPD OR COPD")
        assert find_subsumed_branches(expr) == []
