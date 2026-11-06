# ssp

Search-string comparison and merge primitives for building version-control tools. Python 3.11+, with no runtime dependencies. SSP does not store revisions or manage repositories.

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

Effect classification uses bounded exhaustive evaluation. The default `max_assignments=4096` supports up to 12 distinct symbols across the two revisions and assumptions; larger comparisons return `UNKNOWN` before enumerating. Callers may explicitly increase the budget, with exponential cost. Identical or associatively reordered expressions without assumptions can be proven equivalent directly at any symbol count. The existing implication helper remains a conservative internal aid for simplification, not a semantic classification oracle.

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

The generic core parses uppercase AND/OR/NOT with precedence NOT > AND > OR, balanced parentheses, and opaque quoted/unquoted term fragments. Raw spelling, case, and quoting remain significant. `ParseError` reports a zero-based character offset. Implicit AND requires `allow_implicit_and=True` and emits `ImplicitAndWarning`.

AST nodes are immutable. `unparse`, `canonicalize`, and `simplify` operate on expressions. Simplification and canonicalization are separate, explicit operations; comparison and merge never silently apply them. `collect_terms`/`compare_terms` support an explicit inventory key but inventory changes alone do not determine match-set effects.

Optional lexical conventions remain in `conventions/`. A `TermMatcher` can be supplied to simplification; semantic revision comparison uses explicit assumption expressions instead. The core does not import optional conventions. There is no general `analyze()` or duplicate-term diagnostic service.

## Structure

- `syntax/`: expressions, tokens, grammar.
- `analysis/`: inventory and structural comparison, revision effects, internal matching/redundancy proofs.
- `merging.py`: conservative three-way merge and conflicts.
- `transformations.py`: explicit canonicalization and simplification.
- `presentation.py`: reconstructed-text diff rendering.
- `conventions/`: optional lexical heuristics.

[tests/README.md](tests/README.md) describes the contracts and independent Boolean-oracle checks. Version 0.5 replaces the general diagnostic interface with revision comparison and merge operations. No compatibility with a consuming application's historical assumptions is imposed.

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
