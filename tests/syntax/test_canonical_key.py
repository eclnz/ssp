from string_parser import canonical_key, parse


def test_keys_support_associative_commutative_equality_and_hashing():
    first = canonical_key(parse("A OR (B OR C)"))
    second = canonical_key(parse("(C OR A) OR B"))
    assert first == second
    assert len({first, second}) == 1
    assert {first: "revision"}[second] == "revision"


def test_keys_preserve_raw_terms_operators_and_nontrivial_boolean_structure():
    expressions = ["A", "a", '"A"', "NOT A", "A AND B", "A OR B", "A AND A"]
    assert len({canonical_key(parse(text)) for text in expressions}) == len(expressions)


def test_keys_support_consistent_ordering_without_prescribing_representation():
    keys = [canonical_key(parse(text)) for text in ["A", "NOT A", "B AND C", "A OR B"]]
    ordered = sorted(keys)
    assert sorted(reversed(keys)) == ordered
    assert all(sorted((b, a)) == [a, b] for a, b in zip(ordered, ordered[1:]))


def test_key_equality_does_not_become_full_logical_equivalence():
    assert canonical_key(parse("A OR (A AND B)")) != canonical_key(parse("A"))
    assert canonical_key(parse("A AND (B AND C)")) == canonical_key(parse("(C AND A) AND B"))
