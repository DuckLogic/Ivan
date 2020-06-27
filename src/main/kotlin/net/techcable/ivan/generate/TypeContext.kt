package net.techcable.ivan.generate

import net.techcable.ivan.NativeType
import net.techcable.ivan.OpaqueType
import net.techcable.ivan.UnresolvedType
import net.techcable.ivan.ast.OpaqueTypeDef

/**
 * Resolves types and interface declarations
 */
class TypeContext(
    opaqueTypes: List<OpaqueType>
) {
    private val opaqueTypes: Map<String, OpaqueType> = opaqueTypes.associateBy { it.name }
    fun resolve(target: NativeType): NativeType {
        if (target !is UnresolvedType) return target
        return opaqueTypes[target.name] ?: throw GenerateException(
            "Unknown type ${target.name}",
            span = target.usageSpan
        )
    }
}
