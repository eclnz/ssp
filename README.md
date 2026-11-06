# ssp

A dependency-free Python library for generic Boolean query syntax, analysis, and rewriting. Extracted from [litdb](https://github.com/eclnz/litdb). Python 3.11 or later.

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
uv build
```

## Generic core

```python
from string_parser import analyze, compare_terms, parse, simplify, unparse

query = parse('(A AND NOT B) OR A')
assert simplify(query) == parse('A')
assert compare_terms(parse('A'), parse('a')).added == {'a'}
assert simplify(parse('flow OR "high flow"')) == parse('flow OR "high flow"')
```

- `parse(text)` consumes the entire input or raises a positioned `ParseError` (`ValueError`). The chosen grammar uses uppercase AND/OR/NOT, precedence NOT > AND > OR, balanced parentheses, and double-quoted opaque terms. Case and quoting remain significant. Quoted suffixes such as `"high flow"[tiab]` stay opaque: their database meaning is not interpreted.
- Core parsing requires operators. Adjacency can be enabled with `parse(text, allow_implicit_and=True)` and emits `ImplicitAndWarning`. String helpers forward the same option.
- AST nodes are immutable; binary nodes require AND/OR and unary nodes require NOT. `unparse` serializes query text without promising particular whitespace or parenthesis placement.
- `compare_terms` reports raw inventories, not meaning changes. Normalization requires an explicit `key` function. `compare_expressions` compares structure, ignoring associative operand order, and returns an unstyled diff plan.
- `canonicalize` normalizes operand order only. `simplify` applies conservative duplicate/absorption rules with exact raw-symbol matching by default. Neither is a complete Boolean theorem prover.
- `analyze` and `simplify` share redundant-operand proofs, including mixed AND/OR/NOT trees. Evidence identifies a removable operand and a witness that survives its flattened group. Analysis describes the supplied tree; later rewrite stages may expose more findings.
- Diagnostics are `DuplicateTerm` or `RedundantOperandDiagnostic`. They have variant-specific required fields and validate their invariants. Repeated terms are occurrence reports, not automatic deletion advice. Rendering is exhaustive over the union and consumes no matching implementation objects.
- Diff rendering can be plain text or ANSI-colored. Styling cannot change the represented query. Diff output reconstructs query text; it is not a source-preserving edit.

## Optional conventions and matching extensions

```python
from string_parser import analyze, parse, simplify
from string_parser.api import suggest_simplification
from string_parser.conventions.lexical import LEXICAL_PHRASE, lexical_term_key
from string_parser import compare_terms

assert suggest_simplification('flow OR "high flow"', matcher=LEXICAL_PHRASE) == 'flow'
assert compare_terms(parse('A'), parse('a'), key=lexical_term_key) == (set(), set())
```

Lexical phrase containment and casefolded, quote-stripped inventories are optional heuristics, not universal Boolean laws or validated PubMed behavior. Field-tagged and wildcard terms are compared literally by the heuristic matcher. The generic core does not import the conventions package.

Algorithms accept a `TermMatcher` protocol with only `covers_term(broader, narrower) -> bool`. True must mean sound coverage; false may conservatively mean unknown. Coverage must be reflexive and transitive. A custom matcher needs no enum inheritance, normalization key, or presentation metadata:

```python
class CasefoldMatcher:
    def covers_term(self, broader: str, narrower: str) -> bool:
        return broader.casefold() == narrower.casefold()

expr = parse('COPD OR copd')
assert simplify(expr, matcher=CasefoldMatcher()) == parse('COPD')
findings = analyze(expr, matcher=CasefoldMatcher(), matching_label='case-insensitive identity')
```

The matching label is optional diagnostic data. The root package exports the main expression API; `api.py` holds string conveniences. Version 0.3 intentionally changes the extracted API: matching uses `matcher=`, inventories default to raw identity, implicit AND is opt-in, and generic diagnostic tuples/enums are replaced by typed variants. Legacy specialized report adapters have been removed.

## Package boundaries

- `syntax/`: AST, positioned tokens, grammar, errors, tree operations, serialization; independent of higher layers.
- `analysis/`: raw inventories, matching protocol, implication, shared redundancy evidence, diagnostics, structural diff plans.
- `transformations/`: apply normalization and proven rewrites using syntax and analysis.
- `presentation/`: render trees, diagnostics, and diff plans.
- `conventions/`: opt-in lexical heuristics and normalization. Core modules do not depend on it.
- `api.py`: string-oriented orchestration.

Public helpers have public names; package initializers contain imports or documentation only.

## Test philosophy

[tests/README.md](tests/README.md) distinguishes semantic laws, explicit grammar/API choices, and optional conventions. An independent Boolean evaluator checks meaning preservation for exhaustive shallow and seeded deeper samples. Tests do not demand a particular algorithm, branch order, message wording, or ANSI span arrangement. Historical test counts are not compatibility goals.

## Graphify interface review

```bash
graphify extract . --code-only
graphify export html
graphify explain 'TermMatcher'
graphify path 'simplify' 'find_redundant_operands'
graphify path 'analyze' 'find_redundant_operands'
graphify hook status
```

Install with `uv tool install graphifyy`; enable local updates with `graphify hook install`. Initialize a new clone with code-only extraction. Generated `graphify-out/` is ignored; no LLM API key is required. Use connectivity to identify candidates, then inspect actual contracts and callers before judging an interface.

## Provenance

The initial source and tests came from `src/string_parser.py` and `tests/test_string_parser.py` in litdb. That implementation and its tests are reference material, not the standalone package's specification. SSP has no runtime database, GUI, network, or litdb dependencies.
