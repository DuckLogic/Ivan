package net.techcable.ivan.ast

import net.techcable.ivan.*
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class ParserTest {
    @Test
    fun testParseFunc() {
        assertEquals(
            FunctionDef(
                name = "hello",
                docString = DocString(
                    listOf("Does some things", "", "On occasion"),
                    span = Span(1, 0)
                ),
                args = listOf(
                    FunctionArg("i", PrimitiveType.INT),
                    FunctionArg("floating", PrimitiveType.DOUBLE)
                ),
                returnType = PrimitiveType.UNIT,
                span = Span(6, 4)
            ),
            parseItem(Parser.fromString("""
                /**
                 * Does some things
                 *
                 * On occasion
                 */
                fun hello(i: int, floating: double);
            """.trimIndent()))
        )
    }
    @Test
    fun testParseBasic() {
        val basicText = String(ParserTest::class.java.classLoader
            .getResourceAsStream("basic.ivan")!!
            .readBytes(), Charsets.UTF_8)
        assertEquals(
            listOf(
                InterfaceDef(
                    name = "Basic",
                    docString = DocString(
                        listOf("This is a basic example of an ivan interface."),
                        Span(1, 0)
                    ),
                    methods = listOf(
                        FunctionDef(
                            name = "noArgs",
                            docString = null,
                            args = listOf(),
                            returnType = FixedIntegerType(bits = 64, signed = true),
                            span = Span(5, 8)
                        ),
                        FunctionDef(
                            name = "findInBytes",
                            docString = DocString(
                                lines = listOf(
                                    "Find the value by searching through the specified bytes.",
                                    "",
                                    "Bytes is a const '&' pointer, so you're expected not to mutate it.",
                                    "It must be valid for the duration of the call.",
                                    "",
                                    "The output (if any) is placed in `result`.",
                                    "It's a `&mut` pointer, so it's expected to be mutable",
                                    "and have no-aliasing for the duration of the call."
                                ),
                                span = Span(6, 4)
                            ),
                            args = listOf(
                                FunctionArg("bytes", ReferenceType(
                                    target = PrimitiveType.BYTE,
                                    kind = ReferenceKind.Immutable
                                )),
                                FunctionArg("start", PrimitiveType.USIZE),
                                FunctionArg("result", ReferenceType(
                                    target = PrimitiveType.USIZE,
                                    kind = ReferenceKind.Mutable
                                ))
                            ),
                            returnType = PrimitiveType.BOOLEAN,
                            span = Span(16, 8)
                        ),
                        FunctionDef(
                            name = "complexLifetime",
                            docString = null,
                            args = listOf(),
                            returnType = ReferenceType(
                                target = PrimitiveType.BYTE,
                                kind = ReferenceKind.Raw
                            ),
                            span = Span(19, 8)
                        )
                    ),
                    span = Span(4, 10)
                ),
                InterfaceDef(
                    name = "Other",
                    docString = DocString(
                        lines = listOf(
                            "Here is another interface",
                            "",
                            "You can have multiple ones defined"
                        ),
                        span = Span(22, 0)
                    ),
                    methods = listOf(
                        FunctionDef(
                            name = "test",
                            docString = null,
                            args = listOf(FunctionArg(
                                "d", PrimitiveType.DOUBLE
                            )),
                            returnType = PrimitiveType.UNIT,
                            span = Span(28, 8)
                        )
                    ),
                    span = Span(27, 10)
                ),
                InterfaceDef(
                    name = "NoMethods",
                    docString = null,
                    methods = listOf(),
                    span = Span(32, 10)
                ),
                OpaqueTypeDef(
                    name = "Example",
                    docString = DocString(
                        listOf("A type defined elsewhere in user code"),
                        Span(36, 0)
                    ),
                    span = Span(39, 12)
                ),
                FunctionDef(
                    name = "topLevel",
                    docString = null,
                    args = listOf(FunctionArg(
                        "e",
                        UnresolvedType("Example", usageSpan = Span(41, 16))
                    )),
                    returnType = PrimitiveType.UNIT,
                    span = Span(41, 4)
                )
            ),
            parseAll(Parser.fromString(basicText))
        )
    }
}