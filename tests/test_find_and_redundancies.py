from string_parser import (
    find_and_redundancies,
    parse,
)


class TestFindAndRedundancies:
    def test_basic(self) -> None:
        # "flow" is always satisfied when "high flow" is
        pairs = find_and_redundancies(parse('flow AND "high flow"'))
        assert ("flow", "high flow") in pairs

    def test_quoted_phrase_vs_quoted_phrase(self) -> None:
        pairs = find_and_redundancies(parse('"high flow" AND "high flow therapy"'))
        assert ("high flow", "high flow therapy") in pairs

    def test_no_redundancy(self) -> None:
        assert find_and_redundancies(parse("COPD AND NIV AND oxygen")) == []

    def test_nested_and(self) -> None:
        # redundancy inside a deeper AND
        pairs = find_and_redundancies(parse('COPD AND (flow AND "high flow")'))
        assert ("flow", "high flow") in pairs

    def test_or_boundary_respected(self) -> None:
        # "flow" and "high flow" are in different OR branches — NOT AND-connected
        pairs = find_and_redundancies(parse('flow OR "high flow"'))
        assert pairs == []

    def test_complex_nested(self) -> None:
        # (COPD OR AECOPD) AND (flow AND "high flow nasal") — redundancy inside inner AND
        expr = parse('(COPD OR AECOPD) AND (flow AND "high flow nasal")')
        pairs = find_and_redundancies(expr)
        assert ("flow", "high flow nasal") in pairs
        # COPD is not AND-connected to flow (separated by OR on the left)
        assert not any("copd" in p for p in pairs)

    def test_multi_word_phrases_no_false_positive(self) -> None:
        # "nasal cannula" and "high flow" share no subphrase relationship
        pairs = find_and_redundancies(parse('"nasal cannula" AND "high flow"'))
        assert pairs == []
