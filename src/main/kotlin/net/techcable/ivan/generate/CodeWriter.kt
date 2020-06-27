package net.techcable.ivan.generate

class CodeWriter {
    private val buffer: StringBuilder = StringBuilder()
    private val lineBuffer: StringBuilder = StringBuilder()
    private var currentIndent = 0

    fun writeln(): CodeWriter {
        this.write('\n')
        return this
    }
    fun writeln(s: String): CodeWriter {
        this.write(s)
        this.write('\n')
        return this
    }
    fun writeln(c: Char): CodeWriter {
        this.write(c)
        this.writeln()
        return this
    }
    private fun flushBuffer() {
        // flush buffer
        if (lineBuffer.isNotEmpty()) {
            for (i in 0 until currentIndent) {
                buffer.append("    ")
            }
            buffer.append(lineBuffer)
        }
        lineBuffer.clear()
    }
    private fun writeMultiline(s: String, firstNewline: Int) {
        require(firstNewline >= 0)
        flushBuffer()
        var lastWritten = 0
        var newlineIndex = firstNewline
        do {
            for (i in 0 until currentIndent) {
                buffer.append("    ")
            }
            this.buffer.append(s, lastWritten, newlineIndex)
            this.buffer.append('\n')
            lastWritten = newlineIndex + 1
            if (lastWritten >= s.length) return
            newlineIndex = s.indexOf('\n', lastWritten)
        } while (newlineIndex >= 0)
        lineBuffer.append(s, lastWritten, s.length)
    }
    fun write(s: String): CodeWriter {
        val firstNewline = s.indexOf('\n')
        if (firstNewline >= 0) {
            this.writeMultiline(s, firstNewline)
        } else {
            this.lineBuffer.append(s)
        }
        return this
    }
    fun write(c: Char): CodeWriter {
        if (c == '\n') this.flushBuffer()
        buffer.append(c)
        return this
    }

    fun withIndent(func: CodeWriter.() -> Unit) {
        currentIndent += 1
        func()
        currentIndent -= 1
    }

    fun asAppendable(): Appendable {
        return object : Appendable {
            override fun append(csq: CharSequence?): Appendable {
                write(csq.toString())
                return this
            }

            override fun append(csq: CharSequence?, start: Int, end: Int): Appendable {
                write(csq?.subSequence(start, end).toString())
                return this
            }

            override fun append(c: Char): java.lang.Appendable {
                write(c)
                return this
            }
        }
    }

    override fun toString() = this.buffer.toString()
}