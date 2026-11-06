from string_parser import parse
from string_parser.analysis.terms import collect_terms
from string_parser.conventions.lexical import lexical_term_key


def test_core_inventory_preserves_independent_raw_symbols():
    expr = parse('COPD AND copd AND "COPD"')
    assert collect_terms(expr) == {"COPD", "copd", '"COPD"'}


def test_normalized_inventory_requires_explicit_key():
    expr = parse('COPD AND copd AND "COPD"')
    assert collect_terms(expr, key=lexical_term_key) == {"copd"}
