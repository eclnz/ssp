"""Positioned lexical tokens, tokenization, and shared parse errors."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class ParseError(ValueError):
    """Invalid query syntax at a zero-based character offset."""

    def __init__(self, message: str, position: int):
        self.position = position
        super().__init__(f"{message} at character {position}")


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
