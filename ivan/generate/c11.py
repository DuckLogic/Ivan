from __future__ import annotations

from ivan import types
from ivan.ast import AstVisitor, OpaqueTypeDef, InterfaceDef, FunctionDeclaration, FunctionSignature, FunctionArg
from ivan.generate import CodeWriter
from ivan.types import IvanType


class C11CodeGenerator(AstVisitor):
    writer: CodeWriter

    def __init__(self, writer: CodeWriter):
        self.writer = writer

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
        self.write_function_signature(func.name, func.signature)
        self.writer.writeln(';')

    def visit_interface_def(self, interface: InterfaceDef):
        self.writer.writeln(f"typedef struct {interface.name} {{")
        with self.writer.with_indent():
            for method in interface.methods:
                self.declare_function_pointer(method.name, method.signature)
        self.writer.writeln(f"}} {interface.name};")

    def visit_opaque_type_def(self, opaque: OpaqueTypeDef):
        self.writer.writeln(f"typedef struct {opaque.name} {opaque.name};")

    def write_wrapper_method(
            self, wrapper_name: str, interface_type: IvanType,
            target_method: FunctionDeclaration,
            indirect_vtable=True
    ):
        """Generate a wrapper method for the specified interface"""
        assert all('vtable' != arg.arg_name for arg in target_method.signature.args)
        self.write_function_signature(wrapper_name, FunctionSignature(
            args=[FunctionArg("vtable", interface_type), *target_method.signature.args],
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
        self.writer.writeln('};')
