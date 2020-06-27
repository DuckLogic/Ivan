package net.techcable.ivan.generate

import net.techcable.ivan.ast.Span

class GenerateException(msg: String, val span: Span?): RuntimeException(msg)