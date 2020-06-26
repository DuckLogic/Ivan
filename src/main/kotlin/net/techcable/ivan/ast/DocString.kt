package net.techcable.ivan.ast

/**
 * The documentation for an item
 */
data class DocString(val lines: List<String>, val span: Span) {
    init {
        check(lines.isNotEmpty())
    }

    fun print(style: Style): MutableList<String> {
        return when(style) {
            Style.Javadoc -> {
                val result = mutableListOf("/**")
                for (line in this.lines) {
                    if (line.isEmpty()) {
                        result.add(" *")
                    } else {
                        result.add(" * $line")
                    }
                }
                result.add("*/")
                result
            }
            Style.Rust -> {
                this.lines.map { line -> "/// $line" }.toMutableList()
            }
        }
    }

    enum class Style {
        Javadoc,
        Rust
    }
}