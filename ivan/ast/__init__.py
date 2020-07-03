from __future__ import annotations

import dataclasses
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Callable, Union, Dict, Tuple

from .lexer import Span
from ..types import IvanType

__all__ = [
    "lexer", "parser", "DocString", "AstVisitor",
    # AST Items
    "PrimaryItem", "InterfaceDef", "FunctionDeclaration", "OpaqueTypeDef",
    # AST Nodes
    "FunctionArg", "Annotation", "AnnotationValue", "FunctionSignature"
]

AnnotationValue = Union[str, int, Tuple[str]]


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
    annotations: List[Annotation]
    """The documentation for this item"""

    @abstractmethod
    def visit(self, visitor: AstVisitor) -> Optional[PrimaryItem]:
        pass

    def update_types(self, updater: Callable[[IvanType], IvanType]) -> PrimaryItem:
        updated = self.visit(TypeUpdater(updater))
        if updated is not None:
            return updated
        else:
            return self


@dataclass(frozen=True)
class FunctionArg:
    arg_name: str
    arg_type: IvanType


@dataclass(frozen=True)
class FunctionSignature:
    args: List[FunctionArg]
    return_type: IvanType


@dataclass(frozen=True)
class FunctionDeclaration(PrimaryItem):
    signature: FunctionSignature

    def visit(self, visitor: AstVisitor) -> Optional[FunctionDeclaration]:
        return visitor.visit_function_declaration(self)


@dataclass(frozen=True)
class InterfaceDef(PrimaryItem):
    """The definition of an interface"""
    methods: List[FunctionDeclaration]
    span: Span

    def visit(self, visitor: AstVisitor) -> Optional[InterfaceDef]:
        return visitor.visit_interface_def(self)


@dataclass(frozen=True)
class OpaqueTypeDef(PrimaryItem):
    """The definition of an opaque type"""

    def visit(self, visitor: AstVisitor) -> Optional[OpaqueTypeDef]:
        return visitor.visit_opaque_type_def(self)


class AstVisitor(metaclass=ABCMeta):
    def visit_type(self, original: IvanType) -> Optional[IvanType]:
        return None  # No children

    def visit_signature(self, signature: FunctionSignature) -> Optional[FunctionSignature]:
        # Children: FunctionSignature.args, FunctionSignature.return_type
        copied_args = None
        for index, original_arg in enumerate(signature.args):
            updated_type = self.visit_type(original_arg.arg_type)
            if updated_type is not None:
                if copied_args is None:
                    copied_args = signature.args.copy()
                copied_args[index] = FunctionArg(
                    arg_name=original_arg.arg_name,
                    arg_type=updated_type
                )
        updated_return_type = self.visit_type(signature.return_type)
        if copied_args is None and updated_return_type is None:
            return None
        return FunctionSignature(
            args=copied_args if copied_args is not None else signature.args,
            return_type=updated_return_type if updated_return_type is not None
            else signature.return_type
        )

    def visit_function_declaration(self, func: FunctionDeclaration) -> Optional[FunctionDeclaration]:
        # Children: FunctionDeclaration.signature
        updated_signature = self.visit_signature(func.signature)
        if updated_signature is not None:
            return dataclasses.replace(func, signature=updated_signature)
        else:
            return None

    def visit_interface_def(self, interface: InterfaceDef) -> Optional[InterfaceDef]:
        # Children: InterfaceDef.methods
        updated_methods = None
        for index, method in enumerate(interface.methods):
            updated_method = self.visit_function_declaration(method)
            if updated_method is not None:
                if updated_methods is None:
                    updated_methods = interface.methods.copy()
                updated_methods[index] = method
        if updated_methods is not None:
            return dataclasses.replace(interface, methods=updated_methods)
        else:
            return None

    def visit_opaque_type_def(self, opaque: OpaqueTypeDef) -> Optional[OpaqueTypeDef]:
        return None  # No children to visit


class TypeUpdater(AstVisitor):
    """Rewrites the types in the AST using a callaback"""
    def __init__(self, updater: Callable[[IvanType], IvanType]):
        self.updater = updater

    def visit_type(self, original: IvanType) -> Optional[IvanType]:
        return self.updater(original)

