"""Human-readable wording for validated diagnostic variants."""

from typing import assert_never

from ..analysis.diagnostics import Diagnostic, DuplicateTerm, RedundantOperandDiagnostic
from ..syntax.serialization import unparse


def render_diagnostic(item: Diagnostic) -> str:
    match item:
        case DuplicateTerm(term=term, count=count):
            return f"Duplicate term: {term!r} appears {count} times"
        case RedundantOperandDiagnostic():
            label = f"{item.matching_label} matching" if item.matching_label else "the selected matching assumptions"
            return f"{item.operator.value} redundancy: {unparse(item.redundant)!r} can be removed; retained {unparse(item.retained)!r} under {label}"
        case _:
            assert_never(item)
