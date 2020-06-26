package net.techcable.ivan.ast

import net.techcable.ivan.*

class Parser(val tokens: List<Token>) {
    private val lastSpan = tokens.last().span
    init {
        check(tokens.isNotEmpty())
    }
    var index = 0
        private set
    val currentSpan: Span
        get() = this.tokens.getOrNull(this.index)?.span ?: this.lastSpan
    fun peek(): Token? = this.tokens.getOrNull(this.index)
    fun pop(): Token {
        if (this.index >= this.tokens.size) {
            throw ParseException("Unexpected EOF", lastSpan)
        }
        return this.tokens[this.index++]
    }
    inline fun pop(lazyMessage: () -> Any): Token {
        if (this.index >= this.tokens.size) {
            throw ParseException("Unexpected EOF: ${lazyMessage()}", this.currentSpan)
        }
        return this.pop()
    }
    fun expectToken(tokenType: TokenType): Token {
        checkNotNull(tokenType.text)
        val actual = this.pop { "Expected ${tokenType.text}" }
        if (actual.tokenType != tokenType) {
            throw ParseException(
                "Expected ${tokenType.text} but got ${actual.value}",
                actual.span
            )
        }
        return actual
    }
    fun expectIdentifier(): String {
        val actual = this.pop { "Expected identifier" }
        if (actual.tokenType == TokenType.Identifier) {
            return actual.value
        } else {
            throw ParseException("Expected identifier", actual.span)
        }
    }
    companion object {
        /**
         * Create a parser from the specified string,
         * implcicitly running it through the lexer.
         */
        @JvmStatic
        fun fromString(s: String) = Parser(lex(s))
    }
}

fun parseDocString(parser: Parser): DocString? {
    val token = parser.peek()
    if (token?.tokenType != TokenType.DocComment) {
        return null
    }
    parser.pop()
    val startLine = token.span.line
    val docLines = ArrayList<String>()
    for ((offset, line) in token.value.lineSequence().withIndex()) {
        val trimmed = line.trim()
        if (trimmed.isEmpty()) continue // Just ignore for now
        if (trimmed == "*") {
            docLines.add("");
            continue
        }
        if (!trimmed.startsWith("* ")) {
            throw ParseException(
                "Expected doc line to start with `* ` (around ${startLine + offset})",
                token.span // TODO: More accurate span
            )
        }
        docLines.add(trimmed.substring("* ".length))
    }
    return DocString(lines = docLines, span = token.span)
}
fun parseOpaqueType(parser: Parser, docString: DocString?): OpaqueTypeDef {
    parser.expectToken(TokenType.Opaque)
    parser.expectToken(TokenType.Type)
    val startSpan = parser.currentSpan
    val name = parser.expectIdentifier()
    parser.expectToken(TokenType.Semicolon)
    return OpaqueTypeDef(
        name = name,
        span = startSpan,
        docString = docString
    )
}
fun parseInterface(parser: Parser, docString: DocString?): InterfaceDef {
    parser.expectToken(TokenType.Interface)
    val startSpan = parser.currentSpan
    val name = parser.expectIdentifier()
    parser.expectToken(TokenType.OpenBracket)
    val methods = ArrayList<FunctionDef>()
    var pendingComment: DocString? = null
    while (true) {
        val token = parser.peek()
        when (token?.tokenType) {
            null -> {
                throw ParseException(
                    "Expected closing brace for $name",
                    startSpan
                )
            }
            TokenType.DocComment -> {
                if (pendingComment != null) {
                    throw ParseException(
                        "Already encountered doc comment @ ${pendingComment.span.line}",
                        token.span
                    )
                }
                pendingComment = parseDocString(parser)!!
            }
            TokenType.Function -> {
                methods.add(parseFunc(parser, pendingComment))
                pendingComment = null
            }
            TokenType.CloseBracket -> {
                parser.pop()
                if (pendingComment != null) {
                    throw ParseException("Unexpected doc comment", pendingComment.span)
                }
                return InterfaceDef(
                    name = name,
                    methods = methods,
                    docString = docString,
                    span = startSpan
                )
            }
            else -> {
                throw ParseException("Unexpected token", token.span)
            }
        }
    }
}
fun parseFunc(parser: Parser, docString: DocString?): FunctionDef {
    parser.expectToken(TokenType.Function)
    val startSpan = parser.currentSpan
    val funcName = parser.expectIdentifier()
    parser.expectToken(TokenType.OpenParen)
    val args = ArrayList<FunctionArg>()
    argLoop@ while (true) {
        val token = parser.peek()
        when (token?.tokenType) {
            null -> {
                throw ParseException(
                    "Expected closing brace for $funcName",
                    startSpan
                )
            }
            TokenType.Identifier -> {
                val argName = parser.expectIdentifier()
                parser.expectToken(TokenType.Colon)
                val argType = parseType(parser)
                args.add(FunctionArg(name = argName, nativeType = argType))
                val trailing = parser.pop()
                when (trailing.tokenType) {
                    TokenType.Comma -> continue@argLoop
                    TokenType.CloseParen -> break@argLoop
                    else -> {
                        throw ParseException(
                            "Unexpected token: ${trailing.tokenType}",
                            trailing.span
                        )
                    }
                }
            }
            TokenType.CloseParen -> {
                parser.pop()
                break@argLoop
            }
            else -> {
                throw ParseException("Unexpected token ${token.tokenType}", token.span)
            }
        }
    }
    val t = parser.pop()
    val returnType: NativeType
    when (t.tokenType) {
        TokenType.Semicolon -> {
            returnType = PrimitiveType.UNIT
        }
        TokenType.Colon -> {
            returnType = parseType(parser)
            parser.expectToken(TokenType.Semicolon)
        }
        else -> throw ParseException("Unexpected token", t.span)
    }
    return FunctionDef(
        name = funcName,
        args = args,
        span = startSpan,
        returnType = returnType,
        docString = docString
    )
}

