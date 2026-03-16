# Lab Work No. 3 — Lexer / Scanner

**Course:** Formal Languages & Finite Automata  
**Author:** Serghei Barladean
**Date:** March 2026

---

## Table of Contents

1. [Objectives](#objectives)
2. [Theoretical Background](#theoretical-background)
3. [Domain — Mini SQL Lexer](#domain--mini-sql-lexer)
4. [Token Specification](#token-specification)
5. [Implementation](#implementation)
6. [Program Output](#program-output)
7. [Conclusions](#conclusions)

---

## Objectives

1. Understand what lexical analysis is and its role in language processing.
2. Get familiar with the inner workings of a lexer / scanner / tokenizer.
3. Design a non-trivial token set for a chosen domain.
4. Implement a fully functional lexer in Python.
5. Demonstrate the lexer on representative input and explain the token stream produced.

---

## Theoretical Background

### What is Lexical Analysis?

Lexical analysis is the **first phase** of a compiler or interpreter. Given a raw character stream, the **lexer** (scanner / tokenizer) groups characters into meaningful chunks called **lexemes** and assigns a category label — the **token type** — to each one.

The output is a flat sequence of `(type, lexeme)` pairs that the parser works with directly.

**Lexeme vs Token:**

| Concept | What it is | Example |
|---------|-----------|---------|
| Lexeme  | The raw extracted substring | `SELECT`, `42`, `>=` |
| Token   | Categorised object: type + value + metadata | `Token(KEYWORD, 'SELECT', line=1)` |

The parser sees token *types*, not raw text — it doesn't care about whitespace, comments, or exact character sequences. That's the lexer's job.

---

### How a Lexer Fits in a Pipeline

```
Source code
    │
    ▼
┌─────────┐   token stream   ┌────────┐   AST   ┌────────────┐
│  LEXER  │ ──────────────▶  │ PARSER │ ──────▶  │ EVALUATOR  │
└─────────┘                  └────────┘          └────────────┘
"What are the words?"    "What is the grammar?"  "What does it mean?"
```

---

### Maximal Munch Rule

When multiple patterns could match at the current position, the lexer always picks the **longest match**. This is why `>=` becomes a single `GTE` token, not `GT` + `EQ`. In practice: always check two-character operators *before* single-character ones.

---

### Connection to Finite Automata (Lab 2)

Every token type corresponds to a **regular language**, and every regular language is recognised by a **DFA**. A production-grade lexer generator (Flex, ANTLR) compiles token regexes into a combined DFA via the subset construction algorithm — exactly what we implemented in Lab 2. The lexer in this lab is a hand-written simulation of that same idea.

---

## Domain — Mini SQL Lexer

A **Mini SQL dialect** was chosen as the domain. It exercises:
- Reserved keywords (case-insensitive)
- Identifiers with underscores
- Integer and float literals (including scientific notation)
- Single-quoted string literals with escape sequences
- Comparison and arithmetic operators (including two-character ones)
- DOT notation for qualified names (`table.column`)
- Line comments (`--`)
- Whitespace handling

Supported keywords:

```
SELECT  FROM    WHERE   AND     OR      NOT     NULL    AS      DISTINCT
ORDER   BY      LIMIT   OFFSET  JOIN    ON      INNER   LEFT    RIGHT
OUTER   CREATE  TABLE   DROP    DELETE  UPDATE  SET     INSERT  INTO
VALUES  GROUP   HAVING
```

---

## Token Specification

| Token Type   | Pattern / Rule                                      | Example          |
|--------------|-----------------------------------------------------|------------------|
| `KEYWORD`    | Case-insensitive match from keyword set             | `SELECT`, `where`|
| `IDENTIFIER` | `[A-Za-z_][A-Za-z0-9_]*` — not a keyword           | `employees`, `t1`|
| `INTEGER`    | `[0-9]+`                                            | `0`, `42`, `1000`|
| `FLOAT`      | `[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?`                 | `3.14`, `1.0e10` |
| `STRING`     | `'...'` — single-quoted, `\'` escape inside         | `'Alice'`        |
| `STAR`       | `*`                                                 | `*`              |
| `PLUS`       | `+`                                                 | `+`              |
| `MINUS`      | `-`                                                 | `-`              |
| `SLASH`      | `/`                                                 | `/`              |
| `PERCENT`    | `%`                                                 | `%`              |
| `EQ`         | `=`                                                 | `=`              |
| `NEQ`        | `<>` or `!=`                                        | `<>`, `!=`       |
| `LT`         | `<`  (not followed by `>` or `=`)                   | `<`              |
| `GT`         | `>`  (not followed by `=`)                          | `>`              |
| `LTE`        | `<=`                                                | `<=`             |
| `GTE`        | `>=`                                                | `>=`             |
| `COMMA`      | `,`                                                 | `,`              |
| `SEMICOLON`  | `;`                                                 | `;`              |
| `LPAREN`     | `(`                                                 | `(`              |
| `RPAREN`     | `)`                                                 | `)`              |
| `DOT`        | `.`                                                 | `.`              |
| `UNKNOWN`    | Any unrecognised character                          | `@`, `#`         |
| `EOF`        | End of input sentinel                               | —                |

Whitespace (spaces, tabs, newlines) and line comments (`-- ...`) are **consumed and discarded** — they never appear in the token stream.

---

## Implementation

### Project Structure

```
lab3/
├── src/
│   ├── sql_token.py   # TokenType enum + Token dataclass
│   ├── lexer.py       # Lexer class — all scanning logic
│   └── main.py        # Demo script with 6 test cases
└── README.md
```

---

### `sql_token.py` — Token Types

```python
from enum import Enum, auto
from dataclasses import dataclass

class TokenType(Enum):
    INTEGER = auto(); FLOAT = auto(); STRING = auto()
    KEYWORD = auto(); IDENTIFIER = auto()
    PLUS = auto();  MINUS = auto();   STAR = auto()
    SLASH = auto(); PERCENT = auto()
    EQ = auto();    NEQ = auto();     LT = auto()
    GT = auto();    LTE = auto();     GTE = auto()
    COMMA = auto(); SEMICOLON = auto()
    LPAREN = auto(); RPAREN = auto(); DOT = auto()
    EOF = auto();   UNKNOWN = auto()

@dataclass
class Token:
    type:  TokenType
    value: str
    line:  int
```

---

### `lexer.py` — Lexer Class

The lexer maintains three state variables: `src` (source string), `pos` (current position), `line` (current line number for error reporting).

**Scan sequence on each call to `next_token()`:**

1. Skip whitespace and line comments
2. Return `EOF` if end of input
3. Try **two-character operators** first (`<=`, `>=`, `<>`, `!=`) — maximal munch
4. If digit → `_scan_number()` (float before int)
5. If `'` → `_scan_string()`
6. If alpha or `_` → `_scan_word()` then keyword lookup
7. Try single-character punctuation/operators
8. Otherwise emit `UNKNOWN`

**Key method — `_scan_number()`:**

```python
def _scan_number(self) -> Token:
    start = self.pos
    while self.current and self.current.isdigit():
        self.pos += 1
    # Peek ahead for decimal point → FLOAT
    if self.current == "." and self.peek and self.peek.isdigit():
        self.pos += 1
        while self.current and self.current.isdigit():
            self.pos += 1
        if self.current in ("e", "E"):          # optional exponent
            self.pos += 1
            if self.current in ("+", "-"):
                self.pos += 1
            while self.current and self.current.isdigit():
                self.pos += 1
        return Token(TokenType.FLOAT, self.src[start:self.pos], self.line)
    return Token(TokenType.INTEGER, self.src[start:self.pos], self.line)
```

Without the lookahead, `3.14` would be misread as `INTEGER(3)` `DOT(.)` `INTEGER(14)`.

**Key method — `_scan_word()` with keyword lookup:**

```python
def _scan_word(self) -> Token:
    start = self.pos
    while self.current and (self.current.isalnum() or self.current == "_"):
        self.pos += 1
    word  = self.src[start:self.pos]
    ttype = TokenType.KEYWORD if word.upper() in SQL_KEYWORDS else TokenType.IDENTIFIER
    return Token(ttype, word, self.line)
```

Case-insensitive lookup: `SELECT`, `select`, `Select` → all produce `KEYWORD`.

**Key method — `_skip_whitespace_and_comments()`:**

```python
def _skip_whitespace_and_comments(self):
    while self.current is not None:
        if self.current in (" ", "\t", "\r"):
            self.pos += 1
        elif self.current == "\n":
            self.pos += 1; self.line += 1
        elif self.current == "-" and self.peek == "-":
            while self.current not in (None, "\n"):
                self.pos += 1
        else:
            break
```

---

### Running

```bash
cd src
python3 main.py
```

---

## Program Output

```
============================================================
TEST: Basic SELECT with WHERE
INPUT: 'SELECT * FROM employees WHERE dept_id = 10;'
============================================================
  Token(KEYWORD      'SELECT'             line=1)
  Token(STAR         '*'                  line=1)
  Token(KEYWORD      'FROM'               line=1)
  Token(IDENTIFIER   'employees'          line=1)
  Token(KEYWORD      'WHERE'              line=1)
  Token(IDENTIFIER   'dept_id'            line=1)
  Token(EQ           '='                  line=1)
  Token(INTEGER      '10'                 line=1)
  Token(SEMICOLON    ';'                  line=1)

============================================================
TEST: Arithmetic expression + FLOAT literal
INPUT: 'SELECT name, salary * 1.1 AS new_sal FROM staff WHERE salary >= 50000.0;'
============================================================
  Token(KEYWORD      'SELECT'             line=1)
  Token(IDENTIFIER   'name'               line=1)
  Token(COMMA        ','                  line=1)
  Token(IDENTIFIER   'salary'             line=1)
  Token(STAR         '*'                  line=1)
  Token(FLOAT        '1.1'                line=1)
  Token(KEYWORD      'AS'                 line=1)
  Token(IDENTIFIER   'new_sal'            line=1)
  Token(KEYWORD      'FROM'               line=1)
  Token(IDENTIFIER   'staff'              line=1)
  Token(KEYWORD      'WHERE'              line=1)
  Token(IDENTIFIER   'salary'             line=1)
  Token(GTE          '>='                 line=1)
  Token(FLOAT        '50000.0'            line=1)
  Token(SEMICOLON    ';'                  line=1)

============================================================
TEST: JOIN with table alias and DOT notation
INPUT: 'SELECT e.name FROM employees e JOIN departments d ON e.dept_id = d.id'
============================================================
  Token(KEYWORD      'SELECT'             line=1)
  Token(IDENTIFIER   'e'                  line=1)
  Token(DOT          '.'                  line=1)
  Token(IDENTIFIER   'name'               line=1)
  Token(KEYWORD      'FROM'               line=1)
  Token(IDENTIFIER   'employees'          line=1)
  Token(IDENTIFIER   'e'                  line=1)
  Token(KEYWORD      'JOIN'               line=1)
  Token(IDENTIFIER   'departments'        line=1)
  Token(IDENTIFIER   'd'                  line=1)
  Token(KEYWORD      'ON'                 line=1)
  Token(IDENTIFIER   'e'                  line=1)
  Token(DOT          '.'                  line=1)
  Token(IDENTIFIER   'dept_id'            line=1)
  Token(EQ           '='                  line=1)
  Token(IDENTIFIER   'd'                  line=1)
  Token(DOT          '.'                  line=1)
  Token(IDENTIFIER   'id'                 line=1)

============================================================
TEST: Multi-line query with line comment and NEQ operator
INPUT: '-- get all active users\nSELECT id, email FROM users WHERE active <> 0 LIMIT 25;'
============================================================
  Token(KEYWORD      'SELECT'             line=2)
  Token(IDENTIFIER   'id'                 line=2)
  Token(COMMA        ','                  line=2)
  Token(IDENTIFIER   'email'              line=2)
  Token(KEYWORD      'FROM'               line=2)
  Token(IDENTIFIER   'users'              line=2)
  Token(KEYWORD      'WHERE'              line=2)
  Token(IDENTIFIER   'active'             line=2)
  Token(NEQ          '<>'                 line=2)
  Token(INTEGER      '0'                  line=2)
  Token(KEYWORD      'LIMIT'              line=2)
  Token(INTEGER      '25'                 line=2)
  Token(SEMICOLON    ';'                  line=2)

============================================================
TEST: String literal with escaped apostrophe
INPUT: "SELECT * FROM users WHERE name = 'O\\'Brien';"
============================================================
  Token(KEYWORD      'SELECT'             line=1)
  Token(STAR         '*'                  line=1)
  Token(KEYWORD      'FROM'               line=1)
  Token(IDENTIFIER   'users'              line=1)
  Token(KEYWORD      'WHERE'              line=1)
  Token(IDENTIFIER   'name'               line=1)
  Token(EQ           '='                  line=1)
  Token(STRING       "O'Brien"            line=1)
  Token(SEMICOLON    ';'                  line=1)

============================================================
TEST: Subexpression with parentheses
INPUT: 'SELECT (salary + bonus) * 1.2 FROM employees;'
============================================================
  Token(KEYWORD      'SELECT'             line=1)
  Token(LPAREN       '('                  line=1)
  Token(IDENTIFIER   'salary'             line=1)
  Token(PLUS         '+'                  line=1)
  Token(IDENTIFIER   'bonus'              line=1)
  Token(RPAREN       ')'                  line=1)
  Token(STAR         '*'                  line=1)
  Token(FLOAT        '1.2'                line=1)
  Token(KEYWORD      'FROM'               line=1)
  Token(IDENTIFIER   'employees'          line=1)
  Token(SEMICOLON    ';'                  line=1)
```

---

## Conclusions

1. **Lexical analysis cleanly separates concerns.** The lexer shields the parser from whitespace, comments, and raw character sequences. The parser sees only typed tokens — it never needs to know what a space looks like.

2. **Maximal munch is essential for operator correctness.** Scanning `<=`, `>=`, `<>`, `!=` before their single-character components means `>=` is never misread as `GT` + `EQ`. The rule is simple to implement: just check two-character patterns first.

3. **Keywords and identifiers share one scanning path.** Scan the word first, then do a case-insensitive lookup in the keyword set. This is simpler than writing separate patterns for every keyword and handles SQL's case-insensitivity for free.

4. **Float detection requires lookahead.** The integer scanner must peek at the next character after consuming digits. If it sees `.` followed by a digit, it switches to float mode. Without this, `3.14` becomes `INTEGER(3)` `DOT(.)` `INTEGER(14)`.

5. **The connection to Lab 2 is direct.** Every token type is a regular language; every regular language is recognised by a DFA. A real lexer generator (Flex, ANTLR) runs exactly the subset construction from Lab 2 on the combined token regex to produce a single DFA. This hand-written lexer is a manual simulation of the same concept.

6. **Line tracking enables useful error messages.** Maintaining a `line` counter throughout the scan loop makes `LexerError: Unterminated string at line 3` possible — without it, debugging becomes painful.
