import logging
import re
import sys

from datetime import datetime


log = logging.getLogger()


def configure_logging():  # pragma: no cover
    log.setLevel(logging.INFO)
    console_log = logging.StreamHandler(stream=sys.stderr)
    log.addHandler(console_log)


class Token:
    __slots__ = ("type", "value", "lineno", "index", "context")

    def __init__(self, type=None, value=None, lineno=1, index=0, context=""):
        self.type = type
        self.value = value
        self.lineno = lineno
        self.index = index
        self.context = context

    def __repr__(self):
        return f"Token({self.type!r}, {self.value!r}, {self.lineno}, {self.index})"


class TaskPaperLexer:
    tokens = [
        "PROJECT",
        "TASK",
        "NOTE",
        "EMPTY",
        "INDENT",
        "DOING",
        "TEXT",
        "TAG_NAME",
        "TAG_VALUE_TEXT",
        "TAG_VALUE_DATE",
        "TAG_VALUE_DATETIME",
        "TAG_VALUE_FLOAT",
        "TAG_VALUE_INT",
        "ERROR",
        "EOF",
    ]

    literals = [
        "@",
        ":",
        "(",
        ")",
        "|",
    ]

    _item_patterns = {
        # Line containing whitespace only.
        "EMPTY": re.compile(r"^\s*$"),
        # A task is a bulleted list.
        # A doing task starts with a date and time.
        "TASK": re.compile(r"^(\t*)([-+*])(?:\s([0-9 :-]+)\s(\|))?\s(.*)$"),
        # A project ends with a colon and optional tag.
        "PROJECT": re.compile(r"^(\t*)((?:[^-+*\s]|(?:[-+*]\S)).*):(?:\s+@([^\s()]*)(\(((?:\\\(|\\\)|[^()])*)\))?)?$"),
        # Notes act as a catchall for input
        "NOTE": re.compile(r"^(\t*)(.*)$"),
    }

    _tag_pattern = re.compile(r"(^@|\s@)([\w]*)(\(((?:\\\(|\\\)|[^()])*)\))?")
    _iso_date_pattern = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})(?:\s([0-9]{2}):([0-9]{2}))?")
    _number_pattern = re.compile(
        r"^\s*[+-]?(?:inf(inity)?|nan|(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?)\s*$",
        re.IGNORECASE,
    )
    _dont_strip_pattern = re.compile(r"\t*[-+*]\s$")

    def tokenize_file(self, f, eof=True):
        lineno = 0
        for line in f:
            lineno += 1
            yield from self.tokenize_line(line, lineno)
        if eof:
            # Two times EOF as parser reads current and next token.
            yield Token("EOF", None, 0, 0)
            yield Token("EOF", None, 0, 0)

    def tokenize_text(self, text, eof=True):
        lineno = 0
        for line in text.splitlines():
            lineno += 1
            yield from self.tokenize_line(line, lineno)
        if eof:
            # Two times EOF as parser reads current and next token.
            yield Token("EOF", None, 0, 0)
            yield Token("EOF", None, 0, 0)

    def tokenize_line(self, text, lineno=1):
        if not self._dont_strip_pattern.match(text):
            text = text.rstrip()

        log.debug('Line %i input text: "%s"', lineno, text)

        found = False
        for kind, pattern in self._item_patterns.items():
            if match := pattern.match(text):
                found = True
                if kind == "EMPTY":
                    log.debug("Line %i is whitespace", lineno)
                    yield Token(type=kind, value=text, lineno=lineno, context=text)
                elif kind == "TASK":
                    if match.group(1):
                        yield Token(
                            type="INDENT", value=match.group(1), lineno=lineno, index=match.start(1), context=text
                        )
                    yield Token(type=kind, value=match.group(2), lineno=lineno, index=match.start(2), context=text)
                    if match.group(3):
                        log.debug("Line %i is a doing task", lineno)
                        yield from self._tokenize_doing_date(
                            match.group(3), lineno=lineno, index=match.start(3), context=text
                        )
                        if match.group(4):
                            yield Token(type="|", value="|", lineno=lineno, index=match.start(4), context=text)
                    else:
                        log.debug("Line %i is a task", lineno)
                    if match.group(5):
                        yield from self._tokenize_item_text(
                            match.group(5), lineno=lineno, index=match.start(5), context=text
                        )
                elif kind == "PROJECT":
                    log.debug("Line %i is a project", lineno)
                    if match.group(1):
                        yield Token(
                            type="INDENT", value=match.group(1), lineno=lineno, index=match.start(1), context=text
                        )
                    yield Token(
                        type="PROJECT", value=match.group(2), lineno=lineno, index=match.start(2), context=text
                    )
                    yield Token(type=":", value=":", lineno=lineno, index=match.end(2), context=text)
                    if match.group(3):
                        yield Token(type="@", value="@", lineno=lineno, index=match.start(3) - 1, context=text)
                        yield Token(
                            type="TAG_NAME", value=match.group(3), lineno=lineno, index=match.start(3), context=text
                        )
                        if match.group(4):
                            yield Token(type="(", value="(", lineno=lineno, index=match.start(4), context=text)
                            if match.group(5):
                                yield from self._tokenize_tag_value(
                                    match.group(5), lineno=lineno, index=match.start(5), context=text
                                )
                            else:
                                yield Token(
                                    type="TAG_VALUE_TEXT",
                                    value="",
                                    lineno=lineno,
                                    index=match.end(4) - 1,
                                    context=text,
                                )
                            yield Token(type=")", value=")", lineno=lineno, index=match.end(4) - 1, context=text)
                elif kind == "NOTE":
                    log.debug("Line %i is a note", lineno)
                    if match.group(1):
                        yield Token(
                            type="INDENT", value=match.group(1), lineno=lineno, index=match.start(1), context=text
                        )
                    if match.group(2):
                        yield Token(type="NOTE", value=None, lineno=lineno, index=match.start(2), context=text)
                        yield from self._tokenize_item_text(
                            match.group(2), lineno=lineno, index=match.start(2), context=text
                        )
                else:  # pragma: no cover
                    log.error("No action defined for pattern %s triggered on line %i", kind, lineno)
                break
        if not found:  # pragma: no cover
            # Practically unreachable due to NOTE acting as catch-all.
            log.warning('Line %i contains illegal input: "%s"', lineno, text)
            yield Token(type="ERROR", value="Illegal input", lineno=lineno, context=text)

    def _tokenize_item_text(self, text, lineno=1, index=0, context=""):
        pos = 0
        for match in self._tag_pattern.finditer(text):
            if pos < match.start(1):
                yield Token(
                    type="TEXT",
                    value=text[pos : match.start(1) + 1],
                    lineno=lineno,
                    index=index + pos,
                    context=context,
                )
                yield Token(type="@", value="@", lineno=lineno, index=index + match.start(2) - 1, context=context)
                yield Token(
                    type="TAG_NAME", value=match.group(2), lineno=lineno, index=index + match.start(2), context=context
                )
                if match.group(3):
                    yield Token(type="(", value="(", lineno=lineno, index=index + match.start(3), context=context)
                    if match.group(4):
                        yield from self._tokenize_tag_value(
                            match.group(4), lineno=lineno, index=index + match.start(4), context=context
                        )
                    else:
                        yield Token(
                            type="TAG_VALUE_TEXT",
                            value="",
                            lineno=lineno,
                            index=index + match.end(3) - 1,
                            context=text,
                        )
                    yield Token(type=")", value=")", lineno=lineno, index=index + match.end(3) - 1, context=context)
                pos = match.end()
            if pos == match.start():
                if match.group(1) != "@":
                    yield Token(
                        type="TEXT",
                        value=text[match.start(1) : match.start(1) + 1],
                        lineno=lineno,
                        index=index + pos,
                        context=context,
                    )
                yield Token(type="@", value="@", lineno=lineno, index=index + match.start(2) - 1, context=context)
                yield Token(
                    type="TAG_NAME", value=match.group(2), lineno=lineno, index=index + match.start(2), context=context
                )
                if match.group(3):
                    yield Token(type="(", value="(", lineno=lineno, index=index + match.start(3), context=context)
                    if match.group(4):
                        yield from self._tokenize_tag_value(
                            match.group(4), lineno=lineno, index=index + match.start(4), context=context
                        )
                    else:
                        yield Token(
                            type="TAG_VALUE_TEXT",
                            value="",
                            lineno=lineno,
                            index=index + match.end(3) - 1,
                            context=text,
                        )
                    yield Token(type=")", value=")", lineno=lineno, index=index + match.end(3) - 1, context=context)
                pos = match.end()
        if pos < len(text):
            yield Token(type="TEXT", value=text[pos:], lineno=lineno, index=index + pos, context=context)

    def _tokenize_doing_date(self, text, lineno=1, index=0, context=""):
        match = self._iso_date_pattern.match(text)
        if match.group(1) and match.group(2) and match.group(3) and match.group(4) and match.group(5):
            try:
                dt = datetime(
                    year=int(match.group(1)),
                    month=int(match.group(2)),
                    day=int(match.group(3)),
                    hour=int(match.group(4)),
                    minute=int(match.group(5)),
                )
                yield Token(type="DOING", value=dt, lineno=lineno, index=index, context=context)
            except ValueError:
                log.warning('Line %i position %i contains an invalid date or time: "%s"', lineno, index, context)
                yield Token(
                    type="ERROR", value="Invalid date or time input", lineno=lineno, index=index, context=context
                )
        else:  # pragma: no cover
            # Practically unreachable due to strict date regex.
            log.warning(
                'Line %i position %i does not contain an ISO fomatted date and time: "%s"', lineno, index, context
            )
            yield Token(
                type="ERROR", value="Invalid date and time format", lineno=lineno, index=index, context=context
            )

    def _tokenize_tag_value(self, text, lineno=1, index=0, context=""):
        if match := self._iso_date_pattern.match(text):
            if match.group(1) and match.group(2) and match.group(3):
                if match.group(4) and match.group(5):
                    try:
                        dt = datetime(
                            year=int(match.group(1)),
                            month=int(match.group(2)),
                            day=int(match.group(3)),
                            hour=int(match.group(4)),
                            minute=int(match.group(5)),
                        )
                        yield Token(type="TAG_VALUE_DATETIME", value=dt, lineno=lineno, index=index, context=context)
                    except ValueError:
                        log.warning('Line %i position %i contains an invalid date or time: "%s"', lineno, index, text)
                        yield Token(
                            type="ERROR",
                            value="Invalid date or time input",
                            lineno=lineno,
                            index=index,
                            context=context,
                        )
                else:
                    try:
                        dt = datetime(
                            year=int(match.group(1)),
                            month=int(match.group(2)),
                            day=int(match.group(3)),
                        )
                        yield Token(type="TAG_VALUE_DATE", value=dt, lineno=lineno, index=index, context=context)
                    except ValueError:
                        log.warning('Line %i position %i contains an invalid date: "%s"', lineno, index, text)
                        yield Token(
                            type="ERROR", value="Invalid date input", lineno=lineno, index=index, context=context
                        )
            else:  # pragma: no cover
                # Practically unreachable due to strict date regex.
                log.warning(
                    'Line %i position %i does not contain an ISO fomatted date and time: "%s"', lineno, index, text
                )
                yield Token(
                    type="ERROR", value="Invalid date and time format", lineno=lineno, index=index, context=context
                )
        elif match := self._number_pattern.match(text):
            if "." in text:
                try:
                    yield Token(type="TAG_VALUE_FLOAT", value=float(text), lineno=lineno, index=index, context=context)
                except ValueError:  # pragma: no cover
                    # Practically unreachable due to strict number regex.
                    log.warning(
                        'Line %i position %i does not contain a valid floating point: "%s"', lineno, index, text
                    )
                    yield Token(
                        type="ERROR", value="Invalid floating point", lineno=lineno, index=index, context=context
                    )
            else:
                try:
                    yield Token(type="TAG_VALUE_INT", value=int(text), lineno=lineno, index=index, context=context)
                except ValueError:  # pragma: no cover
                    # Practically unreachable due to strict number regex.
                    log.warning('Line %i position %i does not contain a valid integer: "%s"', lineno, index, text)
                    yield Token(type="ERROR", value="Invalid integer", lineno=lineno, index=index, context=context)
        else:
            yield Token(type="TAG_VALUE_TEXT", value=text, lineno=lineno, index=index, context=context)


def main():  # pragma: no cover
    configure_logging()
    log.info("start")

    lexer = TaskPaperLexer()

    with open("data/example.taskpaper", "r") as f:
        for tok in lexer.tokenize_file(f):
            log.info(tok)


if __name__ == "__main__":  # pragma: no cover
    main()
