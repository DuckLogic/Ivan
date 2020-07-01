from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Optional

from ivan.ast.lexer import Span


class UnresolvedTypeException(Exception):
    name: str
    span: Span

    def __init__(self, name: str, span: Span):
        super().__init__(f"Unresolved type {name!r}")
        self.name = name
        self.span = span


class IvanType(metaclass=ABCMeta):
    """Base class for the internal type system"""
    name: str
    """The name of the type, as used in Ivan code

    This doesn't necessarily correspond to a valid type
    name in either C11 or Rust.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def print_c11(self) -> str:
        """Print this Ivan type as a C11 type"""
        pass

    @abstractmethod
    def print_rust(self) -> str:
        """Print this type as a Rust type"""
        pass

    def __eq__(self, other):
        return isinstance(other, IvanType) and other.name == self.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    @abstractmethod
    def __repr__(self):
        pass


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
        return isinstance(other, UnresolvedTypeRef)\
               and other.name == self.name\
               and other.usage_span == self.usage_span

    def __repr__(self):
        return f"UnresolvedType({self.name}, {self.usage_span!r})"


class ReferenceKind(Enum):
    IMMUTABLE = '&'
    MUTABLE = "&mut"
    OWNED = "&own"
    RAW = "&raw"


class ReferenceType(IvanType):
    target: IvanType
    kind: ReferenceKind

    def __init__(self, target: IvanType, kind: ReferenceKind):
        super().__init__(
            f"&{target.name}" if kind == ReferenceKind.IMMUTABLE
            else f"{kind.value} {target.name}"
        )
        self.target = target
        self.kind = kind

    def print_c11(self) -> str:
        # Everything is a pointer in C!
        if self.kind == ReferenceKind.IMMUTABLE:
            return f"const {self.target.print_c11()}*"
        else:
            return f"{self.target.print_c11()}*"

    def print_rust(self) -> str:
        if self.kind == ReferenceKind.IMMUTABLE:
            # TODO: Are references always safe to use?
            # This pretty-low level FFI code....
            return f"&{self.target.print_rust()}"
        elif self.kind == ReferenceKind.MUTABLE:
            return f"&mut {self.target.print_rust()}"
        elif self.kind == ReferenceKind.OWNED or\
                self.kind == ReferenceKind.RAW:
            # Rust doesn't have a way to handle these natively
            # We just map them to raw pointers
            return f"*mut {self.target.print_rust()}"
        else:
            raise AssertionError(f"Unknown kind: {self.kind}")

    def __repr__(self):
        return f"ReferenceType({self.target}, {self.kind})"


class FixedIntegerType(IvanType):
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
        return isinstance(other, FixedIntegerType) and\
               self.bits == other.bits and self.signed == other.signed

    def __hash__(self):
        return self.bits if self.signed else -self.bits

    def __repr__(self):
        return f"FixedIntegerType({self.bits}, {self.signed})"


_PRIMITIVE_TYPES = dict()


class PrimitiveType(IvanType):

    def __init__(self, name: str, c11: str, rust: str):
        super().__init__(name=name)
        self.c11_name = c11
        self.rust_name = rust
        global _PRIMITIVE_TYPES
        if _PRIMITIVE_TYPES is None:
            _PRIMITIVE_TYPES = dict()
        if name in _PRIMITIVE_TYPES:
            raise RuntimeError(f"Already defined primitive {name}")
        _PRIMITIVE_TYPES[name] = self

    c11_name: str
    rust_name: str

    def print_c11(self) -> str:
        return self.c11_name

    def print_rust(self) -> str:
        return self.rust_name

    def __repr__(self):
        return f"PrimitiveType(name={self.name}, " \
               f"c11={self.c11_name}, " \
               f"rust={self.rust_name})"

    @staticmethod
    def try_parse(s: str) -> Optional["PrimitiveType"]:
        return _PRIMITIVE_TYPES.get(s)


UNIT = PrimitiveType("unit", "void", "()")
"""The unit type - for functions that don't return any value"""

INT = PrimitiveType("int", "int", "i32")  # NOTE: Assumes sizeof(int) == 32
"""The idiomatic way to represent a signed 32-bit integer"""

BYTE = PrimitiveType("byte", "char", "u8")
"""The idiomatic way to represent a byte"""

DOUBLE = PrimitiveType("double", "double", "f64")
BOOLEAN = PrimitiveType("bool", "bool", "bool")
USIZE = PrimitiveType("usize", "size_t", "usize")
ISIZE = PrimitiveType("isize", "intptr_t", "isize")
