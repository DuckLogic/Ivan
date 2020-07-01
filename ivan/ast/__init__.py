from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from .lexer import Span
from ..types import IvanType

__all__ = [
    "lexer", "parser", "DocString",
    # AST Items
    "PrimaryItem", "InterfaceDef", "FunctionDeclaration", "OpaqueTypeDef",
    # AST Nodes
    "FunctionArg"
]


@dataclass
class DocString:
    """The documentation for an item"""
    lines: List[str]
    span: Span

    def print_like_java(self) -> List[str]:
        result = ["/**"]
        for line in self.lines:
            if not line:
                # Empty
                result.append(" *")
            else:
                result.append(f" * {line}")
        result.append(" */")
        return result

    def print_like_rust(self) -> List[str]:
        return [f"/// {line}" if line else "///" for line in self.lines]


@dataclass
class PrimaryItem(metaclass=ABCMeta):
    """A top level item"""
    name: str
    span: Span
    """The span where this item was defined"""
    doc_string: Optional[DocString]
    """The documentation for this item"""

    @abstractmethod
    def visit(self, visitor: "AstVisitor"):
        pass


@dataclass(frozen=True)
class FunctionArg:
    arg_name: str
    arg_type: IvanType


@dataclass(frozen=True)
class FunctionSignature:
    args: List[FunctionArg]
    return_type: IvanType


@dataclass
class FunctionDeclaration(PrimaryItem):
    signature: FunctionSignature

    def visit(self, visitor: "AstVisitor"):
        visitor.visit_function_declaration(self)


@dataclass
class InterfaceDef(PrimaryItem):
    """The definition of an interface"""
    methods: List[FunctionDeclaration]
    span: Span

    def visit(self, visitor: "AstVisitor"):
        visitor.visit_interface_def(self)


@dataclass
class OpaqueTypeDef(PrimaryItem):
    """The definition of an opaque type"""

    def visit(self, visitor: "AstVisitor"):
        visitor.visit_opaque_type_def(self)


class AstVisitor(metaclass=ABCMeta):
    def visit_function_declaration(self, func: FunctionDeclaration):
        pass

    def visit_interface_def(self, interface: InterfaceDef):
        for method in interface.methods:
            self.visit_function_declaration(method)

    def visit_opaque_type_def(self, opaque: OpaqueTypeDef):
        pass
