from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Optional

from ivan.ast.lexer import Span


@dataclass(frozen=True)
class IvanStatement(metaclass=ABCMeta):
    """A statement"""
    span: Span

    @abstractmethod
    def visit(self, visitor: StatementVisitor):
        pass


@dataclass(frozen=True)
class ReturnStatement(IvanStatement):
    value: Optional[IvanExpr]

    def visit(self, visitor: StatementVisitor):
        return visitor.visit_return(self)


@dataclass(frozen=True)
class IvanExpr:
    """An expression"""
    span: Span


@dataclass(frozen=True)
class NullExpr(IvanExpr):
    """A null pointer expression"""
    pass


class StatementVisitor(metaclass=ABCMeta):
    @abstractmethod
    def visit_return(self, r: ReturnStatement):
        pass
