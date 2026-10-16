"""A lossless lexical front end; does not tokenize invalid Python with tokenize."""

from __future__ import annotations

import bisect
import unicodedata
from dataclasses import dataclass


@dataclass
class SourceMap:
    original: str
    translated: str
    origins: list[int]

    def __post_init__(self):
        self.original_starts = [0] + [i + 1 for i, c in enumerate(self.original) if c == "\n"]
        self.translated_starts = [0] + [i + 1 for i, c in enumerate(self.translated) if c == "\n"]

    def position(self, line: int, column: int, *, byte_column: bool = True) -> tuple[int, int]:
        line_start = self.translated_starts[min(line - 1, len(self.translated_starts) - 1)]
        if byte_column:
            line_text = self.translated[line_start:].split("\n", 1)[0]
            column = len(line_text.encode("utf-8")[:column].decode("utf-8", "ignore"))
        offset = min(line_start + column, len(self.origins) - 1)
        original_offset = self.origins[max(0, offset)]
        original_line = bisect.bisect_right(self.original_starts, original_offset)
        original_column = original_offset - self.original_starts[original_line - 1]
        if byte_column:
            start = self.original_starts[original_line - 1]
            original_column = len(self.original[start:original_offset].encode("utf-8"))
        return original_line, original_column

    def syntax_error(self, error: SyntaxError, filename: str) -> SyntaxError:
        line, column = self.position(error.lineno or 1, max(0, (error.offset or 1) - 1),
                                     byte_column=False)
        end_line, end_column = self.position(
            error.end_lineno or error.lineno or 1,
            max(0, (error.end_offset or error.offset or 1) - 1), byte_column=False,
        )
        lines = self.original.splitlines(keepends=True)
        text = lines[line - 1] if line <= len(lines) else ""
        return type(error)(error.msg, (filename, line, column + 1, text,
                                       end_line, max(column + 1, end_column + 1)))


class Lexer:
    """Rewrite only name tokens, including expressions inside f/t strings."""

    PREFIXES = {"r", "u", "b", "br", "rb", "f", "fr", "rf", "t", "tr", "rt"}

    def __init__(self, source: str, replacements: dict[str, str], filename: str):
        self.source = source
        self.replacements = replacements
        self.filename = filename
        self.i = 0
        self.parts: list[tuple[str, list[int]]] = []

    def emit(self, text: str, start: int, end: int | None = None):
        end = start + len(text) if end is None else end
        width = max(1, end - start)
        self.parts.append((text, [start + min(j, width - 1) for j in range(len(text))]))

    def copy(self, end: int):
        self.emit(self.source[self.i:end], self.i)
        self.i = end

    @staticmethod
    def name_start(c: str) -> bool:
        return c == "_" or (not c.isdecimal() and c.isidentifier())

    @staticmethod
    def name_continue(c: str) -> bool:
        return ("a" + c).isidentifier()

    def name(self):
        start = self.i
        self.i += 1
        while self.i < len(self.source) and self.name_continue(self.source[self.i]):
            self.i += 1
        word = self.source[start:self.i]
        if self.i < len(self.source) and self.source[self.i] in "\"'" and word.lower() in self.PREFIXES:
            self.emit(word, start)
            self.string(formatted="f" in word.lower() or "t" in word.lower(),
                        raw="r" in word.lower())
            return
        normalized = unicodedata.normalize("NFKC", word)
        if normalized.startswith("__han_"):
            line = self.source.count("\n", 0, start) + 1
            col = start - self.source.rfind("\n", 0, start)
            raise SyntaxError("'__han_' 접두사는 실행기가 사용하는 예약 이름입니다",
                              (self.filename, line, col, self.source.splitlines()[line - 1]))
        self.emit(self.replacements.get(normalized, word), start, self.i)

    def string(self, *, formatted: bool = False, raw: bool = False):
        quote = self.source[self.i]
        delimiter = quote * (3 if self.source.startswith(quote * 3, self.i) else 1)
        self.copy(self.i + len(delimiter))
        while self.i < len(self.source):
            if self.source.startswith(delimiter, self.i):
                self.copy(self.i + len(delimiter))
                return
            c = self.source[self.i]
            if c == "\\":
                if not raw and self.source.startswith("\\N{", self.i):
                    end = self.source.find("}", self.i + 3)
                    self.copy(len(self.source) if end < 0 else end + 1)
                    continue
                # In formatted strings a backslash does not escape a brace.
                self.copy(min(len(self.source), self.i + (1 if formatted and
                          self.source[self.i + 1:self.i + 2] in {"{", "}"} else 2)))
            elif formatted and self.source[self.i:self.i + 2] in {"{{", "}}"}:
                self.copy(self.i + 2)
            elif formatted and c == "{":
                self.field()
            else:
                self.copy(self.i + 1)

    def code(self, *, field: bool = False) -> str:
        brackets: list[str] = []
        while self.i < len(self.source):
            c = self.source[self.i]
            if field and not brackets:
                if c == "}" or c == ":" or (c == "!" and self.source[self.i:self.i + 2] != "!="):
                    return c
                if c == "=" and self.source[self.i:self.i + 2] != "==" and (
                    self.i == 0 or self.source[self.i - 1] not in "=!<>:"
                ):
                    return "="
            if c == "#":
                end = self.source.find("\n", self.i)
                self.copy(len(self.source) if end < 0 else end)
            elif c in "\"'":
                self.string()
            elif self.name_start(c):
                self.name()
            else:
                if c in "([{":
                    brackets.append(c)
                elif c in ")]}":
                    if brackets:
                        brackets.pop()
                self.copy(self.i + 1)
        return ""

    def field(self):
        opening = len(self.parts)
        start = self.i
        self.copy(self.i + 1)
        expression_start = self.i
        ending = self.code(field=True)
        debug = ending == "="
        if debug:
            self.i += 1
            while self.i < len(self.source) and self.source[self.i].isspace():
                self.i += 1
            label = self.source[expression_start:self.i]
            prefix = "{" + repr(label) + "}{"
            self.parts[opening] = (prefix, [start] * len(prefix))
            ending = self.source[self.i:self.i + 1]
        explicit_conversion = ending == "!"
        if explicit_conversion:
            self.copy(min(len(self.source), self.i + 2))
            ending = self.source[self.i:self.i + 1]
        if ending == ":":
            self.copy(self.i + 1)
            self.format_spec()
        elif ending == "}":
            if debug and not explicit_conversion:
                self.emit("!r", self.i, self.i + 1)
            self.copy(self.i + 1)

    def format_spec(self):
        while self.i < len(self.source):
            if self.source[self.i] == "}":
                self.copy(self.i + 1)
                return
            if self.source[self.i] == "{":
                self.field()
            else:
                self.copy(self.i + 1)

    def run(self) -> SourceMap:
        self.code()
        translated = "".join(p[0] for p in self.parts)
        origins = [origin for _, part in self.parts for origin in part]
        origins.append(len(self.source))
        return SourceMap(self.source, translated, origins)
