"""Linear-size Boolean encoding and budgeted SAT checks through PySAT."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from pysat.solvers import Minisat22

from ..syntax.expressions import Expr, Op, Term, UnaryExpr

Assignment = tuple[tuple[str, bool], ...]


@dataclass(frozen=True)
class SolverLimits:
    """Positive per-check work budgets, not time or memory limits."""

    conflicts: int = 10_000
    propagations: int = 1_000_000

    def __post_init__(self) -> None:
        if self.conflicts < 1 or self.propagations < 1:
            raise ValueError("SAT solver budgets must be positive")


@dataclass(frozen=True)
class SatCheck:
    """True is SAT, False is UNSAT, None means the work limit was reached."""

    satisfiable: bool | None
    witness: Assignment | None = None


@dataclass
class _Encoding:
    symbols: dict[str, int] = field(default_factory=dict)
    clauses: list[list[int]] = field(default_factory=list)
    variables: int = 0

    def _fresh(self) -> int:
        self.variables += 1
        return self.variables

    def literal(self, expr: Expr) -> int:
        if isinstance(expr, Term):
            if expr.value not in self.symbols:
                self.symbols[expr.value] = self._fresh()
            return self.symbols[expr.value]
        if isinstance(expr, UnaryExpr):
            return -self.literal(expr.operand)
        left, right = self.literal(expr.left), self.literal(expr.right)
        result = self._fresh()
        # Define result iff (left op right), without distributing subexpressions.
        if expr.op is Op.AND:
            self.clauses.extend([[-result, left], [-result, right], [result, -left, -right]])
        else:
            self.clauses.extend([[result, -left], [result, -right], [-result, left, right]])
        return result


class SatSolver:
    """One shared encoding; each check temporarily asserts root literals."""

    def __init__(self, expressions: Sequence[Expr], limits: SolverLimits):
        self._encoding = _Encoding()
        self.roots = tuple(self._encoding.literal(expr) for expr in expressions)
        self._limits = limits
        self._solver = Minisat22(bootstrap_with=self._encoding.clauses)

    def __enter__(self) -> SatSolver:
        return self

    def __exit__(self, *_: object) -> None:
        self._solver.delete()

    def check(self, assumptions: Sequence[int]) -> SatCheck:
        # These budgets are relative to counters at the start of each check.
        self._solver.conf_budget(self._limits.conflicts)
        self._solver.prop_budget(self._limits.propagations)
        status: bool | None = self._solver.solve_limited(assumptions=list(dict.fromkeys(assumptions)))
        if status is not True:
            return SatCheck(status)
        model = self._solver.get_model()
        if model is None:
            raise RuntimeError("SAT backend returned SAT without a model")
        positive = {literal for literal in model if literal > 0}
        witness = tuple((name, variable in positive) for name, variable in sorted(self._encoding.symbols.items()))
        return SatCheck(True, witness)
