from string_parser import compare_terms, parse
from string_parser.conventions.lexical import lexical_term_key


def test_compare_terms_does_not_silently_change_identity():
    changes = compare_terms(parse("A AND B"), parse("a AND B"))
    assert changes.added == {"a"} and changes.removed == {"A"}
    assert compare_terms(parse("A AND B"), parse("a AND B"), key=lexical_term_key) == (set(), set())


def test_inventory_is_not_a_meaning_comparison():
    before = parse("A AND B")
    for after in (parse("A OR B"), parse("A AND NOT B")):
        assert compare_terms(before, after) == (set(), set())
