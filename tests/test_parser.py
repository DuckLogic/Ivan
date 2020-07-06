from pathlib import Path

from ivan import types
from ivan.ast import FunctionDeclaration, DocString, InterfaceDef, FunctionArg, OpaqueTypeDef, FunctionSignature, \
    Annotation, IvanModule
from ivan.ast.lexer import Span
from ivan.ast.parser import parse_item, parse_module, Parser, parse_annotation, parse_type
from ivan.types import ReferenceType, ReferenceKind, FixedIntegerType
from ivan.types.context import UnresolvedTypeRef


def test_parse_types():
    assert parse_type(Parser.parse_str("opt &byte")) == ReferenceType(
        kind=ReferenceKind.IMMUTABLE,
        target=types.BYTE,
        optional=True
    )


def test_parse_func():
    assert parse_item(Parser.parse_str(
        """/**
     * Does some things
     *
     * On occasion
     */
    fun hello(i: int, floating: double);
""")) == FunctionDeclaration(
        name="hello",
        doc_string=DocString(
            ["Does some things", "", "On occasion"],
            span=Span(1, 0)
        ),
        signature=FunctionSignature(
            args=[
                FunctionArg("i", types.INT),
                FunctionArg("floating", types.DOUBLE)
            ],
            return_type=types.UNIT,
        ),
        annotations=[],
        span=Span(6, 8),
        body=None
    )


def test_parse_annotation():
    assert parse_annotation(Parser.parse_str("@Example")) == Annotation(
        name="Example",
        values=None,
        span=Span(1, 1)
    )
    assert parse_annotation(Parser.parse_str('@Test(key="value", b=false)')) == Annotation(
        name="Test",
        values={
            "key": "value",
            "b": False
        },
        span=Span(1, 1)
    )


def test_parse_basic():
    with open(Path(Path(__file__).parent, "basic.ivan"), "rt") as f:
        basic_text = f.read()
    parsed = parse_module(Parser.parse_str(basic_text), name="ivan.basic")
    expected_items = [
        InterfaceDef(
            name="Basic",
            doc_string=DocString(
                ["This is a basic example of an ivan interface."],
                span=Span(1, 0)
            ),
            methods=[
                FunctionDeclaration(
                    name="noArgs",
                    doc_string=None,
                    signature=FunctionSignature(
                        args=[],
                        return_type=FixedIntegerType(bits=64, signed=True),
                    ),
                    annotations=[],
                    span=Span(6, 8),
                    body=None
                ),
                FunctionDeclaration(
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
                        span=Span(7, 4),
                    ),
                    annotations=[],
                    signature=FunctionSignature(
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
                    ),
                    span=Span(17, 8),
                    body=None
                ),
                FunctionDeclaration(
                    name="complexLifetime",
                    doc_string=None,
                    signature=FunctionSignature(
                        args=[],
                        return_type=ReferenceType(
                            types.BYTE,
                            kind=ReferenceKind.RAW
                        ),
                    ),
                    annotations=[
                        Annotation(
                            name="NestedAnnotation",
                            values=None,
                            span=Span(20, 5)
                        )
                    ],
                    span=Span(21, 8),
                    body=None
                ),
            ],
            span=Span(5, 10),
            annotations=[
                Annotation(
                    name="GenerateWrappers",
                    values={
                        "prefix": "basic",
                        "include_doc": False
                    },
                    span=Span(4, 1),
                )
            ]
        ),
        InterfaceDef(
            name="Other",
            doc_string=DocString(
                ["Here is another interface",
                 "",
                 "You can have multiple ones defined"],
                Span(24, 0)
            ),
            methods=[
                FunctionDeclaration(
                    name="test",
                    doc_string=None,
                    signature=FunctionSignature(
                        args=[
                            FunctionArg("d", types.DOUBLE)
                        ],
                        return_type=types.UNIT,
                    ),
                    span=Span(31, 8),
                    annotations=[],
                    body=None
                )
            ],
            span=Span(30, 10),
            annotations=[
                Annotation(
                    name="GenerateWrappers",
                    values={
                        "prefix": "other",
                        "indirect_vtable": False
                    },
                    span=Span(29, 1)
                )
            ]
        ),
        InterfaceDef(
            name="NoMethods",
            doc_string=None,
            methods=[],
            span=Span(35, 10),
            annotations=[]
        ),
        OpaqueTypeDef(
            name="Example",
            doc_string=DocString(
                ["A type defined elsewhere in user code"],
                span=Span(39, 0)
            ),
            span=Span(42, 12),
            annotations=[]
        ),
        FunctionDeclaration(
            name="topLevel",
            doc_string=None,
            signature=FunctionSignature(
                args=[
                    FunctionArg("e", UnresolvedTypeRef(
                        "Example",
                        usage_span=Span(44, 16)
                    ))
                ],
                return_type=types.UNIT,
            ),
            span=Span(44, 4),
            annotations=[],
            body=None
        )
    ]
    assert parsed == IvanModule(
        name="ivan.basic",
        items=expected_items
    )
