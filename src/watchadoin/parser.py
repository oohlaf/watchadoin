import logging
import sys

from watchadoin.lexer import TaskPaperLexer
from watchadoin.nodes import (
    TaskPaperDocument,
    Empty,
    Project,
    Task,
    Note,
    Doing,
    Tag,
    TextTag,
    DateTag,
    DateTimeTag,
    IntTag,
    FloatTag,
    Text,
)


log = logging.getLogger()


def configure_logging():  # pragma: no cover
    log.setLevel(logging.INFO)
    console_log = logging.StreamHandler(stream=sys.stderr)
    log.addHandler(console_log)


class TaskPaperParser:
    def __init__(self) -> None:
        self.tokens = None
        self.cur_token = None
        self.next_token = None

    def parse(self, tokens) -> TaskPaperDocument:
        self.tokens = tokens
        self.cur_token = None
        self.next_token = None
        return self._parse_document()

    def _advance(self) -> None:
        self.cur_token = self.next_token
        self.next_token = next(self.tokens)

    def _parse_document(self):
        doc = TaskPaperDocument()
        try:
            self._advance()
            self._advance()
            while self.cur_token.type != "EOF":
                if not self._parse_item(parent=doc):
                    log.error("Unexpected input %r", self.cur_token)
                    raise SyntaxError(
                        "Unexpected input",
                        (None, self.cur_token.lineno, self.cur_token.index + 1, self.cur_token.context),
                    )
        except StopIteration:
            pass
        return doc

    def _get_indent_level(self) -> int:
        if self.cur_token.type == "INDENT":
            return len(self.cur_token.value)
        return None

    def _parse_item(self, parent=None):
        return (
            self._parse_empty(parent=parent)
            or self._parse_task(parent=parent)
            or self._parse_project(parent=parent)
            or self._parse_note(parent=parent)
        )

    def _parse_nested_items(self, node):
        while self.cur_token.type in ["INDENT", "EMPTY"]:
            if self.cur_token.type == "EMPTY":
                self._parse_empty(parent=node)
            else:
                tok_level = self._get_indent_level()
                if tok_level >= node.level():
                    self._advance()
                    self._parse_item(parent=node)
                else:
                    break
        return node

    def _parse_empty(self, parent=None) -> Empty | None:
        if self.cur_token.type == "EMPTY":
            self._advance()
            return Empty(parent=parent)

    def _parse_project(self, parent=None) -> Project | None:
        if self.cur_token.type == "PROJECT":
            node = Project(name=self.cur_token.value, parent=parent)
            self._advance()
            if self.cur_token.type == ":":
                self._advance()
            else:
                raise SyntaxError(
                    "Expected a colon after a project name",
                    (None, self.cur_token.lineno, self.cur_token.index + 1, self.cur_token.context),
                )
            if tag := self._parse_tag():
                node.attach_tag(tag)
            return self._parse_nested_items(node)

    def _parse_task(self, parent=None) -> Task | Doing | None:
        if self.cur_token.type == "TASK":
            symbol = self.cur_token.value
            self._advance()
            if self.cur_token.type == "DOING":
                node = Doing(date=self.cur_token.value, symbol=symbol, parent=parent)
                self._advance()
                if self.cur_token.type == "|":
                    self._advance()
                else:
                    raise SyntaxError(
                        "Expected a pipe symbol after a doing date",
                        (None, self.cur_token.lineno, self.cur_token.index + 1, self.cur_token.context),
                    )
            else:
                node = Task(symbol=symbol, parent=parent)
            while self.cur_token.type in ["TEXT", "@"]:
                content = self._parse_text() or self._parse_tag()
                node.add_content(content)
            if self.cur_token.type == "<" and self.next_token == "TASK_ID":
                self._advance()
                node.id = self.cur_token.value
                self._advance()
                if self.cur_token.type == ">":
                    self._advance()
                else:
                    raise SyntaxError(
                        "Expected a closing symbol > after a task ID",
                        (None, self.cur_token.lineno, self.cur_token.index + 1, self.cur_token.context),
                    )
            return self._parse_nested_items(node)

    def _parse_note(self, parent=None) -> Note | None:
        if self.cur_token.type == "NOTE":
            node = Note(parent=parent)
            self._advance()
            while self.cur_token.type in ["TEXT", "@"]:
                content = self._parse_text() or self._parse_tag()
                node.add_content(content)
            return self._parse_nested_items(node)

    def _parse_tag(self) -> Tag | None:
        if self.cur_token.type == "@":
            self._advance()
            if self.cur_token.type == "TAG_NAME":
                name = self.cur_token.value
                self._advance()
            if self.cur_token.type == "(":
                self._advance()
                if self.cur_token.type == "TAG_VALUE_TEXT":
                    node = TextTag(name=name, value=self.cur_token.value)
                elif self.cur_token.type == "TAG_VALUE_DATE":
                    node = DateTag(name=name, value=self.cur_token.value)
                elif self.cur_token.type == "TAG_VALUE_DATETIME":
                    node = DateTimeTag(name=name, value=self.cur_token.value)
                elif self.cur_token.type == "TAG_VALUE_INT":
                    node = IntTag(name=name, value=self.cur_token.value)
                elif self.cur_token.type == "TAG_VALUE_FLOAT":
                    node = FloatTag(name=name, value=self.cur_token.value)
                self._advance()
                if self.cur_token.type == ")":
                    self._advance()
                else:
                    raise SyntaxError(
                        "Expected a closing parenthesis",
                        (None, self.cur_token.lineno, self.cur_token.index + 1, self.cur_token.context),
                    )
            else:
                node = Tag(name=name)
            return node

    def _parse_text(self) -> Text | None:
        if self.cur_token.type == "TEXT":
            node = Text(value=self.cur_token.value)
            self._advance()
            return node


def main():  # pragma: no cover
    configure_logging()
    log.info("start")

    lexer = TaskPaperLexer()
    parser = TaskPaperParser()

    with open("data/example.taskpaper", "r") as f:
        tokens = lexer.tokenize_file(f)
        try:
            doc = parser.parse(tokens)
        except SyntaxError:
            log.exception("Syntax Error")
    log.info("end")


if __name__ == "__main__":  # pragma: no cover
    main()
