from string_parser.syntax.parser import parse
from string_parser.syntax.serialization import unparse
from string_parser.transformations.normalization import canonicalize


class TestCanonicalize:
    def test_or_branches_sorted(self) -> None:
        a = unparse(canonicalize(parse("COPD OR AECOPD")))
        b = unparse(canonicalize(parse("AECOPD OR COPD")))
        assert a == b

    def test_and_operands_sorted(self) -> None:
        a = unparse(canonicalize(parse("NIV AND COPD")))
        b = unparse(canonicalize(parse("COPD AND NIV")))
        assert a == b

    def test_nested_reorder(self) -> None:
        a = unparse(canonicalize(parse("(COPD OR AECOPD) AND (NIV OR BiPAP)")))
        b = unparse(canonicalize(parse("(AECOPD OR COPD) AND (BiPAP OR NIV)")))
        assert a == b

    def test_genuinely_different_strings_differ(self) -> None:
        a = unparse(canonicalize(parse("COPD AND NIV")))
        b = unparse(canonicalize(parse("COPD AND BiPAP")))
        assert a != b

    def test_deeply_nested_or_within_and(self) -> None:
        a = unparse(canonicalize(parse("(A OR B) AND (C OR D)")))
        b = unparse(canonicalize(parse("(B OR A) AND (D OR C)")))
        assert a == b

    def test_deeply_nested_and_within_or(self) -> None:
        a = unparse(canonicalize(parse("(A AND B) OR (C AND D)")))
        b = unparse(canonicalize(parse("(B AND A) OR (D AND C)")))
        assert a == b

    def test_three_levels_deep(self) -> None:
        a = unparse(canonicalize(parse("((COPD OR AECOPD) AND NIV) OR (BiPAP AND (ILD OR IPF))")))
        b = unparse(canonicalize(parse("(BiPAP AND (IPF OR ILD)) OR (NIV AND (AECOPD OR COPD))")))
        assert a == b

    def test_or_branch_order_independent_of_complexity(self) -> None:
        a = unparse(canonicalize(parse("(COPD AND NIV AND oxygen) OR (ILD AND BiPAP)")))
        b = unparse(canonicalize(parse("(ILD AND BiPAP) OR (oxygen AND COPD AND NIV)")))
        assert a == b

    def test_not_nodes_preserved(self) -> None:
        a = unparse(canonicalize(parse("(COPD OR AECOPD) AND NOT asthma")))
        b = unparse(canonicalize(parse("(AECOPD OR COPD) AND NOT asthma")))
        assert a == b

    def test_mixed_depth_reorder(self) -> None:
        a = unparse(canonicalize(parse("(A AND (B OR C)) OR (D AND (E OR F))")))
        b = unparse(canonicalize(parse("(D AND (F OR E)) OR (A AND (C OR B))")))
        assert a == b
