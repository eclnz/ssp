from __future__ import annotations

import difflib
import re
import warnings
from collections import Counter
from dataclasses import dataclass
from enum import Enum, StrEnum

# ---------------------------------------------------------------------------
# Expression types
# ---------------------------------------------------------------------------


class Op(Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


@dataclass
class Term:
    value: str  # a search term or quoted phrase e.g. "high flow"


@dataclass
class BinaryExpr:
    op: Op  # AND or OR
    left: Expr
    right: Expr


@dataclass
class UnaryExpr:
    op: Op  # NOT
    operand: Expr


Expr = Term | BinaryExpr | UnaryExpr


class ImplicitAndWarning(UserWarning):
    """Raised when adjacent terms are implicitly AND-ed (no operator between them)."""


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

# Quoted phrases first, then operators, then parens, then any non-whitespace non-paren token.
_TOKEN = re.compile(r'"[^"]*"|\b(?:AND|OR|NOT)\b|[()]|[^\s()]+')


class _Paren(Enum):
    OPEN = "("
    CLOSE = ")"


_Token = Term | Op | _Paren


def _tokenize(string: str) -> list[_Token]:
    tokens: list[_Token] = []
    for m in _TOKEN.findall(string):
        if m == "AND":
            tokens.append(Op.AND)
        elif m == "OR":
            tokens.append(Op.OR)
        elif m == "NOT":
            tokens.append(Op.NOT)
        elif m == "(":
            tokens.append(_Paren.OPEN)
        elif m == ")":
            tokens.append(_Paren.CLOSE)
        else:
            tokens.append(Term(m))
    return tokens


# ---------------------------------------------------------------------------
# Recursive-descent parser — precedence: NOT > AND > OR
# ---------------------------------------------------------------------------


def _parse(tokens: list[_Token]) -> Expr:
    pos = 0

    def peek() -> _Token | None:
        return tokens[pos] if pos < len(tokens) else None

    def consume() -> _Token:
        nonlocal pos
        t = tokens[pos]
        pos += 1
        return t

    def parse_or() -> Expr:
        left = parse_and()
        while peek() is Op.OR:
            consume()
            left = BinaryExpr(Op.OR, left, parse_and())
        return left

    def parse_and() -> Expr:
        left = parse_not()
        while True:
            if peek() is Op.AND:
                consume()
            elif isinstance(peek(), Term) or peek() in (_Paren.OPEN, Op.NOT):
                warnings.warn(
                    "Adjacent terms without operator — treating as AND (PubMed behaviour)",
                    ImplicitAndWarning,
                    stacklevel=3,
                )
            else:
                break
            left = BinaryExpr(Op.AND, left, parse_not())
        return left

    def parse_not() -> Expr:
        if peek() is Op.NOT:
            consume()
            return UnaryExpr(Op.NOT, parse_not())
        return parse_atom()

    def parse_atom() -> Expr:
        t = peek()
        if t is _Paren.OPEN:
            consume()
            expr = parse_or()
            if peek() is _Paren.CLOSE:
                consume()
            return expr
        t = consume()
        if isinstance(t, Term):
            return t
        raise ValueError(f"Unexpected token in expression: {t!r}")

    return parse_or()


def parse(string: str) -> Expr:
    return _parse(_tokenize(string))


def collect_terms(expr: Expr) -> set[str]:
    """Return the set of all leaf terms in an expression, lowercased for comparison."""
    if isinstance(expr, Term):
        return {expr.value.lower().strip('"')}
    elif isinstance(expr, UnaryExpr):
        return collect_terms(expr.operand)
    else:
        return collect_terms(expr.left) | collect_terms(expr.right)


def classify_change(old: str, new: str) -> tuple[set[str], set[str]]:
    """Return (added_terms, removed_terms) between two search strings."""
    old_terms = collect_terms(parse(old))
    new_terms = collect_terms(parse(new))
    return new_terms - old_terms, old_terms - new_terms


def _phrase_words(term: str) -> list[str]:
    return term.lower().strip('"').split()


def _is_subphrase(broader: str, narrower: str) -> bool:
    """True if broader's words appear as a contiguous run inside narrower's words.

    In OR context broader already captures every hit narrower would — narrower is redundant.
    """
    bw = _phrase_words(broader)
    nw = _phrase_words(narrower)
    n = len(bw)
    if n >= len(nw):
        return False
    return any(nw[i : i + n] == bw for i in range(len(nw) - n + 1))


def _collect_and_terms(expr: Expr) -> set[str]:
    """Terms reachable through AND-only paths; stops (returns empty) at OR/NOT nodes."""
    if isinstance(expr, Term):
        return {expr.value.lower().strip('"')}
    if isinstance(expr, BinaryExpr) and expr.op == Op.AND:
        return _collect_and_terms(expr.left) | _collect_and_terms(expr.right)
    return set()


def _collect_or_branches(expr: Expr) -> list[Expr]:
    """Flatten consecutive OR nodes into a flat list of branches."""
    if isinstance(expr, BinaryExpr) and expr.op == Op.OR:
        return _collect_or_branches(expr.left) + _collect_or_branches(expr.right)
    return [expr]


def find_and_redundancies(expr: Expr) -> list[tuple[str, str]]:
    """Return (redundant_broader, necessary_narrower) pairs within AND context.

    In 'flow AND "high flow"', 'flow' is always satisfied when 'high flow' is — it adds no constraint.
    """
    results: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def walk(e: Expr) -> None:
        if isinstance(e, BinaryExpr):
            if e.op == Op.AND:
                for lt in _collect_and_terms(e.left):
                    for rt in _collect_and_terms(e.right):
                        pair = (lt, rt) if _is_subphrase(lt, rt) else (rt, lt) if _is_subphrase(rt, lt) else None
                        if pair and pair not in seen:
                            seen.add(pair)
                            results.append(pair)
            walk(e.left)
            walk(e.right)
        elif isinstance(e, UnaryExpr):
            walk(e.operand)

    walk(expr)
    return results


def find_absorbed_branches(expr: Expr) -> list[tuple[str, set[str]]]:
    """Return (absorbing_term, absorbed_and_terms) where 'T OR (A AND B)' simplifies to T.

    T absorbs an AND branch when T is a subphrase of (or equal to) at least one term in that branch —
    meaning every document matching the AND also matches T.
    """
    results: list[tuple[str, set[str]]] = []
    seen: set[tuple[str, frozenset[str]]] = set()

    def walk(e: Expr) -> None:
        if isinstance(e, BinaryExpr):
            if e.op == Op.OR:
                branches = _collect_or_branches(e)
                or_terms = [b.value.lower().strip('"') for b in branches if isinstance(b, Term)]
                and_branches = [_collect_and_terms(b) for b in branches if isinstance(b, BinaryExpr) and b.op == Op.AND]
                for t in or_terms:
                    for and_terms in and_branches:
                        if and_terms and any(t == at or _is_subphrase(t, at) for at in and_terms):
                            key = (t, frozenset(and_terms))
                            if key not in seen:
                                seen.add(key)
                                results.append((t, and_terms))
            walk(e.left)
            walk(e.right)
        elif isinstance(e, UnaryExpr):
            walk(e.operand)

    walk(expr)
    return results


def combine(*exprs: Expr) -> Expr:
    """OR together multiple expressions — use when analysing a set of search strings jointly."""
    if not exprs:
        raise ValueError("At least one expression required")
    result = exprs[0]
    for e in exprs[1:]:
        result = BinaryExpr(Op.OR, result, e)
    return result


def find_duplicate_terms(expr: Expr) -> list[str]:
    """Return terms that appear more than once anywhere in the expression tree.

    collect_terms deduplicates, so (A OR B) OR (A OR C) hides the duplicate A.
    """
    all_terms: list[str] = []

    def walk(e: Expr) -> None:
        if isinstance(e, Term):
            all_terms.append(e.value.lower().strip('"'))
        elif isinstance(e, BinaryExpr):
            walk(e.left)
            walk(e.right)
        elif isinstance(e, UnaryExpr):
            walk(e.operand)

    walk(expr)
    return [t for t, n in Counter(all_terms).items() if n > 1]


def _branch_subsumes(e1: set[str], e2: set[str]) -> bool:
    """True if every document matching e2 (AND of e2 terms) also matches e1 (AND of e1 terms).

    This holds when every term in e1 has a broader-or-equal counterpart in e2.
    """
    if e1 == e2:
        return False
    return all(any(t1 == t2 or _is_subphrase(t1, t2) for t2 in e2) for t1 in e1)


def find_subsumed_branches(expr: Expr) -> list[tuple[set[str], set[str]]]:
    """Return (subsuming_terms, subsumed_terms) OR-branch pairs.

    The subsumed branch adds no coverage: every document it matches is already matched
    by the subsuming branch.  Works across single terms and AND-of-terms branches alike.

    E.g. (flow AND COPD) OR ("high flow" AND COPD) → ({'flow','copd'}, {'high flow','copd'})
    """
    results: list[tuple[set[str], set[str]]] = []
    seen: set[tuple[frozenset[str], frozenset[str]]] = set()

    def walk(e: Expr) -> None:
        if isinstance(e, BinaryExpr):
            if e.op == Op.OR:
                branch_terms = [_collect_and_terms(b) for b in _collect_or_branches(e)]
                pure = [t for t in branch_terms if t]
                for i, t1 in enumerate(pure):
                    for j, t2 in enumerate(pure):
                        if i != j and _branch_subsumes(t1, t2):
                            key = (frozenset(t1), frozenset(t2))
                            if key not in seen:
                                seen.add(key)
                                results.append((t1, t2))
            walk(e.left)
            walk(e.right)
        elif isinstance(e, UnaryExpr):
            walk(e.operand)

    walk(expr)
    return results


def find_subsumed_terms(terms: set[str]) -> list[tuple[str, str]]:
    """Return (broader, narrower) pairs where broader subsumes narrower in OR context.

    E.g. 'high flow' subsumes 'high flow therapy': any match for the latter also
    satisfies the former, so the narrower term adds no coverage.
    """
    term_list = sorted(terms)
    pairs: list[tuple[str, str]] = []
    for i, a in enumerate(term_list):
        for b in term_list[i + 1 :]:
            if _is_subphrase(a, b):
                pairs.append((a, b))
            elif _is_subphrase(b, a):
                pairs.append((b, a))
    return pairs


# ---------------------------------------------------------------------------
# Simplification and linting
# ---------------------------------------------------------------------------


def _collect_and_exprs(expr: Expr) -> list[Expr]:
    """Flatten consecutive AND nodes into a list of operands."""
    if isinstance(expr, BinaryExpr) and expr.op == Op.AND:
        return _collect_and_exprs(expr.left) + _collect_and_exprs(expr.right)
    return [expr]


def _rebuild_binary(op: Op, exprs: list[Expr]) -> Expr:
    result = exprs[0]
    for e in exprs[1:]:
        result = BinaryExpr(op, result, e)
    return result


def unparse(expr: Expr) -> str:
    """Reconstruct a PubMed search string from an expression tree."""
    if isinstance(expr, Term):
        return expr.value  # preserves original quoting
    if isinstance(expr, UnaryExpr):
        return f"NOT {unparse(expr.operand)}"
    return f"({unparse(expr.left)} {expr.op.value} {unparse(expr.right)})"


def canonical_form(string: str) -> str:
    """Parse, canonicalize, and re-unparse a query — its order-independent normal form."""
    return unparse(canonicalize(parse(string)))


def canonically_equal(a: str, b: str) -> bool:
    """True if two query strings normalise to the same canonical form."""
    return canonical_form(a) == canonical_form(b)


def canonicalize(expr: Expr) -> Expr:
    """Return an equivalent expression with OR and AND branches sorted deterministically.

    Two expressions that differ only in operand order will produce identical output
    after canonicalization, enabling reliable equality checks.
    """
    if isinstance(expr, Term):
        return expr
    if isinstance(expr, UnaryExpr):
        return UnaryExpr(expr.op, canonicalize(expr.operand))
    if expr.op == Op.OR:
        branches = sorted([canonicalize(b) for b in _collect_or_branches(expr)], key=unparse)
        return _rebuild_binary(Op.OR, branches)
    if expr.op == Op.AND:
        operands = sorted([canonicalize(e) for e in _collect_and_exprs(expr)], key=unparse)
        return _rebuild_binary(Op.AND, operands)
    return expr


def simplify(expr: Expr) -> Expr:
    """Return a new expression with redundancies removed.

    - OR: removes branches subsumed by a sibling (including duplicate branches).
    - AND: removes broader terms made redundant by a narrower sibling term.
    """
    if isinstance(expr, UnaryExpr):
        return UnaryExpr(expr.op, simplify(expr.operand))

    if not isinstance(expr, BinaryExpr):
        return expr

    if expr.op == Op.OR:
        branches = [simplify(b) for b in _collect_or_branches(expr)]
        branch_terms = [_collect_and_terms(b) for b in branches]
        seen: set[frozenset[str]] = set()
        keep: list[Expr] = []
        for i, (b, t) in enumerate(zip(branches, branch_terms)):
            key = frozenset(t)
            if key in seen:
                continue
            if t and any(j != i and bt and _branch_subsumes(bt, t) for j, bt in enumerate(branch_terms)):
                continue
            if key:
                seen.add(key)
            keep.append(b)
        return _rebuild_binary(Op.OR, keep or branches)

    if expr.op == Op.AND:
        and_exprs = [simplify(e) for e in _collect_and_exprs(expr)]
        normed = [e.value.lower().strip('"') if isinstance(e, Term) else None for e in and_exprs]
        keep_and = [
            e
            for i, e in enumerate(and_exprs)
            if (n_i := normed[i]) is None
            or not any(
                j != i and (n_j := normed[j]) is not None and _is_subphrase(n_i, n_j) for j in range(len(and_exprs))
            )
        ]
        return _rebuild_binary(Op.AND, keep_and or and_exprs)

    return expr


def lint_string(string: str) -> list[str]:
    """Return human-readable warnings about redundancies in a search string."""
    expr = parse(string)
    issues: list[str] = []

    for term in find_duplicate_terms(expr):
        issues.append(f"Duplicate term: {term!r} appears more than once")

    for broader, narrower in find_and_redundancies(expr):
        issues.append(
            f"AND redundancy: {broader!r} is always satisfied when {narrower!r} matches — {broader!r} can be removed"
        )

    for subsuming, subsumed in find_subsumed_branches(expr):
        issues.append(
            f"OR redundancy: ({' AND '.join(sorted(subsumed))}) is fully captured by "
            f"({' AND '.join(sorted(subsuming))}) — the narrower branch adds no coverage"
        )

    return issues


def suggest_simplification(string: str) -> str | None:
    """Return a simplified string if redundancies were found, else None."""
    expr = parse(string)
    simplified = unparse(simplify(expr))
    original = unparse(expr)
    return simplified if simplified != original else None


class Colour(StrEnum):
    RED = "\033[31m"
    GREEN = "\033[32m"
    RESET = "\033[0m"


def _colour_branches(expr: Expr, highlight: set[frozenset[str]], colour: Colour) -> str:
    branches = _collect_or_branches(expr)
    result = ""
    for i, b in enumerate(branches):
        t = frozenset(_collect_and_terms(b))
        s = unparse(b)
        sep = " OR " if i > 0 else ""
        if t and t in highlight:
            result += f"{colour}{sep}{s}{Colour.RESET}"
        else:
            result += f"{sep}{s}"
    return result


def format_simplification_diff(string: str) -> str | None:
    """Original string with removed OR branches in red, or None if no change."""
    orig_expr = parse(string)
    simp_expr = simplify(orig_expr)
    if unparse(simp_expr) == unparse(orig_expr):
        return None
    simp_terms = {frozenset(_collect_and_terms(b)) for b in _collect_or_branches(simp_expr)}
    orig_terms = {frozenset(_collect_and_terms(b)) for b in _collect_or_branches(orig_expr)}
    removed = orig_terms - simp_terms
    return _colour_branches(orig_expr, removed, Colour.RED)


def _coloured_join(parts: list[str], sep: str) -> str:
    """Join parts with sep, pulling the separator into the colour span of each coloured part."""
    result = ""
    for i, part in enumerate(parts):
        if i == 0:
            result += part
        elif part.startswith("\033["):
            code = part[:5]  # \033[31m or \033[32m
            result += f"{code}{sep}{Colour.RESET}{part}"
        else:
            result += sep + part
    return result


def _tree_aware_diff(old: Expr, new: Expr) -> tuple[str, str]:
    """Recursively diff two expression trees, returning (coloured_was, coloured_now).

    Flattens same-op nodes into branch lists, aligns them with a sequence diff,
    then recurses into single-branch replacements — so shared subtrees stay plain
    and only the genuinely new/removed parts are coloured.
    """
    old_s, new_s = unparse(old), unparse(new)
    if old_s == new_s:
        return old_s, new_s

    # Infer op for branch-level diffing: works when both sides share an op, or when
    # one side collapses to a single term (e.g. (COPD OR AECOPD) → COPD).
    op: Op | None = None
    if isinstance(old, BinaryExpr) and isinstance(new, BinaryExpr) and old.op == new.op:
        op = old.op
    elif isinstance(old, BinaryExpr) and not isinstance(new, BinaryExpr):
        op = old.op
    elif isinstance(new, BinaryExpr) and not isinstance(old, BinaryExpr):
        op = new.op

    if op is not None:
        old_branches = _collect_or_branches(old) if op == Op.OR else _collect_and_exprs(old)
        new_branches = _collect_or_branches(new) if op == Op.OR else _collect_and_exprs(new)
        old_keys = [unparse(b) for b in old_branches]
        new_keys = [unparse(b) for b in new_branches]
        sep = f" {op.value} "
        was_parts: list[str] = []
        now_parts: list[str] = []

        for code, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old_keys, new_keys, autojunk=False).get_opcodes():
            if code == "equal":
                was_parts.extend(old_keys[i1:i2])
                now_parts.extend(new_keys[j1:j2])
            elif code == "delete":
                was_parts.extend(f"{Colour.RED}{k}{Colour.RESET}" for k in old_keys[i1:i2])
            elif code == "insert":
                now_parts.extend(f"{Colour.GREEN}{k}{Colour.RESET}" for k in new_keys[j1:j2])
            elif code == "replace":
                if i2 - i1 == 1 and j2 - j1 == 1:
                    w, n = _tree_aware_diff(old_branches[i1], new_branches[j1])
                    was_parts.append(w)
                    now_parts.append(n)
                else:
                    was_parts.extend(f"{Colour.RED}{k}{Colour.RESET}" for k in old_keys[i1:i2])
                    now_parts.extend(f"{Colour.GREEN}{k}{Colour.RESET}" for k in new_keys[j1:j2])

        was_joined = _coloured_join(was_parts, sep)
        now_joined = _coloured_join(now_parts, sep)
        return (
            f"({was_joined})" if len(old_branches) > 1 else was_joined,
            f"({now_joined})" if len(new_branches) > 1 else now_joined,
        )

    return f"{Colour.RED}{old_s}{Colour.RESET}", f"{Colour.GREEN}{new_s}{Colour.RESET}"


