from pathlib import Path

from ivan.ast import InterfaceDef
from ivan.ast.parser import parse_all, Parser
from ivan.generate import CodeWriter
from ivan.generate.c11 import C11CodeGenerator
from ivan.types.context import TypeContext


def test_basic_c11_codegen():
    with open(Path(Path(__file__).parent, "basic.ivan"), "rt") as f:
        basic_text = f.read()
    with open(Path(Path(__file__).parent, "basic_generated.h"), "rt") as f:
        generated_text = f.read()
    parsed = parse_all(Parser.parse_str(basic_text))
    context = TypeContext.build_context(parsed)
    parsed = [item.update_types(context.resolve_type) for item in parsed]
    generator = C11CodeGenerator(writer=CodeWriter(), name="ivan.basic")
    generator.write_header()
    for item in parsed:
        item.visit(generator)
        generator.writer.writeln()

    named_interfaces = {}
    for item in parsed:
        if isinstance(item, InterfaceDef):
            named_interfaces[item.name] = item

    generator.writer.writeln("// wrappers")
    generator.writer.writeln()

    basic_def = named_interfaces["Basic"]
    basic_type = context.resolve_type_name("Basic", basic_def.span)
    for method in basic_def.methods:
        generator.write_wrapper_method(
            f"basic_{method.name}", basic_type, method, indirect_vtable=True
        )
        generator.writer.writeln()

    other_def = named_interfaces["Other"]
    other_type = context.resolve_type_name("Other", other_def.span)
    for method in other_def.methods:
        generator.write_wrapper_method(
            f"other_{method.name}", other_type, method, indirect_vtable=False
        )
        generator.writer.writeln()

    generator.write_footer()
    actual_generated_text = str(generator.writer)
    assert generated_text == actual_generated_text
