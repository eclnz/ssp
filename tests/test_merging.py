from itertools import product
from random import Random

import pytest

from string_parser import BinaryExpr, Op, Term, UnaryExpr, merge_revisions, parse
from string_parser.analysis.revisions import structural_edits


@pytest.mark.parametrize(
    ("base", "left", "right", "expected"),
    [
        ("A", "A", "B", "B"),
        ("A", "B", "A", "B"),
        ("A", "B", "B", "B"),
        ("A AND B", "C AND B", "A AND D", "C AND D"),
        ("A AND B", "(A OR C) AND B", "A AND (B OR D)", "(A OR C) AND (B OR D)"),
        ("NOT (A AND B)", "NOT (C AND B)", "NOT (A AND D)", "NOT (C AND D)"),
    ],
)
def test_fast_forwards_identical_changes_and_disjoint_subtree_edits(base, left, right, expected):
    result = merge_revisions(parse(base), parse(left), parse(right))
    assert result.expression == parse(expected) and not result.conflicts
    assert result.changes
    swapped = merge_revisions(parse(base), parse(right), parse(left))
    assert swapped.expression == result.expression


@pytest.mark.parametrize(
    ("base", "left", "right"),
    [
        ("A", "B", "C"),
        ("A AND B", "A OR B", "A AND C"),
        ("A AND B", "B AND A", "B AND B"),
        ("A AND B", "(A AND B) AND C", "A AND C"),
        ("A", "A OR B", "A OR C"),
        ("NOT A", "A", "NOT B"),
    ],
)
def test_ambiguous_or_overlapping_changes_are_conflicts_not_silent_choices(base, left, right):
    base_node, left_node, right_node = parse(base), parse(left), parse(right)
    result = merge_revisions(base_node, left_node, right_node)
    assert result.expression is None and result.conflicts and not result.changes
    conflict = result.conflicts[0]
    assert conflict.path == () and (conflict.base, conflict.left, conflict.right) == (base_node, left_node, right_node)
    assert conflict.reason
    assert merge_revisions(base_node, right_node, left_node).expression is None


def test_all_conflicts_are_reported_without_a_partial_query():
    result = merge_revisions(parse("A AND B"), parse("C AND D"), parse("E AND F"))
    assert result.expression is None
    assert {item.path for item in result.conflicts} == {("left",), ("right",)}


def test_unchanged_revision_has_no_changes():
    base = parse("A AND B")
    result = merge_revisions(base, base, base)
    assert result.expression == base and not result.changes and not result.conflicts


def test_successful_merges_retain_both_sides_requested_occurrence_edits():

    leaves = [Term("A"), Term("B"), UnaryExpr(Op.NOT, Term("A"))]
    pool = leaves + [BinaryExpr(op, a, b) for op in (Op.AND, Op.OR) for a, b in product(leaves, repeat=2)]
    rng = Random(117)
    for _ in range(600):
        base, left, right = [rng.choice(pool) for _ in range(3)]
        result = merge_revisions(base, left, right)
        reverse = merge_revisions(base, right, left)
        assert reverse.expression == result.expression
        assert {c.path for c in reverse.conflicts} == {c.path for c in result.conflicts}
        if result.expression is None:
            continue
        for edit in structural_edits(base, left) + structural_edits(base, right):
            value = result.expression
            for name in edit.path:
                value = getattr(value, name)
            assert value == edit.after
