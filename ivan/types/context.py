from __future__ import annotations
from typing import Dict, List, Optional

from . import IvanType
from ..ast import OpaqueTypeDef, PrimaryItem, InterfaceDef, AstVisitor
from ..ast.lexer import Span


class UnresolvedTypeException(Exception):
    name: str
    span: Span

    def __init__(self, name: str, span: Span):
        super().__init__(f"Unresolved type {name!r}")
        self.name = name
        self.span = span


class UnresolvedTypeRef(IvanType):
    """A named type which hasn't been resolved"""
    usage_span: Span
    """The span where this type is referenced"""

    def __init__(self, name: str, usage_span: Span):
        super().__init__(name)
        self.usage_span = usage_span

    def print_c11(self) -> str:
        raise UnresolvedTypeException(self.name, self.usage_span)

    def print_rust(self) -> str:
        raise UnresolvedTypeException(self.name, self.usage_span)

    def __eq__(self, other):
        return isinstance(other, UnresolvedTypeRef) \
               and other.name == self.name \
               and other.usage_span == self.usage_span

    def __repr__(self):
        return f"UnresolvedType({self.name}, {self.usage_span!r})"


class DuplicateTypeException(Exception):
    name: str
    span: Span

    def __init__(self, name: str, span: Span):
        super().__init__(f"Unresolved type {name!r}")
        self.name = name
        self.span = span


class TypeContext:
    opaque_types: Dict[str, OpaqueTypeDef]
    interface_types: Dict[str, InterfaceDef]

    def __init__(self):
        self.opaque_types = {}
        self.interface_types = {}

    def resolve_type(self, target: IvanType) -> IvanType:
        if not isinstance(target, UnresolvedTypeRef):
            return target
        return self.resolve_type_name(target.name, target.usage_span)

    def resolve_type_name(self, name: str, span: Span):
        if name in self.opaque_types:
            opaque = self.opaque_types[name]
            return OpaqueTypeRef(
                definition=opaque,
                resolved=opaque.name
            )
        elif name in self.interface_types:
            interface = self.interface_types[name]
            return InterfaceTypeRef(
                definition=interface,
                resolved=interface.name
            )
        else:
            raise UnresolvedTypeException(name, span)

    def __contains__(self, item):
        return item in self.opaque_types or item in self.interface_types

    @staticmethod
    def build_context(items: List[PrimaryItem]) -> TypeContext:
        builder = TypeContextBuilder()
        for item in items:
            item.visit(builder)
        return builder.context


class TypeContextBuilder(AstVisitor):
    context: TypeContext

    def __init__(self):
        self.context = TypeContext()

    def visit_interface_def(self, interface: InterfaceDef) -> Optional[InterfaceDef]:
        if interface.name in self.context:
            raise DuplicateTypeException(interface.name, interface.span)
        else:
            self.context.interface_types[interface.name] = interface
        return super().visit_interface_def(interface)

    def visit_opaque_type_def(self, opaque: OpaqueTypeDef) -> Optional[OpaqueTypeDef]:
        if opaque.name in self.context:
            raise DuplicateTypeException(opaque.name, opaque.span)
        else:
            self.context.opaque_types[opaque.name] = opaque
        return super().visit_opaque_type_def(opaque)


class OpaqueTypeRef(IvanType):
    definition: OpaqueTypeDef
    resolved_name: str

    def __init__(self, definition: OpaqueTypeDef, resolved: str):
        super().__init__(definition.name)
        self.definition = definition
        self.resolved_name = resolved

    def print_c11(self) -> str:
        return self.resolved_name

    def print_rust(self) -> str:
        return self.resolved_name

    def __repr__(self):
        if self.resolved_name == self.definition.name:
            return f"OpaqueTypeRef({self.resolved_name})"
        else:
            return f"OpaqueTypeRef({self.definition.name}, resolved={self.resolved_name})"


class InterfaceTypeRef(IvanType):
    definition: InterfaceDef
    resolved_name: str

    def __init__(self, definition: InterfaceDef, resolved: str):
        super().__init__(definition.name)
        self.definition = definition
        self.resolved_name = resolved

    def print_c11(self) -> str:
        return self.resolved_name

    def print_rust(self) -> str:
        return self.resolved_name

    def __repr__(self):
        if self.resolved_name == self.definition.name:
            return f"InterfaceTypeRef({self.resolved_name})"
        else:
            return f"InterfaceTypeRef({self.definition.name}, resolved={self.resolved_name})"
