"""Compiles Ivan code"""
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Optional

from ivan import types
from ivan.ast import FunctionSignature, FunctionBody, TypeRef
from ivan.ast.expr import IvanExpr, NullExpr, StatementVisitor, ReturnStatement
from ivan.ast.lexer import Span
from ivan.compiler.types import IvanType
from ivan.generate import CodeWriter


class CompileException(Exception):
    span: Span

    def __init__(self, msg: str, span: Span):
        super().__init__(msg)
        self.span = span

    def __str__(self):
        # TODO: This seems inconsistent with other error printing
        # We need a more consistent way to handle error spans :p
        return str(super()) + f" @ {self.span}"


class IncompatibleTypeException(CompileException):
    desired: IvanType
    actual: str

    def __init__(self, desired_type: IvanType, actual_type: str, span: Span):
        super().__init__(f"Can't compile an {actual_type} to a {desired_type}", span)
        self.desired = desired_type
        self.actual = actual_type


@dataclass(frozen=True)
class CompiledExpr:
    original: IvanExpr
    static_type: IvanType
    code: str


@dataclass(frozen=True)
class CompiledBody:
    original: FunctionBody
    code: str


@dataclass(frozen=True)
class CompilerContext:
    context_name: str
    return_type: Optional[IvanType] = None


class ExprCompiler(metaclass=ABCMeta):
    def compile_expr(self, expr: IvanExpr, desired_type: IvanType) -> CompiledExpr:
        if isinstance(expr, NullExpr):
            return self.compile_null_expr(expr, desired_type)
        else:
            raise TypeError(f"Unknown expression type: {type(desired_type)}")

    @abstractmethod
    def compile_null_expr(self, expr: NullExpr, desired_type: IvanType) -> CompiledExpr:
        pass


class BaseCompiler(StatementVisitor, ExprCompiler, metaclass=ABCMeta):
    writer: CodeWriter
    func_signature: FunctionSignature

    def __init__(self, writer: CodeWriter, func_signature: FunctionSignature):
        self.writer = writer
        self.func_signature = func_signature

    def resolve(self, target: TypeRef) -> IvanType:
        raise NotImplementedError

    def compile_body(self, body: FunctionBody) -> CompiledBody:
        assert not str(self.writer), f"Already has code:\n{self.writer}"
        for statement in body.statements:
            statement.visit(self)
        return CompiledBody(
            original=body,
            code=str(self.writer)
        )


class C11Compiler(BaseCompiler):
    def visit_return(self, r: ReturnStatement):
        self.writer.write('return')
        if r.value is None:
            if self.func_signature.return_type != types.UNIT:
                raise CompileException(
                    f"Expected a {self.func_signature.return_type!r}, "
                    "but got no return value",
                    span=r.span
                )
        else:
            value = self.compile_expr(r.value, desired_type=self.func_signature.return_type)
            self.writer.write(f' {value.code}')
        self.writer.writeln(';')

    def compile_null_expr(self, expr: NullExpr, desired_type: IvanType) -> CompiledExpr:
        if isinstance(desired_type, IvanType) and desired_type.optional:
            return CompiledExpr(
                original=expr,
                static_type=desired_type,
                code="NULL"
            )
        else:
            raise IncompatibleTypeException(
                desired_type, "optional reference",
                span=expr.span
            )

