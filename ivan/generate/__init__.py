import dataclasses
import re
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from typing import ContextManager, Optional, Iterable, List

from ivan.ast import IvanModule, OpaqueTypeDef, InterfaceDef, FunctionDeclaration, DocString, FunctionBody
from ivan.types import IvanType
from ivan.types.context import TypeContext


class CodeWriter:
    current_indent: int
    __slots__ = "_lines", "current_indent", "_current_line_buffer"

    def __init__(self):
        self._lines = []
        self.current_indent = 0
        self._current_line_buffer = []

    def lines(self) -> Iterable[str]:
        yield from self._lines
        if self._current_line_buffer:
            yield ''.join(self._current_line_buffer)

    def writeln(self, s: Optional[str] = None) -> "CodeWriter":
        if s:
            self.write(s)
        self.write('\n')
        return self

    def _flush_buffer(self):
        buffer = self._current_line_buffer
        if buffer:
            self._lines.append(
                "    " * self.current_indent +
                ''.join(buffer)
            )
        buffer.clear()

    def _write_multiline(self, s: str, first_newline: int):
        assert 0 <= first_newline < len(s)
        self._flush_buffer()
        last_written = 0
        newline_index = first_newline
        buffer = []
        indent = "    " * self.current_indent
        while True:
            buffer.append(indent)
            buffer.append(s[last_written:newline_index])
            self._lines.append('\n')
            last_written = newline_index + 1
            if last_written >= len(s): return
            newline_index = s.find('\n', last_written)
            if newline_index < 0:
                break
        self._current_line_buffer.append(s[last_written:len(s)])

    def write(self, s: str) -> "CodeWriter":
        first_newline = s.find('\n')
        if first_newline >= 0:
            if first_newline == 0:
                if self._current_line_buffer:
                    self._flush_buffer()
                else:
                    self._lines.append('')
                return self
            self._write_multiline(s, first_newline)
        else:
            self._current_line_buffer.append(s)
        return self

    @contextmanager
    def with_indent(self) -> ContextManager["CodeWriter"]:
        self.current_indent += 1
        try:
            yield self
        finally:
            self.current_indent -= 1

    def __str__(self):
        return '\n'.join(self.lines())


class CodeGenerator(CodeWriter, metaclass=ABCMeta):
    context: TypeContext
    module: IvanModule
    """The target module we're generating"""
    _queued_wrappers: Optional[List[InterfaceDef]]
    """The list of interfaces want to generate wrappers for"""


    def __init__(self, module: IvanModule, context: TypeContext):
        super(CodeGenerator, self).__init__()
        self.context = context
        self.module = context.resolve_module(module)
        self._queued_wrappers = []

    def declare_types(self):
        for item in self.module.items:
            # TODO: Visitor pattern?
            wrapper_annotation = item.get_annotation("GenerateWrappers")
            if wrapper_annotation is not None:
                if isinstance(item, InterfaceDef):
                    self._queued_wrappers.append(item)
                else:
                    raise CodegenException(
                        f"Unable to generate wrappers "
                        f"for {item.name!r}: not an interface"
                    )
            if isinstance(item, InterfaceDef):
                self._declare_interface(item)
            elif isinstance(item, FunctionDeclaration):
                self._declare_top_level_function(item)
            elif isinstance(item, OpaqueTypeDef):
                self._declare_opaque_type(item)
            else:
                raise TypeError(f"Unexpected item type: {type(item)}")
            self.writeln()  # Trailing whitespace

    def generate_wrappers(self, use_prefixes=True):
        if self._queued_wrappers is None:
            raise RuntimeError(f"Already generated wrappers")
        for target_interface in self._queued_wrappers:
            interface_type = self.context.resolve_type_name(
                target_interface.name, target_interface.span
            )
            generate_annotation = target_interface.get_annotation("GenerateWrappers")
            # TODO: Utils for checking validity of annotations
            if generate_annotation.values is None:
                generate_annotation.values = {}  # HACK
            if generate_annotation.values.keys() > {"indirect_vtable", "include_doc", "prefix"}:
                raise CodegenException(f"GenerateWrappers has forbidden "
                                       f"keys for {target_interface.name}")
            # If we should accept a pointer to the vtable instead
            # of passing by value (default=True)
            indirect_vtable = generate_annotation.values.get("indirect_vtable", True)
            if type(indirect_vtable) is not bool:
                raise CodegenException("GenerateWrappers.indirect_vtable must be a bool")
            # If we should copy the documentation to the generated method
            include_doc = generate_annotation.values.get("include_doc", True)
            if type(include_doc) is not bool:
                raise CodegenException("GenerateWrappers.include_doc must be a bool")
            # The prefix for the generated method
            # This only applies if the use_prefixes option is true
            # If the string is empty, there will be no prefix (default)
            prefix = generate_annotation.values.get("prefix", "")
            if type(prefix) is not str:
                raise CodegenException("GenerateWrappers.prefix must be a str")
            for method in target_interface.methods:
                if method.get_annotation("SkipWrapper"):
                    continue
                if prefix and use_prefixes:
                    wrapper_name = f"{prefix}_{method.name}"
                else:
                    wrapper_name = method.name
                if include_doc and method.doc_string is not None:
                    doc_string = dataclasses.replace(
                        method.doc_string, lines=method.doc_string.lines + [
                            "", "[AUTO] Generated wrapper which "
                                f"delegates to {target_interface.name}"
                        ]
                    )
                else:
                    doc_string = None
                # TODO: These joined ifs seem to make IntellIJ thhink `method.body` is None from here on out
                if method.body is not None and not method.body.default:
                    raise CodegenException(
                        f"Method must be default: "
                        f"{target_interface.name}.{method.name}"
                    )
                self._write_wrapper_method(
                    wrapper_name=wrapper_name, indirect_vtable=indirect_vtable,
                    target_method=method, interface_type=interface_type,
                    default_impl=method.body,
                    doc_string=doc_string
                )
                self.writeln()  # Trailing whitespace
        self._queued_wrappers = None

    @abstractmethod
    def _write_wrapper_method(
            self, wrapper_name: str, interface_type: IvanType,
            target_method: FunctionDeclaration,
            doc_string: Optional[DocString],
            default_impl: Optional[FunctionBody],
            indirect_vtable: bool
    ):
        pass

    @abstractmethod
    def write_header(self):
        pass

    @abstractmethod
    def write_footer(self):
        pass

    @abstractmethod
    def _declare_opaque_type(self, opaque: OpaqueTypeDef):
        pass

    @abstractmethod
    def _declare_interface(self, interface: InterfaceDef):
        pass

    @abstractmethod
    def _declare_top_level_function(self, func: FunctionDeclaration):
        pass


class CodegenException(Exception):
    pass
