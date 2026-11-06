import re

import pytest

from string_parser import compare_expressions, parse
from string_parser.api import format_simplification_diff, suggest_simplification
from string_parser.presentation.diff import render_diff


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("(A OR B) AND C", "A AND C"),
        ("A AND C", "(A OR B) AND C"),
        ("A AND B", "A OR B"),
        ("NOT A", "NOT B"),
    ],
)
def test_rendering_preserves_the_diff_plan_with_optional_styling(before, after):
    plan = compare_expressions(parse(before), parse(after))
    assert plan is not None
    plain = render_diff(plan, color=False)
    colored = render_diff(plan)
    # Styling is allowed to change, but cannot change the represented query.
    assert tuple(re.sub(r"\x1b\[[0-9;]*m", "", text) for text in colored) == plain
    assert parse(plain[0]) == parse(before)
    assert parse(plain[1]) == parse(after)


def test_suggestion_and_diff_conveniences_have_no_lexical_assumptions():
    query = 'flow OR "high flow"'
    assert suggest_simplification(query) is None
    assert format_simplification_diff(query) is None
    suggestion = suggest_simplification("A OR (A AND B)")
    assert suggestion is not None and parse(suggestion) == parse("A")
