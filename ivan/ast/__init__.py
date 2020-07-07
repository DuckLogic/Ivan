from __future__ import annotations

import dataclasses
import re
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Callable, Union, Dict, Tuple

from .expr import IvanStatement
from .lexer import Span
from ..types import IvanType

__all__ = [
    "lexer", "parser", "DocString", "AstVisitor",
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

    @abstractmethod
    def visit(self, visitor: AstVisitor) -> Optional[PrimaryItem]:
        pass

    def replace_types(self, updater: Callable[[IvanType], IvanType]) -> PrimaryItem:
        updated = self.visit(TypeUpdater(updater))
        if updated is not None:
            return updated
        else:
            return self

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
    static_type: IvanType
    """The type of the field"""


@dataclass(frozen=True)
class FunctionArg:
    arg_name: str
    arg_type: IvanType


@dataclass(frozen=True)
class FunctionSignature:
    args: List[FunctionArg]
    return_type: IvanType


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

    def visit(self, visitor: AstVisitor) -> Optional[FunctionDeclaration]:
        return visitor.visit_function_declaration(self)


@dataclass(frozen=True)
class Implementation(frozen=True):
    interface_name: str
    target_name: str


@dataclass(frozen=True)
class InterfaceDef(PrimaryItem):
    """The definition of an interface"""
    fields: List[FieldDef]
    methods: List[FunctionDeclaration]

    def visit(self, visitor: AstVisitor) -> Optional[InterfaceDef]:
        return visitor.visit_interface_def(self)


@dataclass(frozen=True)
class StructDef(PrimaryItem):
    fields: List[FieldDef]

    def visit(self, visitor: AstVisitor) -> Optional[PrimaryItem]:
        return visitor.visit_struct_def(self)


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

    def visit_field_def(self, field: FieldDef) -> Optional[FieldDef]:
        # Children: FieldDef.static_type
        updated_static_type = self.visit_type(field.static_type)
        if updated_static_type is not None:
            return dataclasses.replace(field, static_type=updated_static_type)
        else:
            return None

    def visit_interface_def(self, interface: InterfaceDef) -> Optional[InterfaceDef]:
        # Children: InterfaceDef.methods, InterfaceDef.fields
        updated_methods = None
        for index, method in enumerate(interface.methods):
            updated_method = self.visit_function_declaration(method)
            if updated_method is not None:
                if updated_methods is None:
                    updated_methods = interface.methods.copy()
                updated_methods[index] = method
        updated_fields = None
        for index, field in enumerate(interface.fields):
            updated_field = self.visit_field_def(field)
            if updated_field is not None:
                if updated_fields is None:
                    updated_fields = interface.fields.copy()
                updated_fields[index] = updated_field
        updates = {}
        if updated_methods is not None:
            updates['methods'] = updated_methods
        if updated_fields is not None:
            updates['fields'] = updated_fields
        if updates:
            return dataclasses.replace(interface, **updates)
        else:
            return None

    def visit_opaque_type_def(self, opaque: OpaqueTypeDef) -> Optional[OpaqueTypeDef]:
        return None  # No children to visit

    def visit_struct_def(self, struct: StructDef) -> Optional[StructDef]:
        # Children: StructDef.fields
        updated_fields = None
        for index, field in enumerate(struct.fields):
            updated_field = self.visit_field_def(field)
            if updated_field is not None:
                if updated_fields is None:
                    updated_fields = struct.fields.copy()
                updated_fields[index] = updated_field
        if updated_fields is not None:
            return dataclasses.replace(struct, fields=updated_fields)
        else:
            return None


class TypeUpdater(AstVisitor):
    """Rewrites the types in the AST using a callback"""
    def __init__(self, updater: Callable[[IvanType], IvanType]):
        self.updater = updater

    def visit_type(self, original: IvanType) -> Optional[IvanType]:
        return self.updater(original)

