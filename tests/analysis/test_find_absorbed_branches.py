from string_parser import (
    find_absorbed_branches,
    parse,
)


class TestFindAbsorbedBranches:
    def test_basic_absorption(self) -> None:
        # "high flow" OR ("high flow therapy" AND COPD) — "high flow" absorbs the AND
        results = find_absorbed_branches(parse('"high flow" OR ("high flow therapy" AND COPD)'))
        assert len(results) == 1
        absorber, and_terms = results[0]
        assert absorber == "high flow"
        assert "high flow therapy" in and_terms

    def test_exact_term_match_absorbed(self) -> None:
        # COPD OR (COPD AND NIV) = COPD
        results = find_absorbed_branches(parse("COPD OR (COPD AND NIV)"))
        assert any(a == "copd" and "copd" in t for a, t in results)

    def test_no_absorption(self) -> None:
        # unrelated terms — no absorption
        assert find_absorbed_branches(parse("COPD OR (NIV AND oxygen)")) == []

    def test_nested_or_absorption(self) -> None:
        # (A OR B) OR (A AND C) — A should absorb at the top-level OR
        expr = parse("COPD OR AECOPD OR (COPD AND NIV)")
        results = find_absorbed_branches(expr)
        assert any(a == "copd" for a, _ in results)

    def test_complex_quoted_absorption(self) -> None:
        # "high flow" absorbs ("high flow nasal" AND "high flow therapy")
        # because "high flow" is subphrase of both terms in the AND
        expr = parse('"high flow" OR ("high flow nasal" AND "high flow therapy")')
        results = find_absorbed_branches(expr)
        assert any(a == "high flow" for a, _ in results)

    def test_partial_subsumption_sufficient(self) -> None:
        # T only needs to subsume ONE term in the AND for the branch to be absorbed
        # "high flow" OR ("high flow therapy" AND "nasal cannula")
        # "high flow" ⊂ "high flow therapy" → AND branch absorbed
        expr = parse('"high flow" OR ("high flow therapy" AND "nasal cannula")')
        results = find_absorbed_branches(expr)
        assert any(a == "high flow" for a, _ in results)

    def test_no_false_positive_and_only(self) -> None:
        # Pure AND — no OR to absorb into
        assert find_absorbed_branches(parse('"high flow" AND "high flow therapy"')) == []