def format_string_diff(old: str, new: str) -> tuple[str, str] | None:
    """Return (coloured_was, coloured_now) with removals in red and additions in green.

    Uses tree-aware diffing so shared subtrees stay plain — only genuinely
    new or removed branches are highlighted.  Returns None if unchanged.
    """
    old_expr, new_expr = parse(old), parse(new)
    if unparse(canonicalize(old_expr)) == unparse(canonicalize(new_expr)):
        return None
    return _tree_aware_diff(old_expr, new_expr)


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------


def _collect_same_op(expr: BinaryExpr) -> list[Expr]:
    """Flatten left-associative same-operator nesting into a single operand list."""
    result: list[Expr] = []

    def collect(e: Expr) -> None:
        if isinstance(e, BinaryExpr) and e.op == expr.op:
            collect(e.left)
            collect(e.right)
        else:
            result.append(e)

    collect(expr.left)
    collect(expr.right)
    return result


def _fmt_expr(expr: Expr, indent: str = "", last: bool = True, combine: bool = False) -> None:
    connector = "└── " if last else "├── "
    next_indent = indent + ("    " if last else "│   ")

    if isinstance(expr, Term):
        print(f"{indent}{connector}Term({expr.value!r})")
    elif isinstance(expr, UnaryExpr):
        print(f"{indent}{connector}{expr.op.value}")
        _fmt_expr(expr.operand, next_indent, last=True, combine=combine)
    elif isinstance(expr, BinaryExpr):
        print(f"{indent}{connector}{expr.op.value}")
        if combine:
            children = _collect_same_op(expr)
            for i, child in enumerate(children):
                _fmt_expr(child, next_indent, last=i == len(children) - 1, combine=combine)
        else:
            _fmt_expr(expr.left, next_indent, last=False, combine=combine)
            _fmt_expr(expr.right, next_indent, last=True, combine=combine)


def print_expr(expr: Expr, combine: bool = False) -> None:
    _fmt_expr(expr, combine=combine)
