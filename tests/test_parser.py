from ivan import types
from ivan.ast import FunctionDef, DocString, InterfaceDef, FunctionArg, OpaqueTypeDef
from ivan.ast.parser import parse_function_def, parse_item, parse_all, Parser
from ivan.ast.lexer import Span

from pathlib import Path
import importlib.resources

from ivan.types import ReferenceType, ReferenceKind, UnresolvedTypeRef, FixedIntegerType


def test_parse_func():
    assert parse_item(Parser.parse_str(
"""/**
     * Does some things
     *
     * On occasion
     */
    fun hello(i: int, floating: double);
""")) == FunctionDef(
        name="hello",
        doc_string=DocString(
            ["Does some things", "", "On occasion"],
            span=Span(1, 0)
        ),
        args=[
            FunctionArg("i", types.INT),
            FunctionArg("floating", types.DOUBLE)
        ],
        return_type=types.UNIT,
        span=Span(6, 8)
    )


def test_parse_basic():
    with open(Path(Path(__file__).parent, "basic.ivan"), "rt") as f:
        basic_text = f.read()
    parsed = parse_all(Parser.parse_str(basic_text))
    expected = [
        InterfaceDef(
            name="Basic",
            doc_string=DocString(
                ["This is a basic example of an ivan interface."],
                span=Span(1, 0)
            ),
            methods=[
                FunctionDef(
                    name="noArgs",
                    doc_string=None,
                    args=[],
                    return_type=FixedIntegerType(bits=64, signed=True),
                    span=Span(5, 8)
                ),
                FunctionDef(
                    name="findInBytes",
                    doc_string=DocString(
                        ["Find the value by searching through the specified bytes.",
                         "",
                         "Bytes is a const '&' pointer, so you're expected not to mutate it.",
                         "It must be valid for the duration of the call.",
                         "",
                         "The output (if any) is placed in `result`.",
                         "It's a `&mut` pointer, so it's expected to be mutable",
                         "and have no-aliasing for the duration of the call."],
                        span=Span(6, 4)
                    ),
                    args=[
                        FunctionArg("bytes", ReferenceType(
                            target=types.BYTE,
                            kind=ReferenceKind.IMMUTABLE
                        )),
                        FunctionArg("start", types.USIZE),
                        FunctionArg("result", ReferenceType(
                            target=types.USIZE,
                            kind=ReferenceKind.MUTABLE
                        ))
                    ],
                    return_type=types.BOOLEAN,
                    span=Span(16, 8)
                ),
                FunctionDef(
                    name="complexLifetime",
                    doc_string=None,
                    args=[],
                    return_type=ReferenceType(
                        types.BYTE,
                        kind=ReferenceKind.RAW
                    ),
                    span=Span(19, 8)
                ),
            ],
            span=Span(4, 10)
        ),
        InterfaceDef(
            name="Other",
            doc_string=DocString(
                ["Here is another interface",
                 "",
                 "You can have multiple ones defined"],
                Span(22, 0)
            ),
            methods=[
                FunctionDef(
                    name="test",
                    doc_string=None,
                    args=[
                        FunctionArg("d", types.DOUBLE)
                    ],
                    return_type=types.UNIT,
                    span=Span(28, 8)
                )
            ],
            span=Span(27, 10)
        ),
        InterfaceDef(
            name="NoMethods",
            doc_string=None,
            methods=[],
            span=Span(32, 10)
        ),
        OpaqueTypeDef(
            name="Example",
            doc_string=DocString(
                ["A type defined elsewhere in user code"],
                span=Span(36, 0)
            ),
            span=Span(39, 12)
        ),
        FunctionDef(
            name="topLevel",
            doc_string=None,
            args=[
                FunctionArg("e", UnresolvedTypeRef(
                    "Example",
                    usage_span=Span(41, 16)
                ))
            ],
            return_type=types.UNIT,
            span=Span(41, 4)
        )
    ]
    assert parsed == expected
