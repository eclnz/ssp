"""Plain-text and optional ANSI revision-diff rendering."""

from __future__ import annotations

from enum import StrEnum

from .analysis.diff import ChangeKind, ExpressionDiff, Fragment


class Colour(StrEnum):
    RED = "\033[31m"
    GREEN = "\033[32m"
    RESET = "\033[0m"


def render_diff(diff: ExpressionDiff, *, color: bool = True) -> tuple[str, str]:
    def render(fragments: tuple[Fragment, ...]) -> str:
        result = []
        for fragment in fragments:
            if not color or fragment.kind is ChangeKind.SAME:
                result.append(fragment.text)
            else:
                code = Colour.RED if fragment.kind is ChangeKind.REMOVED else Colour.GREEN
                result.append(f"{code}{fragment.text}{Colour.RESET}")
        return "".join(result)

    return render(diff.before), render(diff.after)
