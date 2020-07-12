"""References to types in the AST"""
import re
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum, EnumMeta
from typing import FrozenSet
from itertools import chain

from ivan.ast.lexer import Span


class ReferenceKind(Enum):
    IMMUTABLE = '&'
    MUTABLE = "&mut"
    OWNED = "&own"
    RAW = "&raw"


@dataclass(frozen=True)
class TypeRef(metaclass=ABCMeta):
    """A reference to the type in the AST"""
    usage_span: Span
    """The span where this type is referenced"""

    @property
    @abstractmethod
    def __str__(self) -> str:
        """This type's textual representation"""
        pass


@dataclass(frozen=True)
class NamedTypeRef(TypeRef):
    """
    A reference to a named type

    This includes builtin types and `i64` anything that parses
    as an identifier
    """
    name: str

    def __post_init__(self):
        name = self.name
        assert name.isidentifier(), f"Invalid identifier: {name!r}"

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class ReferenceTypeRef(TypeRef):
    inner: TypeRef
    kind: ReferenceKind

    def __str__(self):
        if self.kind == ReferenceKind.IMMUTABLE:
            return f"&{self.inner}"
        else:
            return f"{self.inner}{self.kind}"


@dataclass(frozen=True)
class OptionalTypeRef(TypeRef):
    inner: TypeRef

    def __str__(self):
        return f"opt {self.inner}"