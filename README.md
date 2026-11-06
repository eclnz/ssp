# ssp

Search-string comparison and merge primitives for building version-control tools. Python 3.11+, using Lark for parsing and PySAT/MiniSat for Boolean reasoning. SSP does not store revisions or manage repositories.

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
uv build
```

## Compare revisions

```python
from string_parser import Effect, compare_revisions, parse

change = compare_revisions(parse("A AND B"), parse("A OR B"))
assert change.effect is Effect.BROADER
assert not change.terms.added and not change.terms.removed
assert change.edits[0].path == ("op",)
assert dict(change.added_witness)  # a hypothetical term-match assignment explaining the expansion
```

`RevisionComparison` contains the before/after trees, structured edits, raw inventory changes, Boolean effect, optional added/removed witnesses, assumptions, and an explanation when the effect is unknown. Paths use `left`, `right`, `operand`, or `op` to address the supplied before tree. Whole-subtree edits stop at their replacement boundary and can be replayed without guessing term identity.

Edits distinguish term replacement, operator changes, adding/removing negation or a branch, operand rearrangement/reassociation, and other subtree replacements. Reorderings stay visible even when their Boolean effect is equivalent. `compare_expressions` provides an optional reconstructed-text diff; its `ignore_operand_order` option is false by default. `presentation.render_diff` renders that plan with optional ANSI styling.

## Boolean effect and limits

- `EQUIVALENT`: no assignments gain or lose a match.
- `BROADER`: some assignments gain a match and none lose one.
- `NARROWER`: some lose a match and none gain one.
- `MIXED`: there are both gains and losses.
- `UNKNOWN`: the budget was exceeded or assumptions admit no assignments.

Terms are independent raw Boolean symbols, not database-resolved searches. A witness describes hypothetical term matches, not a retrieved record or an observed result-count change.

Effect classification uses SAT checks for `after AND NOT before` (gains) and `before AND NOT after` (losses). A linear-size encoding preserves the Boolean structure; production never enumerates truth tables. If both directions are unsatisfiable under supplied assumptions, the assumption context must also be proven satisfiable before reporting equivalence.

There is no fixed term-count ceiling. Default per-check limits are 10,000 conflicts and 1,000,000 propagations; configure them explicitly:

```python
from string_parser import SolverLimits
change = compare_revisions(parse("A AND B"), parse("A OR B"),
                           limits=SolverLimits(conflicts=50_000, propagations=2_000_000))
```

An unfinished check returns `UNKNOWN`, retaining any witnesses already established. Inconsistent assumptions also return `UNKNOWN`. These are solver-work limits, not wall-clock or memory limits: encoding and solver initialization happen before limited solving, and hard problems can still be expensive. Budgets are positive to avoid accidentally disabling PySAT's limits. The old `max_assignments` parameter has been removed.

Relationships between terms can be supplied explicitly as an assumption expression:

```python
change = compare_revisions(parse("A"), parse("B"), assumptions=parse("NOT A OR B"))
assert change.effect is Effect.BROADER  # assuming A implies B
```

## Three-way merge

```python
from string_parser import merge_revisions

result = merge_revisions(parse("A AND B"), parse("C AND B"), parse("A AND D"))
assert result.expression == parse("C AND D")
assert not result.conflicts
```

The merge supports unchanged sides, identical edits, and independent edits to distinct subtrees with stable layout. Accepted base-to-result edits are returned in `changes`. It does not simplify or normalize a side before merging.

Competing edits at one occurrence, ancestor replacement versus descendant edits, operator changes alongside concurrent child edits, and ambiguous reorderings return contextual `MergeConflict` values. Conflicts include the path, base/left/right expressions, and reason. A conflicting merge returns `expression=None` and no accepted changes, never a partial executable query. The policy is deliberately conservative: some reconcilable changes still need caller review. There is no automatic union of two competing branch additions.

## Core and optional conventions

A small Lark LALR grammar parses uppercase AND/OR/NOT with precedence NOT > AND > OR, balanced parentheses, and opaque quoted/unquoted term fragments. Raw spelling, case, and quoting remain significant. `ParseError` reports a zero-based character offset. Implicit AND requires `allow_implicit_and=True` and emits `ImplicitAndWarning`.

AST nodes are immutable. `canonical_key(expr)` returns a recursively typed `CanonicalKey` union of `TermKey`, `UnaryKey`, and `BinaryKey`, using ordinary tuple equality, hashing, and ordering modulo AND/OR association and operand order. Raw term identity and duplicate operands remain significant; this is not complete Boolean equivalence. The aliases describe the tuple shapes without runtime wrappers; relative sort order remains an implementation detail, and its hash is not a persistent revision digest. `unparse`, `canonicalize`, and `simplify` operate on expressions. Simplification and canonicalization are separate, explicit operations; comparison and merge never silently apply them. `collect_terms`/`compare_terms` support an explicit inventory key but inventory changes alone do not determine match-set effects.

Optional lexical conventions remain in `conventions/`. A `TermMatcher` can be supplied to simplification; semantic revision comparison uses explicit assumption expressions instead. The core does not import optional conventions. There is no general `analyze()` or duplicate-term diagnostic service.

## Structure

- `syntax/`: expressions and the Lark grammar/AST adapter.
- `analysis/`: inventory/structural comparison, revision effects, a scoped PySAT adapter, and internal matching/redundancy proofs.
- `merging.py`: conservative three-way merge and conflicts.
- `transformations.py`: explicit canonicalization and simplification.
- `presentation.py`: reconstructed-text diff rendering.
- `conventions/`: optional lexical heuristics.

[tests/README.md](tests/README.md) describes the contracts and independent Boolean-oracle checks. Version 0.6 replaces handwritten parsing with Lark and truth-table enumeration with limited SAT checks. Comparison and merge result types remain independent of both libraries. No compatibility with a consuming application's historical assumptions is imposed.

## Graphify

```bash
uv tool install graphifyy
graphify extract . --code-only
graphify export html
graphify hook install
graphify path 'compare_revisions' 'structural_edits'
graphify path 'merge_revisions' 'structural_edits'
```

Generated graphs are local and ignored; no LLM API key is needed. Use graph relationships to identify review candidates, then verify their contracts and callers.
