import dataclasses
import re
from typing import List, Optional, Set

from ivan import types
from ivan.ast import lexer, DocString, OpaqueTypeDef, InterfaceDef, FunctionDeclaration, FunctionArg, PrimaryItem, \
    FunctionSignature, Annotation, AnnotationValue, IvanModule, FunctionBody
from ivan.ast.lexer import Token, Span, ParseException, TokenType
from ivan.types import ReferenceKind, ReferenceType, PrimitiveType, FixedIntegerType, IvanType
from ivan.types.context import UnresolvedTypeRef


class Parser:
    tokens: List[Token]
    last_span: Span
    index: int

    def __init__(self, tokens: List[Token]):
        if len(tokens) == 0:
            raise ParseException("Empty tokens", Span(0, 0))
        self.tokens = tokens
        # TODO: Get an actual Span that points at EOF
        self.last_span = tokens[-1].span
        self.index = 0

    @property
    def current_span(self) -> Span:
        try:
            return self.tokens[self.index].span
        except IndexError:
            return self.last_span

    def look(self, ahead: int) -> Optional[Token]:
        assert ahead >= 0
        try:
            return self.tokens[self.index + ahead]
        except IndexError:
            return None

    def peek(self) -> Optional[Token]:
        try:
            return self.tokens[self.index]
        except IndexError:
            return None

    def pop(self) -> Token:
        try:
            t = self.tokens[self.index]
            self.index += 1
            return t
        except IndexError:
            raise ParseException("Unexpected EOF", self.last_span) from None

    def expect_symbol(self, symbol: str) -> Token:
        assert symbol in lexer.VALID_SYMBOLS
        actual = self.peek()
        if actual is not None and actual.value == symbol \
                and actual.value == symbol:
            self.index += 1
            return actual
        else:
            actual_value = actual.value if actual is not None else "EOF"
            raise ParseException(
                f"Expected symbol ${symbol!r} but got ${actual_value}",
                self.current_span
            )

    def expect_keyword(self, keyword: str) -> Token:
        assert keyword in lexer.VALID_KEYWORDS
        actual = self.peek()
        if actual is None or actual.value != keyword \
                or actual.token_type != TokenType.KEYWORD:
            actual_value = actual.value if actual is not None else "EOF"
            raise ParseException(
                f"Expected keyword ${keyword} but got ${actual_value}",
                self.current_span
            )
        else:
            self.index += 1
            return actual

    def expect_identifier(self) -> str:
        actual = self.peek()
        if actual is not None and actual.token_type == TokenType.IDENTIFIER:
            self.index += 1
            return actual.value
        else:
            raise ParseException("Expected identifier", self.current_span)

    @staticmethod
    def parse_str(s: str) -> "Parser":
        """Create a parser from the specified string,

        implicitly running it through the lexer."""
        # TODO: Handle empty tokens
        return Parser(list(lexer.lex_all(s)))

    def __repr__(self):
        return f"Parser(index={self.index}, tokens={self.tokens})"

    def __len__(self):
        # NOTE: Guard against negative len just in case
        return max(0, len(self.tokens) - self.index)


ALLOWED_FUNCTION_MODIFIERS = {"default", }
ALLOWED_TYPE_MODIFIERS = set()


@dataclasses.dataclass
class ItemHeader:
    """The data that typically comes before an item"""
    span: Span
    doc_string: Optional[DocString] = None
    annotations: List[Annotation] = dataclasses.field(default_factory=list)
    modifiers: Set[str] = dataclasses.field(default_factory=set)

    def _check_modifiers(self, allowed: Set[str], span: Span):
        unexpected = self.modifiers - allowed
        if unexpected:
            raise ParseException(f"Unexpected modifiers: {unexpected}", span)

    def expect_type_header(self, span: Span):
        self._check_modifiers(ALLOWED_TYPE_MODIFIERS, span)

    def expect_function_definition(self, span: Span):
        self._check_modifiers(ALLOWED_FUNCTION_MODIFIERS, span)


def parse_doc_string(parser: Parser) -> Optional[DocString]:
    token = parser.peek()
    if token is None or token.token_type != TokenType.DOC_COMMENT:
        return None
    parser.pop()
    start_line = token.span.line
    doc_lines = []
    for (offset, line) in enumerate(token.value.split('\n')):
        trimmed = line.strip()
        if len(trimmed) == 0:
            continue  # Just ignore for now
        if trimmed == "*":
            doc_lines.append("")
        elif trimmed.startswith("* "):
            doc_lines.append(trimmed[len("* "):])
        else:
            raise ParseException(
                f"Expected doc line to start with `* ` (around {start_line + offset})",
                token.span  # TODO: More accurate span
            )
    return DocString(lines=doc_lines, span=token.span)


