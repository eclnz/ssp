"""The minimum matching contract and generic raw-symbol identity."""

from typing import Protocol


class TermMatcher(Protocol):
    """Sound, reflexive, transitive coverage; false may conservatively mean unknown."""

    def covers_term(self, broader: str, narrower: str) -> bool: ...


class ExactMatcher:
    def covers_term(self, broader: str, narrower: str) -> bool:
        return broader == narrower


EXACT = ExactMatcher()
