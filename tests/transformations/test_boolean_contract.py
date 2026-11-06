from itertools import product

from string_parser import BinaryExpr, MatchPolicy, Op, Term, UnaryExpr, parse, simplify, unparse


def evaluate(expr, values):
    if isinstance(expr, Term):
        return values[expr.value]
    if isinstance(expr, UnaryExpr):
        return not evaluate(expr.operand, values)
    if expr.op is Op.AND:
        return evaluate(expr.left, values) and evaluate(expr.right, values)
    return evaluate(expr.left, values) or evaluate(expr.right, values)


def test_exact_rewrites_preserve_truth_tables_and_are_idempotent():
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
    assignments = [dict(zip(("A", "B", "C"), bits)) for bits in product((False, True), repeat=3)]
    for expr in expressions:
        result = simplify(expr)
        assert simplify(result) == result
        for values in assignments:
            assert evaluate(expr, values) == evaluate(result, values), (expr, result, values)


def test_phrase_matching_requires_explicit_opt_in():
    expr = parse('flow OR "high flow"')
    assert simplify(expr) == expr
    assert unparse(simplify(expr, policy=MatchPolicy.LEXICAL_PHRASE)) == "flow"


def test_field_tags_and_wildcards_do_not_use_phrase_heuristics():
    for query in ('flow[ti] OR "high flow"[ti]', 'flow* OR "high flow"'):
        expr = parse(query)
        assert simplify(expr, policy=MatchPolicy.LEXICAL_PHRASE) == expr


def test_exact_symbols_retain_case_and_quoting():
    for query in ("A OR a", 'A OR "A"'):
        expr = parse(query)
        assert simplify(expr) == expr
