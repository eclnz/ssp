import pytest

from string_parser import (
    EXACT,
    BinaryExpr,
    DuplicateTerm,
    Op,
    RedundantOperandDiagnostic,
    TermMatcher,
    analyze,
    parse,
    simplify,
)
from string_parser.analysis.redundancy import find_redundant_operands
from string_parser.conventions.lexical import LEXICAL_PHRASE
from string_parser.presentation.diagnostics import render_diagnostic
from string_parser.syntax.tree import flatten


class CasefoldMatcher:
    # No enum base, normalization key, or presentation metadata.
    def covers_term(self, broader: str, narrower: str) -> bool:
        return broader.casefold() == narrower.casefold()


@pytest.mark.parametrize("matcher", [EXACT, LEXICAL_PHRASE, CasefoldMatcher()])
def test_matcher_substitution_across_analysis_rewrite_and_rendering(matcher: TermMatcher):
    expr = parse("A AND (A OR B)")
    findings = analyze(expr, matcher=matcher, matching_label="test assumptions")
    removals = [item for item in findings if isinstance(item, RedundantOperandDiagnostic)]
    assert len(removals) == 1
    assert removals[0].retained == parse("A")
    assert simplify(expr, matcher=matcher) == removals[0].retained
    for item in findings:
        assert render_diagnostic(item)
    assert "test assumptions" in render_diagnostic(removals[0])


def test_custom_matching_changes_behavior_without_core_edits():
    expr = parse("COPD OR copd")
    assert simplify(expr) == expr
    assert simplify(expr, matcher=CasefoldMatcher()) == parse("COPD")
    assert any(isinstance(item, DuplicateTerm) and item.count == 2 for item in analyze(expr, matcher=CasefoldMatcher()))


def test_diagnostic_variants_validate_their_own_invariants():
    with pytest.raises(ValueError):
        DuplicateTerm("A", 1)
    with pytest.raises(ValueError):
        RedundantOperandDiagnostic(Op.NOT, parse("A"), parse("B"), False)
    with pytest.raises(TypeError):
        RedundantOperandDiagnostic(Op.AND)


@pytest.mark.parametrize(
    "query",
    [
        "(A AND B AND C) OR (A AND B) OR A",
        "A AND (A OR B) AND (A OR B OR C)",
    ],
)
def test_evidence_names_witnesses_that_survive_the_entire_group(query):
    expr = parse(query)
    assert isinstance(expr, BinaryExpr)
    findings = find_redundant_operands(expr)
    assert len(findings) == 2
    removed = {item.redundant_index for item in findings}
    assert all(item.retained_index not in removed for item in findings)
    survivors = [node for i, node in enumerate(flatten(expr, expr.op)) if i not in removed]
    assert survivors == [parse("A")]
    assert simplify(expr) == parse("A")
