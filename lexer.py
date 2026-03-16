from sql_token import Token, TokenType


SQL_KEYWORDS = frozenset({
    "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "NULL", "AS", "DISTINCT",
    "ORDER", "BY", "LIMIT", "OFFSET", "JOIN", "ON", "INNER", "LEFT", "RIGHT",
    "OUTER", "CREATE", "TABLE", "DROP", "DELETE", "UPDATE", "SET", "INSERT",
    "INTO", "VALUES", "GROUP", "HAVING",
})


class LexerError(Exception):
    pass


class Lexer:
    def __init__(self, source: str):
        self.src  = source
        self.pos  = 0
        self.line = 1


    @property
    def current(self):
        return self.src[self.pos] if self.pos < len(self.src) else None

    @property
    def peek(self):
        return self.src[self.pos + 1] if self.pos + 1 < len(self.src) else None


    def next_token(self) -> Token:
        self._skip_whitespace_and_comments()

        if self.current is None:
            return Token(TokenType.EOF, "", self.line)

        ch  = self.current
        two = ch + (self.peek or "")

        if two == "<>": return self._emit(TokenType.NEQ, 2)
        if two == "!=": return self._emit(TokenType.NEQ, 2)
        if two == "<=": return self._emit(TokenType.LTE, 2)
        if two == ">=": return self._emit(TokenType.GTE, 2)

        if ch.isdigit():
            return self._scan_number()

        if ch == "'":
            return self._scan_string()

        if ch.isalpha() or ch == "_":
            return self._scan_word()
        
        single = {
            "+": TokenType.PLUS,    "-": TokenType.MINUS,
            "*": TokenType.STAR,    "/": TokenType.SLASH,
            "%": TokenType.PERCENT, "=": TokenType.EQ,
            "<": TokenType.LT,      ">": TokenType.GT,
            "(": TokenType.LPAREN,  ")": TokenType.RPAREN,
            ",": TokenType.COMMA,   ";": TokenType.SEMICOLON,
            ".": TokenType.DOT,
        }
        if ch in single:
            return self._emit(single[ch], 1)

        return self._emit(TokenType.UNKNOWN, 1)


    def _emit(self, ttype: TokenType, length: int) -> Token:
        tok = Token(ttype, self.src[self.pos : self.pos + length], self.line)
        self.pos += length
        return tok

    def _skip_whitespace_and_comments(self):
        while self.current is not None:
            if self.current in (" ", "\t", "\r"):
                self.pos += 1
            elif self.current == "\n":
                self.pos  += 1
                self.line += 1
            elif self.current == "-" and self.peek == "-":
                while self.current is not None and self.current != "\n":
                    self.pos += 1
            else:
                break

    def _scan_number(self) -> Token:
        start = self.pos
        while self.current and self.current.isdigit():
            self.pos += 1

        if self.current == "." and self.peek and self.peek.isdigit():
            self.pos += 1  
            while self.current and self.current.isdigit():
                self.pos += 1
            if self.current in ("e", "E"):
                self.pos += 1
                if self.current in ("+", "-"):
                    self.pos += 1
                while self.current and self.current.isdigit():
                    self.pos += 1
            return Token(TokenType.FLOAT, self.src[start : self.pos], self.line)

        return Token(TokenType.INTEGER, self.src[start : self.pos], self.line)

    def _scan_string(self) -> Token:
        start_line = self.line
        self.pos  += 1  # skip opening quote
        buf        = []
        while self.current != "'":
            if self.current is None:
                raise LexerError(f"Unterminated string literal at line {start_line}")
            if self.current == "\\" and self.peek == "'":
                buf.append("'")
                self.pos += 2
            else:
                if self.current == "\n":
                    self.line += 1
                buf.append(self.current)
                self.pos += 1
        self.pos += 1  # skip closing quote
        return Token(TokenType.STRING, "".join(buf), start_line)

    def _scan_word(self) -> Token:
        start = self.pos
        while self.current and (self.current.isalnum() or self.current == "_"):
            self.pos += 1
        word  = self.src[start : self.pos]
        ttype = TokenType.KEYWORD if word.upper() in SQL_KEYWORDS else TokenType.IDENTIFIER
        return Token(ttype, word, self.line)


def tokenize(source: str) -> list[Token]:
    lexer  = Lexer(source)
    tokens = []
    while True:
        tok = lexer.next_token()
        if tok.type == TokenType.EOF:
            break
        tokens.append(tok)
    return tokens