val FIXED_INTEGER_PATTERN = Regex("([iu])(8|16|32|64)")
fun parseType(parser: Parser): NativeType {
    val identToken = parser.pop { "Expected type" }
    val typeName = when (identToken.tokenType) {
        TokenType.Identifier -> identToken.value
        TokenType.And -> {
            // We have a reference!
            val kind = when (parser.peek()?.tokenType) {
                TokenType.Raw -> ReferenceKind.Raw
                TokenType.Own -> ReferenceKind.Owned
                TokenType.Mut -> ReferenceKind.Mutable
                else -> ReferenceKind.Immutable
            }
            // We ate a token!
            if (kind != ReferenceKind.Immutable) parser.pop()
            return ReferenceType(
                target = parseType(parser),
                kind = kind
            )
        }
        else -> {
            throw ParseException(
                "Unexpected token: ${identToken.tokenType}",
                identToken.span
            )
        }
    }
    val primitive = PrimitiveType.tryParse(typeName)
    if (primitive != null) return primitive
    val intMatch = FIXED_INTEGER_PATTERN.find(typeName)
    if (intMatch != null) {
        return FixedIntegerType(
            bits = intMatch.groupValues[2].toInt(),
            signed = when (intMatch.groupValues[1]) {
                "i" -> true
                "u" -> false
                else -> throw AssertionError()
            }
        )
    }
    return UnresolvedType(typeName, usageSpan = identToken.span)
}

fun parseItem(parser: Parser, docString: DocString? = null): PrimaryItem {
    val token = parser.peek()
        ?: throw ParseException("Unexpected EOF: Expected item", parser.currentSpan)
    return when (token.tokenType) {
        TokenType.DocComment -> {
            if (docString != null) {
                throw ParseException("Multiple doc comments", token.span)
            }
            return parseItem(parser, docString = parseDocString(parser))
        }
        TokenType.Function -> parseFunc(parser, docString = docString)
        TokenType.Interface -> parseInterface(parser, docString = docString)
        TokenType.Opaque -> parseOpaqueType(parser, docString = docString)
        else -> throw ParseException("Expected item", token.span)
    }
}

fun parseAll(parser: Parser): List<PrimaryItem> {
    val result = ArrayList<PrimaryItem>()
    while (parser.peek() != null) {
        result.add(parseItem(parser))
    }
    return result
}