package net.techcable.ivan.ast

import net.techcable.ivan.ast.TokenType.*
import kotlin.math.min

data class Span(
    val line: Int,
    val column: Int
)

data class Token(
    val tokenType: TokenType,
    val value: String,
    val span: Span
)

enum class TokenType(val text: String?) {
    Identifier(null),
    DocComment(null),

    // Symbols
    OpenBracket("{"),
    CloseBracket("}"),
    Colon(":"),
    Semicolon(";"),
    Comma(","),
    And("&"),
    Star("*"),
    OpenParen("("),
    CloseParen(")"),

    // Keywords
    SelfType("Self"),
    Self("self"),
    Interface("interface"),
    Function("fun"),
    Raw("raw"),
    Mut("mut"),
    Own("own"),
    Opaque("opaque"),
    Type("type"),
}

val keywordMap: Map<String, TokenType> = HashMap<String, TokenType>().apply {
    for (token in values()) {
        val text = token.text ?: continue
        assert(text !in this) {
            "Duplicate tokens for ${text}: ${this[text]} and $token"
        }
        this[text] = token // TODO: Duplicate checks
    }
}

fun lex(text: String): List<Token> {
    val lexer = Lexer(text)
    val result = ArrayList<Token>(text.length / 8)
    lexLoop@ while (lexer.peek() != null) {
        val c = lexer.peek()!!
        result.add(
            when (c) {
                '{' -> lexer.expectToken(OpenBracket)
                '}' -> lexer.expectToken(CloseBracket)
                ':' -> lexer.expectToken(Colon)
                ';' -> lexer.expectToken(Semicolon)
                ',' -> lexer.expectToken(Comma)
                '&' -> lexer.expectToken(And)
                '*' -> lexer.expectToken(Star)
                '(' -> lexer.expectToken(OpenParen)
                ')' -> lexer.expectToken(CloseParen)
                '/' -> {
                    when (lexer.peek(1)) {
                        '/' -> {
                            // Skip till end of line
                            while (lexer.index < lexer.text.length &&
                                lexer.text[lexer.index] != '\n'
                            ) {
                                lexer.pop()
                            }
                            continue@lexLoop
                        }
                        '*' -> {
                            if (lexer.peek(2) != '*') {
                                throw ParseException(
                                    "Block comments are unsupported",
                                    lexer.span()
                                )
                            }
                            val startSpan = lexer.span()
                            lexer.skipText("/**\n")
                            val closeIndex = lexer.text.indexOf(
                                " */", // NOTE: We require proper formatting
                                startIndex = lexer.index
                            )
                            if (closeIndex < 0) {
                                throw ParseException(
                                    "Unable to find end of comment",
                                    startSpan
                                )
                            } else {
                                val commentText = lexer.text.substring(
                                    lexer.index, closeIndex
                                )
                                lexer.skipText(commentText)
                                lexer.skipText(" */")
                                Token(
                                    tokenType = DocComment,
                                    value = commentText,
                                    span = startSpan
                                )
                            }
                        }
                        else -> throw ParseException(lexer.span())
                    }
                }
                else -> {
                    // Ignore whitespace
                    if (c.isWhitespace()) {
                        lexer.pop()
                        continue@lexLoop
                    }
                    val startSpan = lexer.span()
                    val ident = lexer.parseIdentifier()
                    val keyword = keywordMap[ident]
                    if (keyword != null) {
                        Token(
                            tokenType = keyword,
                            value = keyword.text!!,
                            span = startSpan
                        )
                    } else {
                        Token(
                            tokenType = Identifier,
                            value = ident,
                            span = startSpan
                        )
                    }
                }
            }
        )
    }
    return result
}

private class Lexer(val text: String) {
    var index = 0
        private set

    fun peek(ahead: Int = 0): Char? {
        if (this.index + ahead >= this.text.length) return null
        return this.text[this.index + ahead]
    }

    fun pop(): Char {
        if (this.index >= this.text.length) {
            throw ParseException("Unexpected EOF", this.span())
        }
        return this.text[this.index++]
    }

    fun expectToken(tokenType: TokenType): Token {
        val tokenText = tokenType.text
            ?: throw IllegalArgumentException("Expected token w/ static text: $tokenType")
        val span = this.span()
        this.skipText(tokenText)
        return Token(tokenType, tokenText, span)
    }

    fun skipText(text: String) {
        if (this.text.regionMatches(this.index, text, 0, text.length)) {
            this.index += text.length
        } else {
            val actual = this.text.substring(
                this.index, min(
                    this.index + text.length,
                    this.text.length
                )
            )
            throw ParseException("Expected $text but got $actual", span())
        }
    }

    fun parseIdentifier(): String {
        val startIndex = this.index
        val start = this.peek()
        if (start == null || !start.isJavaIdentifierStart()) {
            throw ParseException("Expected an identifier", this.span())
        }
        do {
            this.index += 1
        } while (this.peek()?.isJavaIdentifierPart() == true)
        return this.text.substring(startIndex, this.index)
    }

    private var cachedLine = -1
    private var lineStart = 0
    private var lineEnd = this.text.indexOf('\n').let { end ->
        if (end >= 0) end else this.text.length
    }
    fun span(): Span {
        if (cachedLine > 0 && this.index <= this.lineEnd) {
            return Span(
                line = this.cachedLine,
                column = this.index - this.lineStart
            )
        }
        // Fallback to compute
        var line = if (this.cachedLine > 0) this.cachedLine else 1
        var index = this.lineStart
        check(index in 0..this.index)
        while (index < this.index) {
            if (this.text[index] == '\n') {
                line += 1
                lineStart = lineEnd + 1
                val end = this.text.indexOf('\n', index + 1)
                lineEnd = if (end >= 0) end else this.text.length
            }
            index += 1
        }
        check(index >= lineStart && index <= lineEnd)
        this.cachedLine = line
        return Span(
            line = line,
            column = index - lineStart
        )
    }
}

class ParseException(msg: String, val span: Span) : RuntimeException(msg) {
    constructor(span: Span) : this("Unexpected text", span)
}