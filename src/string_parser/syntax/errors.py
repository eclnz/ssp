"""Errors reported by tokenization and parsing."""


class ParseError(ValueError):
    """Invalid query syntax at a zero-based character offset."""

    def __init__(self, message: str, position: int):
        self.position = position
        super().__init__(f"{message} at character {position}")
