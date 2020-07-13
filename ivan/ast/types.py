"""References to types in the AST"""
from __future__ import annotations

import re
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum

from ivan.ast.lexer import Span


class UnresolvedTypeError(RuntimeError):
    """An unexpectedly unresolved type

    This is considered an internal error.
    The app is in an incorrect state.
    """
    span: Span

    def __init__(self, name: str, span: Span):
        super().__init__(f"Unresolved type: {name!r}")
        self.span = span


class ReferenceKind(Enum):
    IMMUTABLE = '&'
    MUTABLE = "&mut"
    OWNED = "&own"
    RAW = "&raw"


class TypeRef(metaclass=ABCMeta):
    """
    A reference to the type in the AST

    This type may or may not be 'resolved'
    """
    usage_span: Span
    """The span where this type is referenced"""

    def __init__(self, usage_span: Span):
        self.usage_span = usage_span
        self._resolved = None

    @property
    def resolved(self) -> ResolvedType:
        resolved = self._resolved
        if resolved is None:
            raise UnresolvedTypeError(
                f"Unresolved type: {self}",
                self.usage_span
            )
        else:
            return resolved

    @resolved.setter
    def resolved(self, updated: ResolvedType):
        if self._resolved is not None:
            raise RuntimeError(
                f"Can't resolve to {updated!r}, because already "
                f"resolved to {self._resolved!r}"
            )
        self._resolved = updated

    def __eq__(self, other) -> bool:
        if not isinstance(other, TypeRef):
            return False
        return str(self) == str(other) and self._resolved == other._resolved

    @abstractmethod
    def __str__(self) -> str:
        """This type's textual representation"""
        pass


class NamedTypeRef(TypeRef):
    """A reference to an unresolved named type"""
    name: str

    def __init__(self, usage_span: Span, name: str):
        super(NamedTypeRef, self).__init__(usage_span)
        self.name = name

    def __post_init__(self):
        name = self.name
        assert name.isidentifier(), f"Invalid identifier: {name!r}"

    def __str__(self) -> str:
        return self.name


class ReferenceTypeRef(TypeRef):
    """An unresolved reference type"""
    inner: TypeRef
    kind: ReferenceKind

    def __init__(self, usage_span: Span, inner: TypeRef, kind: ReferenceKind):
        super().__init__(usage_span)
        self.inner = inner
        self.kind = kind

    def __str__(self) -> str:
        if self.kind == ReferenceKind.IMMUTABLE:
            return f"&{self.inner}"
        else:
            return f"{self.kind} {self.inner}"


class OptionalTypeRef(TypeRef):
    inner: TypeRef

    def __init__(self, usage_span: Span, inner: TypeRef):
        super().__init__(usage_span)
        self.inner = inner

    def __str__(self):
        return f"opt {self.inner}"


class BuiltinKind(Enum):
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


class ResolvedType(metaclass=ABCMeta):
    """Base class for all resolved types"""
    name: str
    """The name of the type, as used in Ivan code

    This doesn't necessarily correspond to a valid type
    name in either C11 or Rust.
    """

    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, ResolvedType) and other.name == self.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def print_c11(self) -> str:
        pass

    @abstractmethod
    def print_rust(self) -> str:
        pass


class FixedIntegerType(ResolvedType):
    """An integer type with a fixed bit width"""
    bits: int
    signed: bool

    def __init__(self, bits: int, signed: bool):
        super().__init__(f"i{bits}" if signed else f"u{bits}")
        if bits not in {8, 16, 32, 64}:
            raise ValueError(f"Invalid #bits: {bits}")
        self.bits = bits
        self.signed = signed

    def print_c11(self) -> str:
        if self.signed:
            return f"int{self.bits}_t"
        else:
            return f"uint{self.bits}_t"

    def print_rust(self) -> str:
        return self.name

    def __eq__(self, other):
        return isinstance(other, FixedIntegerType) and \
               self.bits == other.bits and self.signed == other.signed

    def __repr__(self):
        return f"FixedIntegerType({self.bits}, {self.signed})"

    PATTERN = re.compile(r"([iu])(\d+)")

    @staticmethod
    def parse(s: str, span: Span) -> FixedIntegerType:
        match = FixedIntegerType.PATTERN.match(s)
        if match is None:
            raise ValueError(f"Expected valid integer: {s!r}")
        if match[1] == 'i':
            signed = True
        elif match[1] == 'u':
            signed = False
        else:
            raise AssertionError(s)
        bits = int(match[2])
        if bits not in {8, 16, 32, 64}:
            raise ParseException(
                f"Invalid # of integer bits: {bits}",
                span
            )
        return FixedIntegerType(signed=signed, bits=bits)


class BuiltinType(ResolvedType):
    kind: BuiltinKind

    def __init__(self, kind: BuiltinKind):
        super().__init__(kind.ivan_name)

    def __repr__(self):
        return f"BuiltinType({self.kind!r})"

    def print_c11(self) -> str:
        return self.kind.c11_name

    def print_rust(self) -> str:
        return self.kind.rust_name


class ReferenceType(ResolvedType):
    target: ResolvedType
    kind: ReferenceKind
    optional: bool

    def __init__(self, target: ResolvedType, kind: ReferenceKind, optional: bool = False):
        super().__init__(
            ("opt " if optional else "") +
            f"&{target.name}" if kind == ReferenceKind.IMMUTABLE
            else f"{kind.value} {target.name}"
        )
        self.optional = optional
        self.target = target
        self.kind = kind

    def print_c11(self) -> str:
        # Everything is a pointer in C!
        # We don't care about "Optional"
        if self.kind == ReferenceKind.IMMUTABLE:
            return f"const {self.target.print_c11()}*"
        else:
            return f"{self.target.print_c11()}*"

    def print_rust(self) -> str:
        if self.kind == ReferenceKind.IMMUTABLE:
            # TODO: Are references always safe to use?
            # This pretty-low level FFI code....
            ref_type = f"&{self.target.print_rust()}"
        elif self.kind == ReferenceKind.MUTABLE:
            ref_type = f"&mut {self.target.print_rust()}"
        elif self.kind == ReferenceKind.OWNED or \
                self.kind == ReferenceKind.RAW:
            # Rust doesn't have a way to handle these natively
            # We just map them to raw pointers
            # At this point we don't care about nullability
            return f"*mut {self.target.print_rust()}"
        else:
            raise AssertionError(f"Unknown kind: {self.kind}")
        assert ref_type
        if self.optional:
            return f"Optional<{ref_type}>"
        else:
            return ref_type

    def __repr__(self):
        return f"ReferenceType({self.target}, {self.kind}, optional={self.optional})"
