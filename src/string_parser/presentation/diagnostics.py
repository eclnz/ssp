"""Human-readable wording for structured analysis findings."""

from ..analysis.diagnostics import Diagnostic, DiagnosticKind


def render_diagnostic(item: Diagnostic) -> str:
    if item.kind is DiagnosticKind.DUPLICATE:
        return f"Duplicate term: {item.broader[0]!r} appears more than once"
    if item.kind is DiagnosticKind.AND_REDUNDANCY:
        a, b = item.broader[0], item.narrower[0]
        return f"AND redundancy: {a!r} is satisfied when {b!r} matches — {a!r} can be removed under {item.policy.value} matching"
    return f"OR redundancy: ({' AND '.join(item.narrower)}) is captured by ({' AND '.join(item.broader)}) under {item.policy.value} matching"
