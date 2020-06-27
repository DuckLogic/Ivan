package net.techcable.ivan.generate

import net.techcable.ivan.ast.PrimaryItem

interface Generator {
    val typeContext: TypeContext
    val config: GenerateConfig

    fun generateHeader(out: CodeWriter)
    fun generateCode(item: PrimaryItem, out: CodeWriter)
    fun generateFooter(out: CodeWriter)
}