def parse_annotation_value(parser: Parser) -> AnnotationValue:
    token = parser.pop()
    if token.token_type == TokenType.STRING_LITERAL:
        return token.value
    elif token.is_keyword('true'):
        return True
    elif token.is_keyword('false'):
        return False
    else:
        raise ParseException("Expected annotation value", token.span)


def parse_annotation(parser: Parser) -> Annotation:
    parser.expect_symbol('@')
    start_span = parser.current_span
    name = parser.expect_identifier()
    if parser and parser.peek().is_symbol('('):
        values = {}
        parser.expect_symbol('(')
        while True:
            token = parser.peek()
            if token is None:
                raise ParseException(f"Expected closing paren for annotation", start_span)
            elif token.token_type == TokenType.IDENTIFIER:
                value_name = token.value
                parser.pop()
                if value_name in values:
                    raise ParseException(
                        f"Duplicate annotation values for {value_name!r} in @{name}",
                        token.span
                    )
                parser.expect_symbol('=')
                values[value_name] = parse_annotation_value(parser)
            elif token.is_symbol(','):
                parser.pop()
                continue
            elif token.is_symbol(')'):
                parser.pop()
                break
            else:
                raise ParseException(f"Unexpected token {token.value!r}", token.span)
        return Annotation(name=name, values=values, span=start_span)
    else:
        return Annotation(name, values=None, span=start_span)


def parse_opaque_type(parser: Parser, header: ItemHeader) -> OpaqueTypeDef:
    header.expect_type_header(parser.current_span)
    parser.expect_keyword("opaque")
    parser.expect_keyword("type")
    start_span = parser.current_span
    name = parser.expect_identifier()
    parser.expect_symbol(';')
    return OpaqueTypeDef(
        name=name,
        span=start_span,
        doc_string=header.doc_string,
        annotations=header.annotations
    )


def parse_interface(parser: Parser, header: ItemHeader) -> InterfaceDef:
    header.expect_type_header(parser.current_span)
    parser.expect_keyword("interface")
    start_span = parser.current_span
    name = parser.expect_identifier()
    parser.expect_symbol('{')
    methods = []
    pending_header: Optional[ItemHeader] = None
    while True:
        token = parser.peek()
        if token is None:
            raise ParseException(f"Expected closing brace for {name}", start_span)
        elif token.token_type == TokenType.DOC_COMMENT \
                or token.is_symbol('@')\
                or token.is_keyword('default'):
            if pending_header is not None:
                raise ParseException(
                    f"Already encountered header @ {pending_header.span.line}",
                    token.span
                )
            pending_header = parse_item_header(parser)
            assert pending_header is not None
        elif token.is_keyword('fun'):
            if pending_header is None:
                pending_header = ItemHeader(span=parser.current_span)
            methods.append(parse_function_declaration(parser, pending_header))
            pending_header = None
        elif token.is_symbol('}'):
            parser.pop()
            # End of interface
            if pending_header is not None:
                raise ParseException("Unexpected item header", pending_header.span)
            return InterfaceDef(
                name=name,
                methods=methods,
                doc_string=header.doc_string,
                span=start_span,
                annotations=header.annotations
            )
        else:
            raise ParseException("Unexpected token", token.span)


def parse_function_signature(parser: Parser) -> FunctionSignature:
    start_span = parser.current_span
    parser.expect_symbol('(')
    args = []
    while True:
        token = parser.peek()
        if token is None:
            raise ParseException(f"Expected closing brace", start_span)
        elif token.token_type == TokenType.IDENTIFIER:
            arg_name = parser.expect_identifier()
            parser.expect_symbol(':')
            arg_type = parse_type(parser)
            args.append(FunctionArg(arg_name=arg_name, arg_type=arg_type))
            trailing = parser.pop()
            if trailing.is_symbol(','):
                continue  # continue parsing args
            elif trailing.is_symbol(')'):
                break  # we're done
            else:
                raise ParseException(
                    f"Unexpected token {trailing.value!r}",
                    trailing.span
                )
        elif token.is_symbol(')'):
            parser.pop()
            break  # stop parsing args
        else:
            raise ParseException(f"Unexpected token {token.value!r}", token.span)
    t = parser.peek()
    if t.is_symbol(';'):
        return_type = types.UNIT
    elif t.is_symbol(':'):
        parser.expect_symbol(':')
        return_type = parse_type(parser)
    else:
        raise ParseException("Unexpected token", t.span)
    return FunctionSignature(return_type=return_type, args=args)


