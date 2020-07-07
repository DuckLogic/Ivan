from __future__ import annotations

from typing import Sequence, Optional

from ivan import types
from ivan.ast import OpaqueTypeDef, InterfaceDef, FunctionDeclaration, FunctionSignature, FunctionArg, \
    DocString, FunctionBody
from ivan.compiler import C11Compiler
from ivan.generate import CodeWriter, CodeGenerator
from ivan.types import IvanType, ReferenceType, ReferenceKind


class C11CodeGenerator(CodeGenerator):
    @property
    def header_name(self) -> str:
        return self.module.name.upper().replace('.', '_') + "_H"

    def write_header(self):
        imports = []  # TODO: Configurable imports
        self.writeln(f"#ifndef {self.header_name}")
        self.writeln(f"#define {self.header_name}")
        self.writeln()
        std_imports = ["<stdint.h>", "<stdbool.h>", "<stdlib.h>", "<assert.h>"]
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
                self.writeln(f"#include {include}")
            self.writeln()
        if global_imports:
            for include in global_imports:
                self.writeln(f"#include {include}")
            self.writeln()
        if local_imports:
            for include in global_imports:
                self.writeln(f"#include {include}")
            self.writeln()

    def write_footer(self):
        self.writeln(f"#endif /* {self.header_name} */")
        self.writeln()

    def write_doc(self, doc_string: Optional[DocString]):
        if doc_string:
            for line in doc_string.print_like_java():
                self.writeln(line)

    def write_function_signature(self, name: str, signature: FunctionSignature):
        self.write(f'{signature.return_type.print_c11()} {name}(')
        self.write(', '.join(f"{arg.arg_type.print_c11()} {arg.arg_name}"
                                    for arg in signature.args))
        self.write(')')

    def declare_function_pointer(self, name: str, signature: FunctionSignature):
        self.write(f'{signature.return_type.print_c11()} (*{name})(')
        self.write(', '.join(f"{arg.arg_type.print_c11()} {arg.arg_name}"
                             for arg in signature.args))
        self.write(')')

    def _declare_top_level_function(self, func: FunctionDeclaration):
        self.write_doc(func.doc_string)
        self.write_function_signature(func.name, func.signature)
        self.writeln(';')

    def _declare_interface(self, interface: InterfaceDef):
        self.write_doc(interface.doc_string)
        self.writeln(f"typedef struct {interface.name} {{")
        with self.with_indent():
            for method in interface.methods:
                self.write_doc(method.doc_string)
                self.declare_function_pointer(method.name, method.signature)
                self.writeln(';')
        self.writeln(f"}} {interface.name};")

    def _declare_opaque_type(self, opaque: OpaqueTypeDef):
        self.write_doc(opaque.doc_string)
        self.writeln(f"typedef struct {opaque.name} {opaque.name};")

    def _write_wrapper_method(
            self, wrapper_name: str, interface_type: IvanType,
            target_method: FunctionDeclaration,
            doc_string: Optional[DocString],
            default_impl: Optional[FunctionBody],
            indirect_vtable: bool
    ):
        """Generate a wrapper method for the specified interface"""
        assert all('vtable' != arg.arg_name for arg in target_method.signature.args)
        self.write_doc(doc_string)
        if indirect_vtable:
            vtable_type = ReferenceType(interface_type, ReferenceKind.IMMUTABLE)
        else:
            vtable_type = interface_type
        self.write_function_signature(wrapper_name, FunctionSignature(
            args=[FunctionArg("vtable", vtable_type), *target_method.signature.args],
            return_type=target_method.signature.return_type
        ))
        self.writeln(' {')
        with self.with_indent() as writer:
            self.declare_function_pointer('func_ptr', target_method.signature)
            writer.write(' = ')
            if indirect_vtable:
                writer.write('vtable->')
            else:
                writer.write('vtable.')
            writer.write(target_method.name)
            writer.writeln(';')

            def call_vtable():
                if target_method.signature.return_type != types.UNIT:
                    writer.write("return ")
                writer.write('(*func_ptr)(')
                writer.write(', '.join(f"{arg.arg_name}" for arg in target_method.signature.args))
                writer.writeln(');')
            if default_impl is None:
                writer.writeln('assert(func_ptr != NULL);')
                call_vtable()
            else:
                writer.writeln("if (func_ptr == NULL) {")
                with self.with_indent():
                    compiler = C11Compiler(
                        writer=self,
                        func_signature=target_method.signature
                    )
                    compiler.compile_body(default_impl)
                writer.writeln("} else {")
                with self.with_indent():
                    call_vtable()
                writer.writeln("}")
        self.writeln('}')
