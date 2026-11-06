"""Positioned lexical tokens, independent of expression tree nodes."""

import re
from dataclasses import dataclass
from enum import Enum

from .errors import ParseError


class TokenKind(Enum):
    TERM = "TERM"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    OPEN = "("
    CLOSE = ")"


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    text: str
    start: int
    end: int


# A field suffix remains attached to its quoted phrase. Other field syntax is opaque.
_TOKEN = re.compile(r'"[^"\n]*"(?:\[[^\]\n]+\])?|[()]|[^"\s()]+')


def tokenize(text: str) -> list[Token]:
    """Preserve lexemes and offsets; reject unmatched quotes."""
    result: list[Token] = []
    pos = 0
    while pos < len(text):
        if text[pos].isspace():
            pos += 1
            continue
        match = _TOKEN.match(text, pos)
        if match is None:
            raise ParseError("Unterminated quoted phrase", pos)
        value = match.group()
        kind = TokenKind(value) if value in {"AND", "OR", "NOT", "(", ")"} else TokenKind.TERM
        result.append(Token(kind, value, pos, match.end()))
        pos = match.end()
    return result
