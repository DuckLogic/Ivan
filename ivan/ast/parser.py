import re
from typing import List, Optional

from ivan import types
from ivan.ast import lexer, DocString, OpaqueTypeDef, InterfaceDef, FunctionDef, FunctionArg, PrimaryItem
from ivan.ast.lexer import Token, Span, ParseException, TokenType
from ivan.types import ReferenceKind, ReferenceType, PrimitiveType, FixedIntegerType, UnresolvedTypeRef, IvanType


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


def parse_opaque_type(parser: Parser, doc_string: Optional[DocString]) -> OpaqueTypeDef:
    parser.expect_keyword("opaque")
    parser.expect_keyword("type")
    start_span = parser.current_span
    name = parser.expect_identifier()
    parser.expect_symbol(';')
    return OpaqueTypeDef(
        name=name,
        span=start_span,
        doc_string=doc_string
    )


def parse_interface(parser: Parser, doc_string: Optional[DocString]) -> InterfaceDef:
    parser.expect_keyword("interface")
    start_span = parser.current_span
    name = parser.expect_identifier()
    parser.expect_symbol('{')
    methods = []
    pending_comment: Optional[DocString] = None
    while True:
        token = parser.peek()
        if token is None:
            raise ParseException(f"Expected closing brace for {name}", start_span)
        elif token.token_type == TokenType.DOC_COMMENT:
            if pending_comment is not None:
                raise ParseException(
                    f"Already encountered doc comment @ {pending_comment.span.line}",
                    token.span
                )
            pending_comment = parse_doc_string(parser)
            assert pending_comment is not None
        elif token.is_keyword('fun'):
            methods.append(parse_function_def(parser, pending_comment))
            pending_comment = None
        elif token.is_symbol('}'):
            parser.pop()
            # End of interface
            if pending_comment is not None:
                raise ParseException("Unexpected doc comment", pending_comment.span)
            return InterfaceDef(
                name=name,
                methods=methods,
                doc_string=doc_string,
                span=start_span
            )
        else:
            raise ParseException("Unexpected token", token.span)


def parse_function_def(parser: Parser, doc_string: Optional[DocString]) -> FunctionDef:
    parser.expect_keyword("fun")
    start_span = parser.current_span
    func_name = parser.expect_identifier()
    parser.expect_symbol('(')
    args = []
    while True:
        token = parser.peek()
        if token is None:
            raise ParseException(f"Expected closing brace for {func_name}", start_span)
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
                raise ParseException(f"Unexpected token {trailing.value!r}")
        elif token.is_symbol(')'):
            parser.pop()
            break  # stop parsing args
        else:
            raise ParseException(f"Unexpected token {token.value!r}", token.span)
    t = parser.pop()
    if t.is_symbol(';'):
        return_type = types.UNIT
    elif t.is_symbol(':'):
        return_type = parse_type(parser)
        parser.expect_symbol(';')
    else:
        raise ParseException("Unexpected token", t.span)
    return FunctionDef(
        name=func_name,
        args=args,
        span=start_span,
        return_type=return_type,
        doc_string=doc_string
    )


FIXED_INTEGER_PATTERN = re.compile("([iu])(8|16|32|64)")


def parse_type(parser: Parser) -> IvanType:
    try:
        ident_token = parser.pop()
    except ParseException:
        raise ParseException(
            "Unexpected EOF: Expected type",
            parser.last_span
        ) from None
    if ident_token.token_type == TokenType.IDENTIFIER:
        type_name = ident_token.value
    elif ident_token.is_symbol('&'):
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
            parser.pop()
        # We ate a token!
        return ReferenceType(
            target=parse_type(parser),
            kind=ref_kind
        )
    else:
        raise ParseException(
            f"Unexpected token: {ident_token.value!r}",
            ident_token.span
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
    return UnresolvedTypeRef(type_name, usage_span=ident_token.span)


def parse_item(parser: Parser, doc_string: Optional[DocString] = None) -> PrimaryItem:
    token = parser.peek()
    if token is None:
        raise ParseException("Unexpected EOF: Expected item", parser.current_span)
    if token.token_type == TokenType.DOC_COMMENT:
        if doc_string is not None:
            raise ParseException("Multiple doc comments", token.span)
        doc_string = parse_doc_string(parser)
        assert doc_string is not None
        return parse_item(parser, doc_string=doc_string)
    elif token.is_keyword('fun'):
        return parse_function_def(parser, doc_string=doc_string)
    elif token.is_keyword('interface'):
        return parse_interface(parser, doc_string=doc_string)
    elif token.is_keyword('opaque'):
        return parse_opaque_type(parser, doc_string=doc_string)
    else:
        raise ParseException("Expected item", token.span)


def parse_all(parser: Parser) -> List[PrimaryItem]:
    result = []
    while parser.peek() is not None:
        result.append(parse_item(parser))
    return result
