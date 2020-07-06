from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional


@dataclass(frozen=True)
class Span:
    """A position in the original text file."""
    __slots__ = "line", "column"
    line: int
    column: int


VALID_SYMBOLS = {"{", "}", ":", ";", ",", "&", "*", '@', '=', "(", ")"}
VALID_KEYWORDS = {"Self", "self", "interface", "fun", "raw", "mut", "own", "opaque", "type",
                  "true", "false", "opt", "field", "default"}


class TokenType(Enum):
    IDENTIFIER = 0
    DOC_COMMENT = 1
    SYMBOL = 2
    KEYWORD = 3
    STRING_LITERAL = 4

class ParseException(Exception):
    span: Span

    def __init__(self, msg: str, span: Span):
        super().__init__(msg)
        self.span = span


@dataclass(frozen=True)
class Token:
    token_type: TokenType
    value: str
    span: Span
    __slots__ = "token_type", "value", "span"

    def is_keyword(self, k: str) -> bool:
        assert k in VALID_KEYWORDS
        return self.token_type == TokenType.KEYWORD and self.value == k

    def is_symbol(self, s: str):
        assert s in VALID_SYMBOLS
        return self.token_type == TokenType.SYMBOL and self.value == s


def lex_all(s: str) -> Iterable[Token]:
    if not s:
        return
    lexer = Lexer(s)
    while lexer.index < len(lexer.text):
        token = lex_next(lexer)
        if token is not None:
            yield token


def lex_next(lexer: "Lexer") -> Optional[Token]:
    c = lexer.peek()
    assert c is not None
    if c in VALID_SYMBOLS:
        span = lexer.span()
        lexer.pop()
        return Token(TokenType.SYMBOL, c, span)
    elif c == '/':
        c = lexer.peek(1)
        if c == '/':
            # Skip till the end of the line
            while lexer.index < len(lexer.text) and\
                    lexer.text[lexer.index] != '\n':
                lexer.index += 1
            return None  # This was skipped
        elif c == '*':
            if lexer.peek(2) != '*':
                raise ParseException("Block comments are unsupported", lexer.span())
            start_span = lexer.span()
            lexer.skip_text("/**\n")
            close_index = lexer.text.find('*/', lexer.index)
            if close_index < 0:
                raise ParseException("Unable to find end of comment", start_span)
            comment_text = lexer.text[lexer.index:close_index]
            lexer.skip_text(comment_text)
            comment_text = comment_text.strip()  # TODO: Is this right?
            lexer.skip_text("*/")
            return Token(
                TokenType.DOC_COMMENT,
                comment_text.strip(),  # TODO: Should we strip the comment's whitespace?
                start_span
            )
        else:
            raise ParseException(f"Unexpected char: {c}", lexer.span)
    elif c == '"':
        start_span = lexer.span()
        lexer.skip_text('"')
        result = []
        while True:
            c = lexer.peek()
            if c == '\\':
                escape_symbol = lexer.peek(1)
                if escape_symbol == '\\':
                    result.append('\\')
                elif escape_symbol == '"':
                    result.append('"')
                else:
                    raise ParseException(f"Invalid escape: {c!r}", lexer.span())
                lexer.index += 2
            elif c == '"':
                break
            else:
                result.append(c)
                lexer.index += 1
        lexer.skip_text('"')
        return Token(TokenType.STRING_LITERAL, ''.join(result), start_span)
    else:
        if c.isspace():
            # Skip all other whitespace
            while True:
                lexer.index += 1
                c = lexer.peek()
                if c is None or not c.isspace():
                    break
            return None  # We just encountered whitespace - nothing special
        start_span = lexer.span()
        ident = lexer.parse_identifier()
        if ident in VALID_KEYWORDS:
            return Token(TokenType.KEYWORD, ident, start_span)
        else:
            return Token(TokenType.IDENTIFIER, ident, start_span)


class Lexer:
    text: str
    index: int
    __slots__ = "text", "index", "_cached_line", "_line_start", "_line_end"

    def __init__(self, text: str):
        assert text, "Blank text"
        self.text = text
        self.index = 0
        self._cached_line = None
        self._line_start = 0
        end = text.find('\n')
        if end >= 0:
            self._line_end = end
        else:
            self._line_end = len(text)

    def peek(self, ahead: int = 0) -> Optional[str]:
        try:
            return self.text[self.index + ahead]
        except IndexError:
            return None

    def pop(self) -> str:
        try:
            c = self.text[self.index]
            self.index += 1
            return c
        except IndexError:
            raise ParseException("Unexpected EOF", self.span())

    def skip_text(self, expected: str):
        start = self.index
        end = self.index + len(expected)
        actual = self.text[start:end]
        if expected == actual:
            self.index = end
        else:
            raise ParseException(f"Expected {expected!r} but got {actual!r}", self.span())

    def parse_identifier(self):
        start = self.index
        end = start
        text = self.text
        while end < len(text) and (text[end].isidentifier() or text[end].isdigit()):
            end += 1
        # NOTE: Digits can't start identifier
        if start == end or text[start].isdigit():
            actual = repr(text[start]) if start < len(text) else "EOF"
            raise ParseException(f"Expected an identifier, but got {actual}", self.span())
        else:
            self.index = end
            return self.text[start:end]

    def span(self):
        if self.index < self._line_end and\
                self._cached_line is not None:
            return Span(self._cached_line, self.index - self._line_start)
        # Fallback to compute
        line = self._cached_line if self._cached_line is not None else 1
        index = self._line_start
        assert 0 <= index <= self.index
        while index < self.index:
            if self.text[index] == '\n':
                line += 1
                self._line_start = self._line_end + 1
                end = self.text.find('\n', index + 1)
                self._line_end = end if end >= 0 else len(self.text)
            index += 1
        assert self._line_start <= index <= self._line_end
        self._cached_line = line
        return Span(line, column=index - self._line_start)

    def __repr__(self):
        return f"Lexer(index={self.index}, span={self.span()!r})"
