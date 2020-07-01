#
from contextlib import contextmanager
from typing import ContextManager, Optional, Iterable


class CodeWriter:
    current_indent: int
    __slots__ = "_lines", "current_indent", "_current_line_buffer"

    def __init__(self):
        self._lines = []
        self.current_indent = 0
        self._current_line_buffer = []

    def lines(self) -> Iterable[str]:
        yield from self._lines
        if self._current_line_buffer:
            yield ''.join(self._current_line_buffer)

    def writeln(self, s: Optional[str] = None) -> "CodeWriter":
        if s:
            self.write(s)
        self.write('\n')
        return self

    def _flush_buffer(self):
        buffer = self._current_line_buffer
        if buffer:
            self._lines.append(
                "    " * self.current_indent +
                ''.join(buffer)
            )
        buffer.clear()

    def _write_multiline(self, s: str, first_newline: int):
        assert 0 <= first_newline < len(s)
        self._flush_buffer()
        last_written = 0
        newline_index = first_newline
        buffer = []
        indent = "    " * self.current_indent
        while True:
            buffer.append(indent)
            buffer.append(s[last_written:newline_index])
            self._lines.append('\n')
            last_written = newline_index + 1
            if last_written >= len(s): return
            newline_index = s.index('\n', last_written)
            if newline_index < 0: break
        self._current_line_buffer.append(s[last_written:len(s)])

    def write(self, s: str) -> "CodeWriter":
        first_newline = s.index('\n')
        if first_newline >= 0:
            if first_newline == 0:
                self._flush_buffer()
                return self
            self._write_multiline(s, first_newline)
        else:
            self._current_line_buffer.append(s)
        return self

    @contextmanager
    def with_indent(self) -> ContextManager["CodeWriter"]:
        self.current_indent += 1
        try:
            yield self
        finally:
            self.current_indent -= 1

    def __str__(self):
        return '\n'.join(self.lines())
