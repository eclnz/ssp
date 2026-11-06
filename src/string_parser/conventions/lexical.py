"""Optional lexical heuristics, not claims about any search database."""


def lexical_term_key(value: str) -> str:
    """Casefold and remove one enclosing quote pair; preserve other raw syntax."""
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        value = value[1:-1]
    return value.casefold()


class LexicalPhraseMatcher:
    """Assume a contiguous phrase covers its extensions. Not database-aware."""

    def covers_term(self, broader: str, narrower: str) -> bool:
        if broader == narrower:
            return True
        if any(c in broader + narrower for c in "[]*?"):
            return broader == narrower
        a, b = lexical_term_key(broader).split(), lexical_term_key(narrower).split()
        return bool(a) and any(b[i : i + len(a)] == a for i in range(len(b) - len(a) + 1))


LEXICAL_PHRASE = LexicalPhraseMatcher()
