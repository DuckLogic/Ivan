from __future__ import annotations

from typing import List, Sequence, Optional

from ivan import types
from ivan.ast import AstVisitor, OpaqueTypeDef, InterfaceDef, FunctionDeclaration, FunctionSignature, FunctionArg, \
    DocString
from ivan.generate import CodeWriter, VALID_MODULE_NAME_PATTERN
from ivan.types import IvanType, ReferenceType, ReferenceKind


class C11CodeGenerator(AstVisitor):
    writer: CodeWriter
    name: str

    def __init__(self, writer: CodeWriter, name: str):
        assert VALID_MODULE_NAME_PATTERN.match(name), f"Invalid name: {name!r}"
        self.writer = writer
        self.name = name

    @property
    def header_name(self) -> str:
        return self.name.upper().replace('.', '_') + "_H"

    def write_header(self, imports: Sequence[str] = ()):
        self.writer.writeln(f"#ifndef {self.header_name}")
        self.writer.writeln(f"#define {self.header_name}")
        self.writer.writeln()
        std_imports = ["<stdint.h>", "<stdbool.h>", "<stdlib.h>"]
        global_imports = []
        local_imports = []
        for header in imports:
            if header.startswith("<std") and header.endswith(">"):
                std_imports.append(header)
            elif header.startswith('<') and header.endswith('>'):
                global_imports.append(header)
            elif header.startswith('"') and header.endswith('"'):
                local_imports.append(header)
            else:
                raise ValueError(f"Invalid import: {header!r}")
        if std_imports:
            for include in std_imports:
                self.writer.writeln(f"#include {include}")
            self.writer.writeln()
        if global_imports:
            for include in global_imports:
                self.writer.writeln(f"#include {include}")
            self.writer.writeln()
        if local_imports:
            for include in global_imports:
                self.writer.writeln(f"#include {include}")
            self.writer.writeln()

    def write_footer(self):
        self.writer.writeln(f"#endif /* {self.header_name} */")
        self.writer.writeln()

    def write_doc(self, doc_string: Optional[DocString]):
        if doc_string:
            for line in doc_string.print_like_java():
                self.writer.writeln(line)

    def write_function_signature(self, name: str, signature: FunctionSignature):
        self.writer.write(f'{signature.return_type.print_c11()} {name}(')
        self.writer.write(', '.join(f"{arg.arg_type.print_c11()} {arg.arg_name}"
                                    for arg in signature.args))
        self.writer.write(')')

    def declare_function_pointer(self, name: str, signature: FunctionSignature):
        self.writer.write(f'{signature.return_type.print_c11()} (*{name})(')
        self.writer.write(', '.join(f"{arg.arg_type.print_c11()} {arg.arg_name}"
                                    for arg in signature.args))
        self.writer.write(')')

    def visit_function_declaration(self, func: FunctionDeclaration):
        self.write_doc(func.doc_string)
        self.write_function_signature(func.name, func.signature)
        self.writer.writeln(';')

    def visit_interface_def(self, interface: InterfaceDef):
        self.write_doc(interface.doc_string)
        self.writer.writeln(f"typedef struct {interface.name} {{")
        with self.writer.with_indent():
            for method in interface.methods:
                self.write_doc(method.doc_string)
                self.declare_function_pointer(method.name, method.signature)
                self.writer.writeln(';')
        self.writer.writeln(f"}} {interface.name};")

    def visit_opaque_type_def(self, opaque: OpaqueTypeDef):
        self.write_doc(opaque.doc_string)
        self.writer.writeln(f"typedef struct {opaque.name} {opaque.name};")

    def write_wrapper_method(
            self, wrapper_name: str, interface_type: IvanType,
            target_method: FunctionDeclaration,
            indirect_vtable=True, include_doc=False
    ):
        """Generate a wrapper method for the specified interface"""
        assert all('vtable' != arg.arg_name for arg in target_method.signature.args)
        if include_doc:
            self.write_doc(target_method.doc_string)
        if indirect_vtable:
            vtable_type = ReferenceType(interface_type, ReferenceKind.IMMUTABLE)
        else:
            vtable_type = interface_type
        self.write_function_signature(wrapper_name, FunctionSignature(
            args=[FunctionArg("vtable", vtable_type), *target_method.signature.args],
            return_type=target_method.signature.return_type
        ))
        self.writer.writeln(' {')
        with self.writer.with_indent() as writer:
            if target_method.signature.return_type != types.UNIT:
                writer.write("return ")
            if indirect_vtable:
                writer.write('vtable->')
            else:
                writer.write('vtable.')
            writer.write(target_method.name)
            writer.write('(')
            writer.write(', '.join(f"{arg.arg_name}" for arg in target_method.signature.args))
            writer.writeln(');')
        self.writer.writeln('}')
