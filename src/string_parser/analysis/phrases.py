"""Lexical phrase containment and branch subsumption predicates."""

from __future__ import annotations


def _phrase_words(term: str) -> list[str]:
    return term.lower().strip('"').split()


def _is_subphrase(broader: str, narrower: str) -> bool:
    """True if broader's words appear as a contiguous run inside narrower's words.

    In OR context broader already captures every hit narrower would — narrower is redundant.
    """
    bw = _phrase_words(broader)
    nw = _phrase_words(narrower)
    n = len(bw)
    if n >= len(nw):
        return False
    return any(nw[i : i + n] == bw for i in range(len(nw) - n + 1))


def _branch_subsumes(e1: set[str], e2: set[str]) -> bool:
    """True if every document matching e2 (AND of e2 terms) also matches e1 (AND of e1 terms).

    This holds when every term in e1 has a broader-or-equal counterpart in e2.
    """
    if e1 == e2:
        return False
    return all(any(t1 == t2 or _is_subphrase(t1, t2) for t2 in e2) for t1 in e1)
