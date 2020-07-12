from __future__ import annotations

import dataclasses
import re
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Callable, Union, Dict, Tuple

from .expr import IvanStatement
from .lexer import Span
from .types import TypeRef

__all__ = [
    "lexer", "parser", "DocString",
    # AST Items
    "PrimaryItem", "InterfaceDef", "FunctionDeclaration", "OpaqueTypeDef",
    "StructDef",
    # AST Nodes
    "FunctionArg", "Annotation", "AnnotationValue", "IvanModule", "FunctionBody",
    "FieldDef", "TypeMember",
    # Misc
    "FunctionSignature",
]

AnnotationValue = Union[str, int, bool, Tuple[str]]


VALID_MODULE_NAME_PATTERN = re.compile(r'^([\w.])+$')


@dataclass(frozen=True)
class IvanModule:
    """The definition of an ivan module"""
    name: str
    items: List[PrimaryItem]

    def __post_init__(self):
        if not VALID_MODULE_NAME_PATTERN.match(self.name):
            raise ValueError(f"Invalid module name: {self.name!r}")


@dataclass(frozen=True)
class Annotation:
    name: str
    values: Optional[Dict[str, AnnotationValue]]
    span: Span


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

    def __len__(self):
        return len(self.lines)


@dataclass(frozen=True)
class PrimaryItem(metaclass=ABCMeta):
    """A top level item"""
    name: str
    span: Span
    """The span where this item was defined"""
    doc_string: Optional[DocString]
    """The documentation for this item"""
    annotations: List[Annotation]

    def get_annotation(self, name: str) -> Optional[Annotation]:
        # TODO: Check for duplicates
        for annotation in self.annotations:
            if annotation.name == name:
                return annotation
        return None


@dataclass(frozen=True)
class TypeMember(metaclass=ABCMeta):
    """The member of a type"""
    name: str
    span: Span
    """The span where this item was defined"""
    doc_string: Optional[DocString]
    """The documentation for this item"""
    annotations: List[Annotation]


@dataclass(frozen=True)
class FieldDef(TypeMember):
    static_type: TypeRef
    """The type of the field"""


@dataclass(frozen=True)
class FunctionArg:
    arg_name: str
    arg_type: TypeRef


@dataclass(frozen=True)
class FunctionSignature:
    args: List[FunctionArg]
    return_type: TypeRef


@dataclass(frozen=True)
class FunctionBody:
    span: Span
    """If this is declared as a default implementation"""
    statements: List[IvanStatement]
    default: bool


@dataclass(frozen=True)
class FunctionDeclaration(PrimaryItem, TypeMember):
    signature: FunctionSignature
    body: Optional[FunctionBody]
    """The body of this function, or None if its an abstract definition"""


@dataclass(frozen=True)
class Implementation(PrimaryItem):
    interface_name: str
    target_name: str
    methods: List[FunctionDeclaration]


@dataclass(frozen=True)
class InterfaceDef(PrimaryItem):
    """The definition of an interface"""
    fields: List[FieldDef]
    methods: List[FunctionDeclaration]


@dataclass(frozen=True)
class StructDef(PrimaryItem):
    fields: List[FieldDef]


@dataclass(frozen=True)
class OpaqueTypeDef(PrimaryItem):
    """The definition of an opaque type"""
