from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    # --- Literals ---
    INTEGER    = auto()
    FLOAT      = auto()
    STRING     = auto()

    # --- Named tokens ---
    KEYWORD    = auto()
    IDENTIFIER = auto()

    # --- Arithmetic operators ---
    PLUS    = auto()
    MINUS   = auto()
    STAR    = auto()
    SLASH   = auto()
    PERCENT = auto()

    # --- Comparison operators ---
    EQ  = auto()   # =
    NEQ = auto()   # <> or !=
    LT  = auto()   # <
    GT  = auto()   # >
    LTE = auto()   # <=
    GTE = auto()   # >=

    # --- Punctuation ---
    COMMA     = auto()
    SEMICOLON = auto()
    LPAREN    = auto()
    RPAREN    = auto()
    DOT       = auto()

    # --- Control ---
    EOF     = auto()
    UNKNOWN = auto()


@dataclass
class Token:
    type:  TokenType
    value: str
    line:  int

    def __repr__(self):
        return f"Token({self.type.name:<12} {self.value!r:<20} line={self.line})"
