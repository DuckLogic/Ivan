from ivan.ast.expr import IvanStatement, ReturnStatement, IvanExpr, NullExpr
from ivan.ast.lexer import ParseException
from ivan.ast.parser import Parser


def parse_statement(parser: Parser) -> IvanStatement:
    first = parser.peek()
    start_span = parser.current_span
    if not first:
        raise ParseException("Unexpected EOF: Expected statement", parser.current_span)
    elif first.is_keyword('return'):
        parser.pop()
        if parser.peek().is_symbol(';'):
            parser.pop()
            return ReturnStatement(span=start_span, value=None)
        else:
            value = parse_expr(parser)
            parser.expect_symbol(';')
            return ReturnStatement(span=start_span, value=value)
    else:
        raise ParseException(f"Unexpected statement token: {first.value!r}", start_span)


def parse_expr(parser: Parser) -> IvanExpr:
    first = parser.peek()
    start_span = parser.current_span
    if not parser:
        raise ParseException("Unexpected EOF: Expected expression", parser.current_span)
    elif first.is_keyword("null"):
        parser.pop()
        return NullExpr(span=start_span)
    else:
        raise ParseException(f"Unexpected keyword: {first.value!r}", start_span)
