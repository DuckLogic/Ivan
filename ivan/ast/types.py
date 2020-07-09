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


class BuiltinType(Enum):
    """
    An enumeration of Ivan's builtin types

    The enum's 'value' is its name in Ivan source code.
    This allows lookups like `BuiltinType('unit')` to retrieve a
    builtin based on its Ivan name
    """
    # TODO: This isn't really a full-fledged type in C
    UNIT = ("unit", "void", "()")
    """The unit type - for functions that don't return any value"""
    INT = ("int", "int", "i32")  # NOTE: Assumes sizeof(int) == 32
    """A signed 32-bit integer - the default numeric type"""
    BYTE = ("byte", "char", "u8")  # NOTE: Signs are mismatched
    """A byte"""
    DOUBLE = ("double", "double", "f64")
    """A double-precision floating point value (64-bit)"""
    BOOLEAN = ("bool", "bool", "bool")
    USIZE = ("usize", "size_t", "usize")
    """A pointer-sized unsigned integer"""
    ISIZE = ("isize", "intptr_t", "isize")
    """A pointer-sized signed integer"""

    ivan_name: str
    """The name of the Ivan type (also the enum's value)"""
    c11_name: str
    """The name of the corresponding C11 type"""
    rust_name: str
    """The name of the corresponding Rust type"""

    def __new__(cls, ivan_name: str, c11_name: str, rust_name: str):
        obj = object.__new__(cls)
        obj._value_ = ivan_name
        obj.ivan_name = ivan_name
        obj.c11_name = c11_name
        obj.rust_name = rust_name
        return obj


BUILTIN_TYPE_NAMES: FrozenSet[str] = frozenset(builtin.ivan_name for builtin in BuiltinType)


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
    """A reference to a named type"""

    name: str

    def __post_init__(self):
        name = self.name
        assert name.isidentifier(), f"Invalid identifier: {name!r}"
        assert name not in RESERVED_NAMES, f"Reserved name: {name!r}"

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class FixedIntegerRef(TypeRef):
    bits: int
    signed: bool

    PATTERN = re.compile(r"([iu])(\d+)")

    def __post_init__(self):
        assert self.bits in {8, 16, 32, 64}, f"Invalid bits: {self.bits}"

    def __str__(self) -> str:
        return f"{'i' if self.signed else 'u'}{self.bits}"


@dataclass(frozen=True)
class ReferenceTypeRef(TypeRef):
    inner: TypeRef
    kind: ReferenceKind

    def __str__(self):
        if self.kind == ReferenceKind.targetIMMUTABLE:
            return f"&{self.inner}"
        else:
            return f"{self.inner}{self.kind}"


@dataclass(frozen=True)
class OptionalTypeRef(TypeRef):
    inner: TypeRef

    def __str__(self):
        return f"opt {self.inner}"


@dataclass(frozen=True)
class BuiltinTypeRef(TypeRef):
    type: BuiltinType

    def __str__(self):
        return self.type.ivan_name


RESERVED_NAMES: FrozenSet[str] = frozenset((
    *BUILTIN_TYPE_NAMES, "opt",
    chain.from_iterable((f"i{bits}", f"u{bits}") for bits in (8, 16, 32, 64))
))
