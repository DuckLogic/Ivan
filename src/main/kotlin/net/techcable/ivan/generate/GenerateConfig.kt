package net.techcable.ivan

import kotlinx.serialization.Serializable

/**
 * The configuration file for generating code
 */
@Serializable
data class GenerateConfig(
        val targetLanguage: TargetLanguage
)

enum class TargetLanguage {
    C11,
    Rust
}
