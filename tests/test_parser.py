from pathlib import Path

from ivan.ast import FunctionDeclaration, DocString, InterfaceDef, FunctionArg, OpaqueTypeDef, FunctionSignature, \
    Annotation, IvanModule, StructDef, FieldDef, SimpleArgument
from ivan.ast.lexer import Span
from ivan.ast.parser import parse_item, parse_module, Parser, parse_annotation, parse_type
from ivan.ast.types import ReferenceKind, OptionalTypeRef, ReferenceTypeRef, NamedTypeRef


def test_parse_types():
    assert parse_type(Parser.parse_str("opt &byte")) == OptionalTypeRef(
        usage_span=Span(1, 0),
        inner=ReferenceTypeRef(
            usage_span=Span(1, 4),
            kind=ReferenceKind.IMMUTABLE,
            inner=NamedTypeRef(Span(1, 5), 'byte')
        )
    )


def test_parse_struct():
    assert parse_item(Parser.parse_str("""struct Vector {
    field x: double;
    field y: double;
    field z: double;
}""")) == StructDef(
        name="Vector",
        span=Span(1, 7),
        fields={
            "x": FieldDef(
                name="x",
                span=Span(2, 10),
                static_type=NamedTypeRef(Span(2, 13), 'double'),
                doc_string=None,
                annotations=[]
            ),
            "y": FieldDef(
                name="y",
                span=Span(3, 10),
                static_type=NamedTypeRef(Span(3, 13), 'double'),
                doc_string=None,
                annotations=[]
            ),
            "z": FieldDef(
                name="z",
                span=Span(4, 10),
                static_type=NamedTypeRef(Span(4, 13), 'double'),
                doc_string=None,
                annotations=[]
            )
        },
        annotations=[],
        doc_string=None
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
                SimpleArgument("i", NamedTypeRef(Span(6, 17), 'int')),
                SimpleArgument("floating", NamedTypeRef(Span(6, 32), 'double'))
            ],
            return_type=NamedTypeRef(Span(6, 39), 'unit'),
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
            members={
                "noArgs": FunctionDeclaration(
                    name="noArgs",
                    doc_string=None,
                    signature=FunctionSignature(
                        args=[],
                        return_type=NamedTypeRef(Span(6, 18), 'i64'),
                    ),
                    annotations=[],
                    span=Span(6, 8),
                    body=None
                ),
                "findInBytes": FunctionDeclaration(
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
                            SimpleArgument("bytes", ReferenceTypeRef(
                                usage_span=Span(17, 27),
                                inner=NamedTypeRef(Span(17, 28), 'byte'),
                                kind=ReferenceKind.IMMUTABLE
                            )),
                            SimpleArgument("start", NamedTypeRef(
                                Span(17, 41), 'usize'
                            )),
                            SimpleArgument("result", ReferenceTypeRef(
                                usage_span=Span(17, 56),
                                inner=NamedTypeRef(Span(17, 61), 'usize'),
                                kind=ReferenceKind.MUTABLE
                            ))
                        ],
                        return_type=NamedTypeRef(Span(17, 69), 'bool'),
                    ),
                    span=Span(17, 8),
                    body=None
                ),
                "complexLifetime": FunctionDeclaration(
                    name="complexLifetime",
                    doc_string=None,
                    signature=FunctionSignature(
                        args=[],
                        return_type=ReferenceTypeRef(
                            usage_span=Span(21, 27),
                            inner=NamedTypeRef(Span(21, 32), 'byte'),
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
            },
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
            members={
                "test": FunctionDeclaration(
                    name="test",
                    doc_string=None,
                    signature=FunctionSignature(
                        args=[
                            SimpleArgument("d", NamedTypeRef(
                                Span(31, 16), 'double'
                            ))
                        ],
                        return_type=NamedTypeRef(Span(31, 23), 'unit'),
                    ),
                    span=Span(31, 8),
                    annotations=[],
                    body=None
                )
            },
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
            members={},
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
                    SimpleArgument("e", NamedTypeRef(
                        name="Example",
                        usage_span=Span(44, 16)
                    ))
                ],
                return_type=NamedTypeRef(Span(44, 24), 'unit'),
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
