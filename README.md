# ssp

A dependency-free Python library for Boolean literature search queries, extracted from [litdb](https://github.com/eclnz/litdb). Requires Python 3.11 or later.

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
uv build
```

## Expression API

Core operations accept immutable expression trees. String convenience functions are in `string_parser.api`.

```python
from string_parser import MatchPolicy, compare_terms, parse, simplify, unparse
from string_parser.api import suggest_simplification

old = parse("COPD AND NIV")
new = parse("COPD AND BiPAP")
changes = compare_terms(old, new)
assert changes.added == {"bipap"}
assert changes.removed == {"niv"}

query = parse('(A AND NOT B) OR A')
assert unparse(simplify(query)) == "A"

# Phrase containment is an explicit heuristic, never the default.
assert suggest_simplification('flow OR "high flow"') is None
assert suggest_simplification('flow OR "high flow"', policy=MatchPolicy.LEXICAL_PHRASE) == "flow"
```

## Contracts

- `parse(text) -> Expr` consumes the entire query. Invalid or empty input raises `ParseError`, a `ValueError` with a zero-based `position`. Operators are uppercase, with precedence `NOT > AND > OR`. Adjacent operands imply AND and emit `ImplicitAndWarning`.
- Tokens carry original text and character offsets. Lexical tokens and AST nodes are separate types. Quoted field suffixes such as `"high flow"[tiab]` stay attached to the phrase. This is a Boolean grammar, not a complete database-specific query validator.
- AST nodes are immutable. Binary nodes accept AND/OR; unary nodes accept NOT. `unparse` serializes a parsed tree back to parseable query text.
- `canonicalize(expr)` normalizes associative operand order only. Raw term spelling, case, and quoting remain significant; canonicalization does not prove general logical equivalence.
- `compare_terms(old, new)` reports normalized lexical inventories only. Operator changes and negation require `compare_expressions(old, new)`, which produces an unstyled structural diff or `None` when only operand order differs.
- `conjunction_terms(expr)` returns a complete positive conjunction or `None`. Unsupported OR/NOT subtrees never become partial term sets used as branch identities.
- `simplify(expr, policy=MatchPolicy.EXACT)` applies conservative duplicate and absorption rules. EXACT treats raw terms as independent symbols. `LEXICAL_PHRASE` additionally assumes case-insensitive contiguous phrase containment. That heuristic is not database-aware; field-tagged or wildcard terms are compared literally. Negation stays opaque except for matching identical expressions and simplifying its operand. This is not a complete Boolean theorem prover.
- `analyze(expr, policy=...)` produces structured diagnostics. Term duplicates are occurrence reports, not instructions to delete every repeated term. Focused redundancy reports currently cover positive conjunctions; simplification can additionally prove some mixed-tree absorption cases.
- `render_diff(plan, color=False)` gives plain text; the default enables ANSI colors. Analysis never emits styling or diagnostic prose. The diff displays reconstructed query text, not source-preserving edits.

## Package boundaries

```text
string_parser/
├── api.py                  # string-oriented orchestration
├── syntax/                 # no dependencies on higher layers
│   ├── ast.py              # immutable expression model
│   ├── tokenizer.py        # positioned lexical tokens
│   ├── parser.py           # grammar
│   ├── errors.py           # shared parse errors
│   ├── tree.py             # traversal, composition, structural identity
│   └── serialization.py    # expression → query text
├── analysis/               # inspect expressions; no rewrites or display
│   ├── terms.py            # inventories and complete conjunctions
│   ├── changes.py          # explicit term-only comparison
│   ├── matching.py         # term interpretation policy
│   ├── implication.py      # conservative proof rules
│   ├── redundancy.py       # focused redundancy reports
│   ├── diagnostics.py      # structured findings
│   └── diff.py             # structural alignment plan
├── transformations/        # produce new trees using syntax and analysis
│   ├── normalization.py
│   └── simplification.py
└── presentation/           # render analysis results for humans
    ├── diagnostics.py
    ├── console.py
    └── diff.py
```

The root package exposes the main expression operations; specialist helpers are imported from their defining module. Exported functions have public names. Package initializers contain imports or documentation only. Tests mirror concept folders and include parser regressions, exact-policy truth tables, rewrite idempotence, and plain-text diff round trips.

Version 0.2 deliberately changes the original API: `classify_change` becomes expression-level `compare_terms`; string helpers move to `api`; phrase-based rewriting requires explicit opt-in.

## Graphify interface review

```bash
graphify extract . --code-only
graphify export html
graphify explain "MatchPolicy"
graphify path "simplify" "implies"
graphify hook status
```

Install the development tool once with `uv tool install graphifyy`. Enable local updates with `graphify hook install`.

The code graph is generated locally in ignored `graphify-out/`. No LLM API key is needed for code-only extraction. Local Git hooks refresh it after code changes; run the extraction command after cloning to initialize a new checkout. Graph connectivity identifies review candidates; inspect actual contracts and callers before concluding an interface is poor.

## Provenance

The initial implementation and tests came from `src/string_parser.py` and `tests/test_string_parser.py` in litdb. The standalone package has no runtime database, GUI, network, or litdb dependencies.
