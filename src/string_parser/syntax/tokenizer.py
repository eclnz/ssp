"""Tokenize query text while preserving term spelling and quotes."""

from __future__ import annotations

import re
from enum import Enum

from .ast import Op, Term

_TOKEN = re.compile(r'"[^"]*"|\b(?:AND|OR|NOT)\b|[()]|[^\s()]+')


class _Paren(Enum):
    OPEN = "("
    CLOSE = ")"


_Token = Term | Op | _Paren


def _tokenize(string: str) -> list[_Token]:
    tokens: list[_Token] = []
    for m in _TOKEN.findall(string):
        if m == "AND":
            tokens.append(Op.AND)
        elif m == "OR":
            tokens.append(Op.OR)
        elif m == "NOT":
            tokens.append(Op.NOT)
        elif m == "(":
            tokens.append(_Paren.OPEN)
        elif m == ")":
            tokens.append(_Paren.CLOSE)
        else:
            tokens.append(Term(m))
    return tokens
