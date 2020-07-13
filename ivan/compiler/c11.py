from ivan.ast.expr import ReturnStatement, NullExpr
from ivan.compiler import CodeCompiler, CompileException, IvanType, CompiledExpr, IncompatibleTypeException
from ivan.compiler.types import ReferenceType


class C11CodeCompiler(CodeCompiler):
    def visit_return(self, r: ReturnStatement):
        self.writer.write('return')
        if r.value is None:
            if self.func_signature.is_unit_return:
                raise CompileException(
                    f"Expected a {self.func_signature.return_type!r}, "
                    "but got no return value",
                    span=r.span
                )
        else:
            value = self.compile_expr(r.value, desired_type=self.func_signature.return_type)
            self.writer.write(f' {value.code}')
        self.writer.writeln(';')

    def compile_null_expr(self, expr: NullExpr, desired_type: IvanType) -> CompiledExpr:
        if isinstance(desired_type, ReferenceType) and desired_type.optional:
            return CompiledExpr(
                original=expr,
                static_type=desired_type,
                code="NULL"
            )
        else:
            raise IncompatibleTypeException(
                desired_type=desired_type,
                actual_type="null reference",
                span=expr.span
            )
