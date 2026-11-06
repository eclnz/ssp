from string_parser import MatchPolicy, analyze, compare_expressions, compare_terms, parse
from string_parser.analysis.terms import conjunction_terms
from string_parser.presentation.diff import render_diff


def test_partial_conjunctions_cannot_masquerade_as_complete_branches():
    assert conjunction_terms(parse("A AND NOT B")) is None
    assert conjunction_terms(parse("A AND (B OR C)")) is None
    assert conjunction_terms(parse("A AND B")) == frozenset({"A", "B"})


def test_term_inventory_and_structural_changes_are_separate():
    for query in ("A OR B", "A AND NOT B"):
        before, after = parse("A AND B"), parse(query)
        assert compare_terms(before, after) == (set(), set())
        diff = compare_expressions(before, after)
        assert diff is not None
        assert all("\x1b" not in fragment.text for fragment in (*diff.before, *diff.after))
        a, b = render_diff(diff, color=False)
        assert parse(a) == before
        assert parse(b) == after


def test_diff_ignores_associativity_and_order_only():
    assert compare_expressions(parse("A OR (B OR C)"), parse("(C OR A) OR B")) is None
    assert compare_expressions(parse("A AND B"), parse("A OR B")) is not None


def test_exact_diagnostics_do_not_collapse_different_symbols():
    assert analyze(parse("A OR a")) == []
    assert analyze(parse('A OR "A"')) == []
    assert analyze(parse('flow OR "high flow"')) == []
    assert analyze(parse('flow OR "high flow"'), policy=MatchPolicy.LEXICAL_PHRASE)


def test_findings_retain_matching_policy():
    findings = analyze(parse('flow OR "high flow"'), policy=MatchPolicy.LEXICAL_PHRASE)
    assert findings and all(item.policy is MatchPolicy.LEXICAL_PHRASE for item in findings)
