from pathlib import Path

from ivan.ast import InterfaceDef
from ivan.ast.parser import parse_module, Parser
from ivan.generate import CodeWriter
from ivan.generate.c11 import C11CodeGenerator
from ivan.types.context import TypeContext


def test_basic_c11_codegen():
    with open(Path(Path(__file__).parent, "basic.ivan"), "rt") as f:
        basic_text = f.read()
    with open(Path(Path(__file__).parent, "basic_generated.h"), "rt") as f:
        generated_text = f.read()
    parsed = parse_module(Parser.parse_str(basic_text), name="ivan.basic")
    context = TypeContext.build_context(parsed)
    generator = C11CodeGenerator(module=parsed, context=context)
    generator.write_header()
    generator.declare_types()

    generator.writeln("// wrappers")
    generator.writeln()

    generator.generate_wrappers()

    generator.write_footer()
    actual_generated_text = str(generator)
    assert generated_text == actual_generated_text
