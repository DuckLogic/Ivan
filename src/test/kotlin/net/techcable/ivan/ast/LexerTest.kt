package net.techcable.ivan.ast

import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test

class LexerTest {
    @Test
    fun testLexDoc() {
        assertEquals(
            listOf(
                Token(
                    span = Span(1, 0),
                    tokenType = TokenType.DocComment,
                    value = " * This is\n * multiline doc\n * comment\n"
                ),
                Token(
                    span = Span(6, 0),
                    tokenType = TokenType.Function,
                    value = "fun"
                ),
                Token(
                    span = Span(6, 4),
                    value = "hello",
                    tokenType = TokenType.Identifier
                )
            ),
            lex("""
                /**
                 * This is
                 * multiline doc
                 * comment
                 */
                fun hello
            """.trimIndent())
        )
    }
    @Test
    fun testLexKeywords() {
        assertEquals(listOf(Token(
            span = Span(line = 1, column = 0),
            tokenType = TokenType.Interface,
            value = "interface"
        )), lex("interface"))
        assertEquals(listOf(
            Token(
                span = Span(line = 1, column = 0),
                tokenType = TokenType.Function,
                value = "fun"
            ),
            Token(
                span = Span(line = 1, column = 4),
                tokenType = TokenType.Interface,
                value = "interface"
            )
        ), lex("fun interface"))
    }
    @Test
    fun testLexLines() {
        assertEquals(
            listOf(
                Token(
                    tokenType = TokenType.Interface,
                    value = "interface",
                    span = Span(1, 0)
                ),
                Token(
                    tokenType = TokenType.OpenBracket,
                    value = "{",
                    span = Span(1, 10)
                ),
                Token(
                    tokenType = TokenType.Identifier,
                    value = "hello",
                    span = Span(2, 4)
                ),
                Token(
                    tokenType = TokenType.Self,
                    value = "self",
                    span = Span(2, 10)
                ),
                Token(
                    tokenType = TokenType.CloseBracket,
                    value = "}",
                    span = Span(3, 0)
                )
            ),
            lex("interface {\n" +
                    "    hello self\n" +
                    "}")
        )
    }
}