def parse_function_body(parser: Parser, is_default: bool) -> FunctionBody:
    start_body_span = parser.current_span
    parser.expect_symbol('{')
    statements = []
    while True:
        token = parser.peek()
        if not token:
            raise ParseException(
                "Expected closing brace for func body",
                span=start_body_span
            )
        elif token.is_symbol('}'):
            parser.pop()
            return FunctionBody(
                statements=statements,
                span=start_body_span,
                default=is_default
            )
        else:
            statements.append(parse_statement(parser))


def parse_function_declaration(parser: Parser, header: ItemHeader) -> FunctionDeclaration:
    header.expect_function_definition(parser.current_span)
    parser.expect_keyword("fun")
    start_span = parser.current_span
    func_name = parser.expect_identifier()
    signature = parse_function_signature(parser)
    is_default = 'default' in header.modifiers
    if parser.peek().is_symbol(';'):
        parser.pop()
        body = None
    elif parser.peek().is_symbol('{'):
        body = parse_function_body(parser, is_default=True)
    else:
        raise ParseException(f"Unexpected symbol", parser.current_span)
    if is_default and body is None:
        raise ParseException(f"Default function mast have body!", start_span)
    return FunctionDeclaration(
        name=func_name,
        span=start_span,
        doc_string=header.doc_string,
        signature=signature,
        annotations=header.annotations,
        body=body
    )


FIXED_INTEGER_PATTERN = re.compile("([iu])(8|16|32|64)")


def parse_type(parser: Parser) -> IvanType:
    try:
        first_token = parser.pop()
    except ParseException:
        raise ParseException(
            "Unexpected EOF: Expected type",
            parser.last_span
        ) from None
    if first_token.token_type == TokenType.IDENTIFIER:
        type_name = first_token.value
    elif first_token.is_symbol('&'):
        # We have a reference!
        ref_token = parser.peek()
        if ref_token is None:
            raise ParseException("Unexpected EOF", parser.current_span)
        if ref_token.is_keyword('raw'):
            ref_kind = ReferenceKind.RAW
        elif ref_token.is_keyword('own'):
            ref_kind = ReferenceKind.OWNED
        elif ref_token.is_keyword('mut'):
            ref_kind = ReferenceKind.MUTABLE
        else:
            ref_kind = ReferenceKind.IMMUTABLE
        if ref_kind != ReferenceKind.IMMUTABLE:
            parser.pop()  # We need to eat the ref_kind token!
        return ReferenceType(
            target=parse_type(parser),
            kind=ref_kind,
            optional=False  # Handled by a seperate rule
        )
    elif first_token.is_keyword('opt'):
        start_span = parser.current_span
        inner_type = parse_type(parser)
        if isinstance(inner_type, ReferenceType):
            assert not inner_type.optional
            # Rebuild
            return ReferenceType(
                target=inner_type.target,
                kind=inner_type.kind,
                optional=True
            )
        else:
            raise ParseException("Can only have optional references", start_span)
    else:
        raise ParseException(
            f"Unexpected token: {first_token.value!r}",
            first_token.span
        )
    primitive = PrimitiveType.try_parse(type_name)
    if primitive is not None:
        return primitive
    int_match = FIXED_INTEGER_PATTERN.match(type_name)
    if int_match is not None:
        if int_match.group(1) == 'i':
            signed = True
        elif int_match.group(1) == 'u':
            signed = False
        else:
            raise AssertionError(int_match.group(1))
        return FixedIntegerType(
            bits=int(int_match.group(2)),
            signed=signed
        )
    return UnresolvedTypeRef(type_name, usage_span=first_token.span)


def parse_item_header(parser: Parser) -> ItemHeader:
    header = ItemHeader(span=parser.current_span)
    if parser and parser.peek().token_type == TokenType.DOC_COMMENT:
        doc_string = parse_doc_string(parser)
        assert doc_string is not None
        header.doc_string = doc_string
    while parser and parser.peek().is_symbol('@'):
        header.annotations.append(parse_annotation(parser))
    if parser and parser.peek().is_keyword('default'):
        parser.pop()
        header.is_default = True
    return header


def parse_item(parser: Parser) -> PrimaryItem:
    header = parse_item_header(parser)
    token = parser.peek()
    if token is None:
        raise ParseException("Unexpected EOF: Expected item", parser.current_span)
    elif token.is_keyword('fun'):
        return parse_function_declaration(parser, header)
    elif token.is_keyword('interface'):
        return parse_interface(parser, header)
    elif token.is_keyword('opaque'):
        return parse_opaque_type(parser, header)
    else:
        raise ParseException(f"Expected item but got {token.value!r}", token.span)


def parse_module(parser: Parser, name: str) -> IvanModule:
    items = []
    while parser.peek() is not None:
        items.append(parse_item(parser))
    return IvanModule(
        items=items,
        name=name
    )


# Must come at end?
from ivan.ast.parser.expr import parse_statement
