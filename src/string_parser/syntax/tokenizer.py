"""Tokenize query text while preserving term spelling and quotes."""

from __future__ import annotations

import re
from enum import Enum

from .ast import Op, Term

_TOKEN = re.compile(r'"[^"]*"|\b(?:AND|OR|NOT)\b|[()]|[^\s()]+')


class Paren(Enum):
    OPEN = "("
    CLOSE = ")"


Token = Term | Op | Paren


def tokenize(string: str) -> list[Token]:
    tokens: list[Token] = []
    for m in _TOKEN.findall(string):
        if m == "AND":
            tokens.append(Op.AND)
        elif m == "OR":
            tokens.append(Op.OR)
        elif m == "NOT":
            tokens.append(Op.NOT)
        elif m == "(":
            tokens.append(Paren.OPEN)
        elif m == ")":
            tokens.append(Paren.CLOSE)
        else:
            tokens.append(Term(m))
    return tokens
