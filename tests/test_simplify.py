from string_parser import (
    parse,
    simplify,
    unparse,
)


class TestSimplify:
    def test_or_subsumption_removed(self) -> None:
        # "high flow therapy" is subsumed — should be dropped
        result = unparse(simplify(parse('"high flow" OR "high flow therapy"')))
        assert result == '"high flow"'

    def test_and_redundancy_removed(self) -> None:
        # "flow" is broader than "high flow" — should be dropped from AND
        result = unparse(simplify(parse('flow AND "high flow" AND COPD')))
        assert "flow" not in result.split()  # bare "flow" gone
        assert "high flow" in result
        assert "COPD" in result or "copd" in result

    def test_multiple_or_branches_removed(self) -> None:
        expr = parse('"high flow" OR "high flow therapy" OR ("high flow nasal" AND COPD)')
        result = unparse(simplify(expr))
        assert result == '"high flow"'

    def test_no_change_when_clean(self) -> None:
        s = '(COPD OR AECOPD) AND ("non-invasive ventilation" OR NIV)'
        assert unparse(simplify(parse(s))) == unparse(parse(s))

    def test_nested_and_within_or(self) -> None:
        # (flow AND COPD) OR ("high flow" AND COPD) — second branch subsumed
        result = unparse(simplify(parse('(flow AND COPD) OR ("high flow" AND COPD)')))
        assert "high flow" not in result
        assert "flow" in result
        assert "COPD" in result or "copd" in result
