## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.

## Interface review with graphify

- Build locally with `graphify extract . --code-only` and `graphify export html`; generated output is ignored. Initialize each new clone before querying. No semantic backend or API key is needed for this workflow.
- Use `graphify explain` and qualified `path::symbol` references when names collide. Treat name collisions as review candidates, not automatic bugs.
- Review cross-package imports, cycles, private-name imports, overly broad signatures, and assumptions lost in return types. Confirm contracts and actual callers before changing an interface.
- Expected dependency direction: `syntax` is independent; `analysis` may use syntax; `transformations` may use syntax and analysis; `presentation` renders syntax/analysis data; `api.py` orchestrates all layers. Export facades and AST types naturally have high connectivity.
- Distinguish EXTRACTED relationships from INFERRED relationships. Graph rank and community membership alone are not evidence of poor design.
- After interface changes, run `uv run pytest` and `uv run ruff check .`, then refresh the graph. Git hooks are local; install them in a new checkout with `graphify hook install`.
