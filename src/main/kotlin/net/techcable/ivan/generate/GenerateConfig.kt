package net.techcable.ivan.generate

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * The configuration file for generating code
 */
@Serializable
data class GenerateConfig(
        /**
         * The name of the module that is being compiled.
         *
         * This is expected to be unique throughout the whole name.
         */
        val moduleName: String,
        /**
         * The target language we're generating configs for
         */
        val targetLanguage: TargetLanguage,
        /**
         * How to generate wrapper functions for each interface type
         */
        val interfaceWrappers: Map<String, WrapperConfig> = mapOf(),
        /**
         * Resolved opaque types
         */
        val opaqueTypes: Map<String, String> = mapOf(),
        /**
         * The list of imports.
         *
         * For Rust these are imports, for C these are includes.
         */
        val imports: List<String> = listOf()
)
@Serializable
data class WrapperConfig(
        /**
         * The list of functions that should have wrappers,
         * or `null` if all functions should have wrappers
         */
        val enabled: List<String>? = null,
        /**
         * List of functions that shouldn't have wrappers
         */
        val disabled: List<String> = listOf(),
        /**
         * The prefix to apply to generated wrapper
         * functions. Should really only be used with C ;)
         */
        val prefix: String? = null
)

@Serializable
enum class TargetLanguage {
    @SerialName("c")
    C11,
    Rust
}
