"""Compiles Ivan code"""
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Dict, List

from ivan.compiler.types import IvanType, BuiltinType, BuiltinKind

from ivan import ast
from ivan.ast import FunctionBody, ResolvedType, FunctionArg, MethodSelfArgument
from ivan.ast.expr import IvanExpr, NullExpr, StatementVisitor
from ivan.ast.lexer import Span
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
    desired: ResolvedType
    actual: str

    def __init__(self, desired_type: ResolvedType, actual_type: str, span: Span):
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
class CompilerInput:
    declared_items: Dict[str, ast.PrimaryItem]
    external_types: Dict[str, str]


class CodeCompiler(StatementVisitor, metaclass=ABCMeta):
    def __init__(self, writer: CodeWriter, func_signature: FunctionSignature):
        self.writer = writer
        self.func_signature = func_signature

    def compile_expr(self, expr: IvanExpr, desired_type: IvanType) -> CompiledExpr:
        if isinstance(expr, NullExpr):
            return self.compile_null_expr(expr, desired_type)
        else:
            raise TypeError(f"Unknown expression type: {type(desired_type)}")

    @abstractmethod
    def compile_null_expr(self, expr: NullExpr, desired_type: IvanType) -> CompiledExpr:
        pass


