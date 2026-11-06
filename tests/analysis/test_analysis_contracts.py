from string_parser import RedundantOperandDiagnostic, analyze, compare_expressions, compare_terms, parse
from string_parser.conventions.lexical import LEXICAL_PHRASE
from string_parser.presentation import render_diff


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
    assert analyze(parse('flow OR "high flow"'), matcher=LEXICAL_PHRASE)


def test_findings_retain_matching_label_without_owning_the_matcher():
    findings = analyze(parse('flow OR "high flow"'), matcher=LEXICAL_PHRASE, matching_label="lexical_phrase")
    removals = [item for item in findings if isinstance(item, RedundantOperandDiagnostic)]
    assert removals and all(item.matching_label == "lexical_phrase" for item in removals)
