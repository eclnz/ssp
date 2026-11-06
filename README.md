# ssp

A dependency-free Python library for parsing, comparing, linting, and simplifying Boolean literature search strings. Extracted from [litdb](https://github.com/eclnz/litdb), preserving its `string_parser` API and behavior.

Requires Python 3.11 or later.

## Install

```bash
pip install .
# Development
uv sync --group dev
uv run pytest
uv run ruff check .
```

## Usage

```python
from string_parser import parse, collect_terms, classify_change, suggest_simplification

query = parse('(COPD OR AECOPD) AND NIV')
assert collect_terms(query) == {"copd", "aecopd", "niv"}
assert classify_change("COPD AND NIV", "COPD AND BiPAP") == ({"bipap"}, {"niv"})
assert suggest_simplification('flow OR "high flow"') == "flow"
```

## API

- Expression trees: `Term`, `BinaryExpr`, `UnaryExpr`, `Expr`, `Op`.
- Parsing and rendering: `parse`, `unparse`, `print_expr`, `collect_terms`, `combine`.
- Normalization: `canonicalize`, `canonical_form`, `canonically_equal`.
- Analysis: `classify_change`, `find_duplicate_terms`, `find_subsumed_terms`, `find_and_redundancies`, `find_absorbed_branches`, `find_subsumed_branches`.
- Simplification: `simplify`, `lint_string`, `suggest_simplification`.
- ANSI terminal diffs: `format_simplification_diff`, `format_string_diff`, `Colour`.

## Query semantics and limits

Operators are uppercase `NOT`, `AND`, and `OR`, with precedence `NOT > AND > OR`. Parentheses group expressions; double quotes preserve phrases. Adjacent terms imply AND and emit `ImplicitAndWarning`. Terms retain their original text; term collection lowercases them and strips surrounding quotes.

This preserves litdb's original parser behavior. It is not a complete PubMed grammar or a strict query validator: database field tags remain term text, unmatched parentheses and trailing tokens may be accepted, and malformed or empty input can raise `ValueError` or `IndexError`. Simplification uses lexical phrase containment rather than database-aware search semantics. Review suggestions before applying them to a database query.

## Package layout

`__init__.py` provides the stable public API; package initializers contain no implementation.

```text
src/string_parser/
├── __init__.py
├── syntax/                 # query language and expression trees
│   ├── ast.py
│   ├── tokenizer.py
│   ├── parser.py
│   ├── traversal.py
│   ├── composition.py
│   └── serialization.py
├── analysis/               # inspect queries without changing them
│   ├── terms.py
│   ├── phrases.py
│   ├── changes.py
│   ├── redundancy.py
│   └── lint.py
├── transformations/        # produce new expression trees
│   ├── normalization.py
│   └── simplification.py
└── presentation/           # human-facing terminal output
    ├── console.py
    └── diff.py
```

`syntax` is the foundation and has no dependencies on higher-level packages. `analysis` inspects syntax trees. `transformations` uses syntax and lexical analysis to produce normalized or simplified trees. `presentation` consumes those results to display trees and diffs. Query serialization belongs to `syntax`, so transformations do not depend on terminal formatting.

Tests mirror these four package folders. Internal modules import their dependencies directly; callers can continue using `from string_parser import parse` and the other existing public imports.

## Provenance

The initial implementation and tests come from `src/string_parser.py` and `tests/test_string_parser.py` in litdb. No runtime database, GUI, network, or litdb dependencies are required.
