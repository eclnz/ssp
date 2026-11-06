# SSP

SSP provides search-string revision comparison and merge primitives. Revision storage and application workflows are outside scope.

The core is generic Boolean syntax. Raw terms retain their identity. Database conventions and lexical heuristics must be explicit, optional, and confined to `conventions/`.

## Graphify

- For `/graphify`, read the installed graphify skill first.
- Before inspecting unfamiliar code, query the existing `graphify-out/graph.json` with `graphify query`, `explain`, or `path`. Use qualified `path::symbol` references when names collide, and verify inferred relationships against source.
- Initialize a checkout with `graphify extract . --code-only`. After changes, run `graphify update .`. Output is local and ignored; no API key is needed.
- Use the graph to identify cycles, upward dependencies, broad interfaces, and ambiguous contracts. Connectivity alone is not a defect; AST types and export facades are expected hubs.

## Boundaries and checks

- `syntax` is independent; `analysis` uses syntax; `transformations` uses syntax and analysis; `presentation` renders results. The core never imports optional conventions.
- Lark owns parsing machinery; SSP owns the grammar, expressions, and error API. PySAT owns SAT solving; SSP owns the encoding, witness decoding, and effect classification. Keep third-party details at these adapter boundaries.
- Truth-table enumeration belongs in tests only. Unfinished SAT checks must never be interpreted as unsatisfiable. Solver budgets apply per check and are not time/memory limits.
- Public analysis is revision comparison, not a general linting service. Structural edits and Boolean effects are separate. Matchers implement only `covers_term`; semantic comparison takes explicit assumptions.
- Merge must preserve accepted occurrence edits and report overlapping/ambiguous edits as conflicts. Never return a partial executable expression on conflict.
- `merging.py` depends on comparison and syntax; do not introduce revision storage or application workflow logic.
- Read `tests/README.md` before changing contracts. Historical tests are not compatibility requirements. Prefer semantic laws over formatting snapshots or implementation shape assertions.
- Run `uv run pytest`, `uv run ruff check .`, and `uv build` for code changes. Refresh Graphify afterward.
