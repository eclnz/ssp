from dataclasses import replace
from itertools import product
from random import Random

import pytest

from string_parser import BinaryExpr, EditKind, Effect, Op, SolverLimits, Term, UnaryExpr, compare_revisions, parse


@pytest.mark.parametrize(
    ("old", "new", "effect"),
    [
        ("A", "A AND B", Effect.NARROWER),
        ("A", "A OR B", Effect.BROADER),
        ("A AND B", "A OR B", Effect.BROADER),
        ("A AND B", "A AND NOT B", Effect.MIXED),
        ("A", "B", Effect.MIXED),
        ("A OR B", "B OR A", Effect.EQUIVALENT),
        ("A OR (A AND B)", "A", Effect.EQUIVALENT),
        ("NOT (A OR B)", "NOT A AND NOT B", Effect.EQUIVALENT),
    ],
)
def test_effect_follows_boolean_context_not_term_counts(old, new, effect):
    assert compare_revisions(parse(old), parse(new)).effect is effect


@pytest.mark.parametrize(
    ("old", "new", "kind"),
    [
        ("A", "B", EditKind.TERM),
        ("A AND B", "A OR B", EditKind.OPERATOR),
        ("A", "NOT A", EditKind.ADD_NEGATION),
        ("NOT A", "A", EditKind.REMOVE_NEGATION),
        ("A", "A OR B", EditKind.ADD_BRANCH),
        ("A OR B", "A", EditKind.REMOVE_BRANCH),
        ("A OR B", "B OR A", EditKind.REARRANGE),
    ],
)
def test_edits_identify_the_changed_occurrence_and_kind(old, new, kind):
    result = compare_revisions(parse(old), parse(new))
    assert len(result.edits) == 1 and result.edits[0].kind is kind


def evaluate(expr, values):
    # Independent Boolean oracle; never uses production implication or comparison.
    match expr:
        case Term(value):
            return values[value]
        case UnaryExpr(_, operand):
            return not evaluate(operand, values)
        case BinaryExpr(Op.AND, left, right):
            return evaluate(left, values) and evaluate(right, values)
        case BinaryExpr(Op.OR, left, right):
            return evaluate(left, values) or evaluate(right, values)
    raise AssertionError(expr)


def apply_edit(expr, path, after):
    if not path:
        return after
    name, *rest = path
    return replace(expr, **{name: apply_edit(getattr(expr, name), rest, after)})


def test_comparison_and_edit_replay_match_an_independent_oracle():
    rng = Random(772)
    atoms = [Term("A"), Term("B"), Term("C")]

    def sample(depth):
        if not depth or rng.random() < 0.3:
            return rng.choice(atoms)
        if rng.random() < 0.25:
            return UnaryExpr(Op.NOT, sample(depth - 1))
        return BinaryExpr(rng.choice((Op.AND, Op.OR)), sample(depth - 1), sample(depth - 1))

    assignments = [dict(zip(("A", "B", "C"), bits)) for bits in product((False, True), repeat=3)]
    for _ in range(400):
        old, new = sample(3), sample(3)
        result = compare_revisions(old, new)
        added = any(evaluate(new, a) and not evaluate(old, a) for a in assignments)
        removed = any(evaluate(old, a) and not evaluate(new, a) for a in assignments)
        expected = {
            (False, False): Effect.EQUIVALENT,
            (True, False): Effect.BROADER,
            (False, True): Effect.NARROWER,
            (True, True): Effect.MIXED,
        }[added, removed]
        assert result.effect is expected
        for witness, was, now in ((result.added_witness, False, True), (result.removed_witness, True, False)):
            if witness is not None:
                assert evaluate(old, dict(witness)) is was and evaluate(new, dict(witness)) is now
        replayed = old
        for edit in result.edits:
            replayed = apply_edit(replayed, edit.path, edit.after)
        assert replayed == new


@pytest.mark.parametrize("limits", [dict(conflicts=0), dict(propagations=0), dict(conflicts=-1)])
def test_solver_limits_cannot_accidentally_disable_budgets(limits):
    with pytest.raises(ValueError):
        SolverLimits(**limits)


def test_relationship_assumptions_are_explicit_and_witnesses_obey_them():
    assumption = parse("NOT A OR B")
    result = compare_revisions(parse("A"), parse("B"), assumptions=assumption)
    assert result.effect is Effect.BROADER and result.assumptions == assumption
    assert result.added_witness is not None and evaluate(assumption, dict(result.added_witness))
    invalid = compare_revisions(parse("A"), parse("B"), assumptions=parse("A AND NOT A"))
    assert invalid.effect is Effect.UNKNOWN and invalid.reason


def test_identical_and_reordered_revisions_do_not_need_exhaustive_enumeration():
    result = compare_revisions(
        parse("A OR B OR C"), parse("C OR A OR B"), limits=SolverLimits(conflicts=1, propagations=1)
    )
    assert result.effect is Effect.EQUIVALENT and result.edits
