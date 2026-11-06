"""Explicit assumptions about when one term covers another."""

from enum import Enum

from .terms import term_key


class MatchPolicy(Enum):
    EXACT = "exact"
    LEXICAL_PHRASE = "lexical_phrase"

    def key(self, term: str) -> str:
        if self is MatchPolicy.EXACT or any(c in term for c in "[]*?"):
            return term
        return term_key(term)

    def covers_term(self, broader: str, narrower: str) -> bool:
        """EXACT treats raw terms as symbols; lexical matching assumes phrase containment.

        Lexical matching is a heuristic, not a database-aware guarantee. Field-tagged
        and wildcard terms are compared literally even under the lexical policy.
        """
        if self is MatchPolicy.EXACT:
            return broader == narrower
        if any(c in broader + narrower for c in "[]*?"):
            return broader == narrower
        a, b = term_key(broader).split(), term_key(narrower).split()
        return bool(a) and any(b[i : i + len(a)] == a for i in range(len(b) - len(a) + 1))
