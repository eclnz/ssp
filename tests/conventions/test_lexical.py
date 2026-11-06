from string_parser import parse, simplify, unparse
from string_parser.conventions.lexical import LEXICAL_PHRASE


def test_phrase_matching_requires_explicit_opt_in():
    expr = parse('flow OR "high flow"')
    assert simplify(expr) == expr
    assert unparse(simplify(expr, matcher=LEXICAL_PHRASE)) == "flow"


def test_field_tags_and_wildcards_do_not_use_phrase_heuristics():
    for query in ('flow[ti] OR "high flow"[ti]', 'flow* OR "high flow"'):
        expr = parse(query)
        assert simplify(expr, matcher=LEXICAL_PHRASE) == expr


def test_optional_matcher_obeys_reflexive_and_transitive_coverage():
    terms = ["A", "a", '"A"', "flow", '"high flow"', '"high flow therapy"', '""', "A[ti]", "flow*"]
    for a in terms:
        assert LEXICAL_PHRASE.covers_term(a, a)
        for b in terms:
            for c in terms:
                if LEXICAL_PHRASE.covers_term(a, b) and LEXICAL_PHRASE.covers_term(b, c):
                    assert LEXICAL_PHRASE.covers_term(a, c)
