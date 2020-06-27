package net.techcable.ivan.generate

import net.techcable.ivan.NativeType
import net.techcable.ivan.ast.*

class C11Generator(
    override val typeContext: TypeContext,
    override val config: GenerateConfig
) : Generator {
    init {
        require(config.targetLanguage == TargetLanguage.C11)
    }
    private val headerGuard = config.moduleName + "_H"

    override fun generateHeader(out: CodeWriter) {
        out.writeln("#ifndef $headerGuard")
        out.writeln("#define $headerGuard")
        out.writeln()
        // Include headers for standard types
        val stdImports = mutableListOf("<stdint>", "<stdbool>", "<stdlib>")
        val globalImports = ArrayList<String>()
        val localImports = ArrayList<String>()
        for (import in this.config.imports) {
            if (import.startsWith("<std") && import.endsWith('>')) {
                stdImports.add(import)
            } else if (import.startsWith('<') && import.endsWith('>')) {
                globalImports.add(import)
            } else if (import.startsWith('"') && import.endsWith('"')) {
                localImports.add(import)
            } else {
                throw GenerateException(
                        "Invalid import (include) for C: $import",
                        span = null
                )
            }
        }
        if (stdImports.isNotEmpty()) {
            for (import in stdImports) out.writeln("#include $import")
            out.writeln()
        }
        if (globalImports.isNotEmpty()) {
            for (import in globalImports) out.writeln("#include $import")
            out.writeln()
        }
        if (localImports.isNotEmpty()) {
            for (import in localImports) out.writeln("#include $import")
            out.writeln()
        }
    }

    private fun NativeType.printResolved() = typeContext.resolve(this).toC11()

    override fun generateCode(item: PrimaryItem, out: CodeWriter) {
        when (item) {
            is FunctionDef -> declareFunc(item, out)
            is InterfaceDef -> {
                out.writeDocString(item.docString)
                out.declareInterface(
                        name = item.name,
                        writeBody = {
                            for (method in item.methods) {
                                out.writeFuncPointer(method)
                            }
                        }
                )
            }
            is OpaqueTypeDef -> {
                out.writeDocString(item.docString)
                out.writeln("typedef struct ${item.name}")
            }
        }
    }
    private fun CodeWriter.writeFuncPointer(item: FunctionDef) {
        writeDocString(item.docString)
        write(item.returnType.printResolved())
        write(" (*${item.name})")
        item.args.joinTo(
                buffer = this.asAppendable(),
                separator = ", ",
                prefix = "(", postfix = ")",
                transform = {
                    val typeName = it.nativeType.printResolved()
                    "$typeName ${it.name}"
                }
        )
        writeln(";")
    }
    private fun declareFunc(item: FunctionDef, out: CodeWriter) {
        out.writeDocString(item.docString)
        out.writeFunc(
                name = item.name,
                returnTypeName = item.returnType.printResolved(),
                args = item.args.map { ResolvedArg(
                        name = it.name,
                        typeName = it.nativeType.printResolved()
                ) },
                writeBody = null // declaration only
        )
    }

    private fun CodeWriter.writeDocString(
            docString: DocString?
    ) {
        if (docString == null) return
        docString.print(DocString.Style.Javadoc)
                .forEach { this.writeln(it) }
    }

    private fun CodeWriter.declareInterface(
            name: String,
            writeBody: CodeWriter.() -> Unit
    ) {
        this.writeln("typedef struct $name {")
        this.withIndent { writeBody() }
        this.writeln("} $name;")
    }

    private fun CodeWriter.writeFunc(
            name: String,
            args: Iterable<ResolvedArg>,
            returnTypeName: String,
            writeBody: (CodeWriter.() -> Unit)?
    ) {
        this.write("$returnTypeName $name")
        args.joinTo(
                buffer = this.asAppendable(),
                separator = ", ",
                prefix = "(", postfix = ")",
                transform = { "${it.typeName} ${it.name}" }
        )
        if (writeBody != null) {
            this.write('{')
            withIndent { writeBody() }
            this.writeln('}')
        } else {
            this.writeln(';')
        }
    }

    override fun generateFooter(out: CodeWriter) {
        out.writeln("#endif /* $headerGuard */")
        out.writeln() // Trailing newline
    }

    class ResolvedArg(val name: String, val typeName: String)
}