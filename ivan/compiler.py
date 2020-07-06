"""Compiles Ivan code"""
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Optional

from ivan.ast.expr import IvanExpr, IvanStatement, NullExpr
from ivan.ast.lexer import Span
from ivan.types import IvanType
from ivan.types.context import TypeContext


class CompileException(Exception):
    span: Span

    def __init__(self, msg: str, span: Span):
        super().__init__(msg)
        self.span = span

    def __str__(self):
        # TODO: This seems inconsistent with other places where we
        # We need a more consistent way to handle error spans :p
        return str(super()) + f" @ {self.span}"


class IncompatibleTypeException(CompileException):
    desired: IvanType
    actual: str

    def __init__(self, desired: IvanType, actual: str, span: Span):
        super().__init__(f"Can't compile a {actual}: needed a {desired}", span)
        self.desired = desired
        self.actual = actual


@dataclass(frozen=True)
class CompiledExpr:
    original: IvanExpr
    static_type: IvanType
    code: str


@dataclass(frozen=True)
class CompiledStatement:
    original: IvanStatement
    code: str


@dataclass(frozen=True)
class CompilerContext:
    context_name: str
    types: TypeContext
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
