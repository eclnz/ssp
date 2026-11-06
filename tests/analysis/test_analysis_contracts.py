from string_parser import compare_expressions, compare_terms, parse
from string_parser.presentation import render_diff


def test_term_inventory_and_structural_changes_are_separate():
    for query in ("A OR B", "A AND NOT B"):
        before, after = parse("A AND B"), parse(query)
        assert compare_terms(before, after) == (set(), set())
        diff = compare_expressions(before, after)
        assert diff is not None
        a, b = render_diff(diff, color=False)
        assert parse(a) == before and parse(b) == after


def test_reorderings_are_visible_unless_explicitly_suppressed():
    a, b = parse("A OR (B OR C)"), parse("(C OR A) OR B")
    assert compare_expressions(a, b) is not None
    assert compare_expressions(a, b, ignore_operand_order=True) is None
