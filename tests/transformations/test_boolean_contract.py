from itertools import product
from random import Random

from string_parser import BinaryExpr, Op, Term, UnaryExpr, canonicalize, parse, simplify, unparse


def evaluate(expr, values):
    if isinstance(expr, Term):
        return values[expr.value]
    if isinstance(expr, UnaryExpr):
        return not evaluate(expr.operand, values)
    if expr.op is Op.AND:
        return evaluate(expr.left, values) and evaluate(expr.right, values)
    return evaluate(expr.left, values) or evaluate(expr.right, values)


def test_transforms_and_serialization_preserve_boolean_meaning():
    atoms = [Term(name) for name in ("A", "B", "C")]
    leaves = atoms + [UnaryExpr(Op.NOT, atom) for atom in atoms]
    branches = [BinaryExpr(op, a, b) for op in (Op.AND, Op.OR) for a, b in product(leaves, repeat=2)]
    expressions = leaves + branches + [UnaryExpr(Op.NOT, branch) for branch in branches]
    expressions += [
        BinaryExpr(op, a, b)
        for op in (Op.AND, Op.OR)
        for branch, leaf in product(branches, leaves)
        for a, b in ((branch, leaf), (leaf, branch))
    ]
    rng = Random(6831)

    def sample(depth):
        if depth == 0 or rng.random() < 0.2:
            return rng.choice(atoms)
        if rng.random() < 0.3:
            return UnaryExpr(Op.NOT, sample(depth - 1))
        return BinaryExpr(rng.choice((Op.AND, Op.OR)), sample(depth - 1), sample(depth - 1))

    expressions += [sample(4) for _ in range(512)]
    assignments = [dict(zip(("A", "B", "C"), bits)) for bits in product((False, True), repeat=3)]
    for expr in expressions:
        results = (simplify(expr), canonicalize(expr), parse(unparse(expr)))
        for values in assignments:
            expected = evaluate(expr, values)
            for result in results:
                assert evaluate(result, values) == expected, (expr, result, values)


def test_rewriting_has_a_stable_result_without_specifying_its_shape():
    expr = parse("(A AND (A OR B)) OR (A AND NOT C)")
    assert simplify(simplify(expr)) == simplify(expr)
    assert canonicalize(canonicalize(expr)) == canonicalize(expr)


def test_exact_symbols_retain_case_and_quoting():
    for query in ("A OR a", 'A OR "A"'):
        expr = parse(query)
        assert simplify(expr) == expr
