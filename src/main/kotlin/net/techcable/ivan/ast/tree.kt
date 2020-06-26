package net.techcable.ivan.ast

import net.techcable.ivan.NativeType

/**
 * A top-level item
 */
sealed class PrimaryItem {
    abstract val name: String
}

data class FunctionArg(
    val name: String,
    val nativeType: NativeType
)

data class FunctionDef(
    override val name: String,
    val args: List<FunctionArg>,
    val returnType: NativeType,
    val docString: DocString?,
    val span: Span
): PrimaryItem()

/**
 * The definition of an interface
 */
data class InterfaceDef(
    override val name: String,
    val methods: List<FunctionDef>,
    val docString: DocString?,
    val span: Span
): PrimaryItem()

/**
 * The definition of an opaque type
 */
data class OpaqueTypeDef(
    override val name: String,
    val docString: DocString?,
    val span: Span
): PrimaryItem()