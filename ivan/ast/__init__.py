from abc import ABCMeta
from dataclasses import dataclass
from typing import List, Optional

from .lexer import Span
from ..types import IvanType

__all__ = [
    "lexer", "parser", "DocString",
    # AST Items
    "PrimaryItem", "InterfaceDef", "FunctionDef", "OpaqueTypeDef",
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


@dataclass(frozen=True)
class FunctionArg:
    arg_name: str
    arg_type: IvanType


@dataclass
class FunctionDef(PrimaryItem):
    args: List[FunctionArg]
    return_type: IvanType
    span: Span


@dataclass
class InterfaceDef(PrimaryItem):
    """The definition of an interface"""
    methods: List[FunctionDef]
    span: Span


@dataclass
class OpaqueTypeDef(PrimaryItem):
    """The definition of an opaque type"""
    pass
