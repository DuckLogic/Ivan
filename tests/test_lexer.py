from typing import List

from ivan.ast import lexer
from ivan.ast.lexer import Token, Span, TokenType


def lex(s: str) -> List[Token]:
    return list(lexer.lex_all(s))


def test_lex_str():
    assert lex('"string literal"') == [Token(
        span=Span(1, 0),
        value="string literal",
        token_type=TokenType.STRING_LITERAL
    )]


def test_lex_doc():
    assert lex(
        """/**
    * This is
    * multiline doc
    * comment
    */
    fun hello""") == [
               Token(
                   span=Span(1, 0),
                   token_type=TokenType.DOC_COMMENT,
                   value="* This is\n    * multiline doc\n    * comment"
               ),
               Token(
                   span=Span(6, 4),
                   token_type=TokenType.KEYWORD,
                   value='fun'
               ),
               Token(
                   span=Span(6, 8),
                   token_type=TokenType.IDENTIFIER,
                   value='hello'
               )
           ]


def test_lex_keywords():
    assert lex("interface") == [Token(
        span=Span(1, 0),
        token_type=TokenType.KEYWORD,
        value='interface'
    )]
    assert lex("fun interface") == [
        Token(
            span=Span(1, 0),
            token_type=TokenType.KEYWORD,
            value='fun'
        ),
        Token(
            span=Span(1, 4),
            token_type=TokenType.KEYWORD,
            value='interface'
        )
    ]


def test_lex_lines():
    assert lex(
        """interface {
    hello self
}""") == [
               Token(
                   token_type=TokenType.KEYWORD,
                   value="interface",
                   span=Span(1, 0)
               ),
               Token(
                   token_type=TokenType.SYMBOL,
                   value="{",
                   span=Span(1, 10)
               ),
               Token(
                   token_type=TokenType.IDENTIFIER,
                   value="hello",
                   span=Span(2, 4)
               ),
               Token(
                   token_type=TokenType.KEYWORD,
                   value="self",
                   span=Span(2, 10)
               ),
               Token(
                   token_type=TokenType.SYMBOL,
                   value="}",
                   span=Span(3, 0)
               )
           ]
