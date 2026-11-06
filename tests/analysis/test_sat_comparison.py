from itertools import product
from random import Random

import pytest

from string_parser import BinaryExpr, Effect, Op, SolverLimits, Term, UnaryExpr, compare_revisions, parse
from string_parser.analysis.satisfiability import SatCheck, SatSolver


def evaluate(expr, values):
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


def test_large_comparisons_have_no_fixed_symbol_ceiling_and_no_auxiliary_witness_symbols():
    query = " AND ".join(f"T{i}" for i in range(80))
    result = compare_revisions(parse(query), parse(f"({query}) AND EXTRA"))
    assert result.effect is Effect.NARROWER and result.removed_witness is not None
    assert set(dict(result.removed_witness)) == {f"T{i}" for i in range(80)} | {"EXTRA"}
    assert all(dict(result.removed_witness)[f"T{i}"] for i in range(80))
    assert not dict(result.removed_witness)["EXTRA"]


def test_large_equivalence_is_not_limited_to_canonical_reorderings():
    old = parse("NOT (" + " OR ".join(f"T{i}" for i in range(40)) + ")")
    new = parse(" AND ".join(f"NOT T{i}" for i in range(40)))
    assert compare_revisions(old, new).effect is Effect.EQUIVALENT


def test_real_solver_exhaustion_retains_edits_without_guessing_an_effect():
    result = compare_revisions(parse("A AND B"), parse("A OR B"), limits=SolverLimits(conflicts=1, propagations=1))
    assert result.effect is Effect.UNKNOWN and result.reason and result.edits


@pytest.mark.parametrize(
    "checks",
    [
        [SatCheck(None), SatCheck(False)],
        [SatCheck(False), SatCheck(None)],
        [SatCheck(None), SatCheck(None)],
        [SatCheck(True, (("A", False), ("B", True))), SatCheck(None)],
    ],
)
def test_unfinished_direction_checks_are_never_treated_as_unsat(monkeypatch, checks):
    outcomes = iter(checks)
    monkeypatch.setattr(SatSolver, "check", lambda self, assumptions: next(outcomes))
    result = compare_revisions(parse("A"), parse("B"))
    assert result.effect is Effect.UNKNOWN and result.reason
    assert result.added_witness == checks[0].witness
    assert result.removed_witness == checks[1].witness


def test_equivalence_requires_a_known_satisfiable_assumption_context(monkeypatch):
    outcomes = iter([SatCheck(False), SatCheck(False), SatCheck(None)])
    monkeypatch.setattr(SatSolver, "check", lambda self, assumptions: next(outcomes))
    result = compare_revisions(parse("A"), parse("B"), assumptions=parse("A AND B"))
    assert result.effect is Effect.UNKNOWN and result.reason


def test_sat_assumptions_match_an_independent_truth_table_oracle():
    atoms = [Term("A"), Term("B"), Term("C")]
    rng = Random(487)

    def sample(depth):
        if not depth or rng.random() < 0.3:
            return rng.choice(atoms)
        if rng.random() < 0.3:
            return UnaryExpr(Op.NOT, sample(depth - 1))
        return BinaryExpr(rng.choice((Op.AND, Op.OR)), sample(depth - 1), sample(depth - 1))

    assignments = [dict(zip(("A", "B", "C"), bits)) for bits in product((False, True), repeat=3)]
    for _ in range(200):
        old, new, context = sample(2), sample(2), sample(2)
        result = compare_revisions(old, new, assumptions=context)
        valid = [values for values in assignments if evaluate(context, values)]
        if not valid:
            assert result.effect is Effect.UNKNOWN
            continue
        added = any(evaluate(new, values) and not evaluate(old, values) for values in valid)
        removed = any(evaluate(old, values) and not evaluate(new, values) for values in valid)
        expected = {
            (False, False): Effect.EQUIVALENT,
            (True, False): Effect.BROADER,
            (False, True): Effect.NARROWER,
            (True, True): Effect.MIXED,
        }[added, removed]
        assert result.effect is expected
        for witness in (result.added_witness, result.removed_witness):
            if witness is not None:
                assert evaluate(context, dict(witness))
