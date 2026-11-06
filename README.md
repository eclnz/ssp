# ssp

A dependency-free Python library for generic Boolean query parsing, analysis, and rewriting. Python 3.11+. Extracted from [litdb](https://github.com/eclnz/litdb).

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
uv build
```

## Expression API

```python
from string_parser import analyze, canonicalize, compare_terms, parse, simplify, unparse

query = parse('(A AND NOT B) OR A')
assert simplify(query) == parse('A')
assert compare_terms(parse('A'), parse('a')).added == {'a'}
findings = analyze(query)
text = unparse(simplify(query))
```

Core operations accept immutable expression trees. There is no parallel string-wrapper API.

- Grammar: uppercase AND/OR/NOT, precedence NOT > AND > OR, parentheses, and quoted opaque terms. Parsing consumes all input or raises `ParseError` with a zero-based character offset.
- Terms retain case and quoting. `"high flow"[tiab]` is an opaque lexeme, not an interpreted database expression. Binary AST nodes require AND/OR; unary nodes require NOT.
- Operators are required unless `parse(text, allow_implicit_and=True)` is explicitly selected. That convention emits `ImplicitAndWarning`.
- `compare_terms` compares raw inventories. Optional normalization requires `key=...`; this is not a meaning comparison.
- `canonicalize` sorts associative operands without interpreting terms. `simplify` applies conservative absorption/duplicate rules. Neither is a complete theorem prover.
- `analyze` and `simplify` share redundancy proofs. Evidence identifies removable operands and surviving witnesses. Analysis describes the supplied tree; later rewrite stages can expose more findings.
- Diagnostics are validated `DuplicateTerm` and `RedundantOperandDiagnostic` variants. Occurrence reports are not automatic deletion advice. An optional `matching_label` is data, not a matcher dependency.
- `compare_expressions` produces an unstyled structural diff. `presentation.diff.render_diff(plan, color=False)` renders plain text; the default adds ANSI styling. Output reconstructs queries rather than preserving source formatting.

## Optional conventions

```python
from string_parser.conventions.lexical import LEXICAL_PHRASE, lexical_term_key

assert simplify(parse('flow OR "high flow"')) == parse('flow OR "high flow"')
assert simplify(parse('flow OR "high flow"'), matcher=LEXICAL_PHRASE) == parse('flow')
assert compare_terms(parse('A'), parse('a'), key=lexical_term_key) == (set(), set())
```

Phrase containment and casefolded quote-stripped inventories are heuristics, not Boolean laws or verified database semantics. Field-tagged and wildcard terms are compared literally by the optional matcher. Core modules do not import conventions.

Custom matchers implement only `TermMatcher.covers_term(broader, narrower) -> bool`. True must be sound coverage; false may mean unknown. Coverage must be reflexive and transitive. No enum ancestry, normalization key, or display metadata is required.

## Structure and tests

- `syntax/`: AST, tokens, grammar, errors, structural operations, serialization.
- `analysis/`: inventories, matching contract, implication, shared redundancy evidence, typed findings, diff plans.
- `transformations/`: normalization and proven rewrites.
- `presentation/`: diagnostic and diff rendering.
- `conventions/`: opt-in lexical heuristics.

[tests/README.md](tests/README.md) distinguishes semantic laws from chosen API contracts and optional conventions. Independent truth tables check meaning preservation across exhaustive shallow and seeded deeper samples. Tests do not prescribe an algorithm, branch order, message wording, or ANSI span arrangement. The original source and tests are reference material, not the specification.

Version 0.4 removes the legacy string facade, specialized report adapters, AST printer, and implicit lexical defaults.

## Graphify

Install once with `uv tool install graphifyy`, then:

```bash
graphify extract . --code-only
graphify export html
graphify hook install
graphify path 'simplify' 'find_redundant_operands'
graphify path 'analyze' 'find_redundant_operands'
```

Graphs are local and ignored; no LLM API key is needed. Git hooks refresh the graph. Use connectivity to identify review candidates, then check their contracts and callers.
