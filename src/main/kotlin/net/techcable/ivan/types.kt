package net.techcable.ivan

import net.techcable.ivan.ast.Span
import java.lang.IllegalArgumentException

sealed class NativeType(
    /**
     * The name of the type, as used in Ivan code
     *
     * This doesn't necessarily correspond to a valid type
     * name in either C11 or Rust.
     */
    val name: String
) {
    abstract fun toC11(): String
    abstract fun toRust(): String
}

/**
 * A type that hasn't been resolved
 */
class UnresolvedType(
    name: String,
    val usageSpan: Span
): NativeType(name) {
    override fun toC11() = throw IllegalStateException("Unresolved $this")
    override fun toRust() = throw IllegalStateException("Unresolved $this")

    override fun equals(other: Any?) = other is UnresolvedType
            && other.name == this.name
            && other.usageSpan == this.usageSpan

    override fun hashCode() = this.name.hashCode() xor usageSpan.hashCode()

    override fun toString() = "UnresolvedType(${this.name}, usageSpan=${this.usageSpan})"
}

data class ReferenceType(
    val target: NativeType,
    val kind: ReferenceKind
): NativeType(target.name + kind.text) {
    /*
     * Everything is a pointer in C!
     * TODO: Const vs non-const?
     */
    override fun toC11() = "*${this.target.toC11()}"
    override fun toRust(): String {
        return when (this.kind) {
            /*
             * TODO: Are references always safe to use?
             * This is basically FFI.....
             */
            ReferenceKind.Immutable -> "&${this.target.toRust()}"
            ReferenceKind.Mutable -> "&mut ${this.target.toRust()}"
            ReferenceKind.Owned, ReferenceKind.Raw -> {
                /*
                 * Rust doesn't have a way to handle these natively
                 * We just map them to raw pointers
                 */
                "*mut ${this.target.toRust()}"
            }
        }
    }
}

enum class ReferenceKind(val text: String) {
    Immutable("&"),
    Mutable("&mut"),
    Owned("&own"),
    Raw("&raw")
}


/**
 * An integer type with a fixed bit width
 */
class FixedIntegerType(
    val bits: Int, val signed: Boolean = true
): NativeType(if (signed) "i${bits}" else "u${bits}") {
    private val c11: String = when (bits) {
        8, 16, 32, 64 -> {
            if (signed) {
                "int${bits}_t"
            } else {
                "uint${bits}_t"
            }
        }
        else -> throw IllegalArgumentException("Forbidden #bits: $bits")
    }

    override fun toRust() = name
    override fun toC11() = c11
    override fun equals(other: Any?): Boolean {
        return other is FixedIntegerType
                && other.bits == this.bits
                && other.signed == this.signed
    }
    override fun hashCode(): Int {
        var code = this.bits.hashCode()
        if (this.signed) code *= -1
        return code
    }
    override fun toString() = name
}

class PrimitiveType private constructor(
    name: String,
    private val c11: String,
    private val rust: String
): NativeType(name) {
    override fun toC11() = c11
    override fun toRust() = rust

    override fun equals(other: Any?) = other is PrimitiveType && other.name == this.name
    override fun hashCode() = name.hashCode()
    override fun toString() = name

    companion object {
        @JvmStatic
        val UNIT: PrimitiveType = PrimitiveType(
            name = "unit",
            c11 = "void",
            rust = "()"
        )

        /**
         * The idiomatic way to represent a signed 32-bit integer
         */
        @JvmStatic
        val INT: PrimitiveType = PrimitiveType(
            name = "int",
            c11 = "int",
            rust = "i32" // NOTE: Assumes sizeof(int) == 32
        )

        /**
         * The idiomatic way to represent a byte
         */
        @JvmStatic
        val BYTE: PrimitiveType = PrimitiveType(
            name = "byte",
            c11 = "char",
            rust = "u8"
        )
        @JvmStatic
        val DOUBLE: PrimitiveType = PrimitiveType(
            name = "double",
            c11 = "double",
            rust = "f64"
        )
        @JvmStatic
        val BOOLEAN: PrimitiveType = PrimitiveType(
            name = "bool",
            c11 = "bool",
            rust = "bool"
        )
        @JvmStatic
        val USIZE: PrimitiveType = PrimitiveType(
            name = "usize",
            c11 = "size_t",
            rust = "usize"
        )
        @JvmStatic
        val ISIZE: PrimitiveType = PrimitiveType(
            name = "isize",
            c11 = "intptr_t",
            rust = "isize"
        )
        @JvmStatic
        fun tryParse(name: String): PrimitiveType? {
            return when (name) {
                "unit" -> UNIT
                "int" -> INT
                "byte" -> BYTE
                "double" -> DOUBLE
                "bool" -> BOOLEAN
                "usize" -> USIZE
                "isize" -> ISIZE
                else -> null
            }
        }
    }
}