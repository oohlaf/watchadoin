import hashlib
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
from watchadoin.parser import TaskPaperParser
from watchadoin.utils import visitor


log = logging.getLogger()


def configure_logging():  # pragma: no cover
    log.setLevel(logging.INFO)
    console_log = logging.StreamHandler(stream=sys.stderr)
    log.addHandler(console_log)


class IdVisitor:
    def __init__(self) -> None:
        self.m = hashlib.md5()
        self.level = 0

    def write_padding(self):
        indent = "\t" * self.level
        self.m.update(indent.encode("utf-8"))

    @visitor.on("node")
    def visit(self, node):
        pass

    @visitor.when(TaskPaperDocument)
    def visit(self, node):
        for child in node.children:
            child.accept(self)

    @visitor.when(Empty)
    def visit(self, node):
        pass

    @visitor.when(Project)
    def visit(self, node):
        self.level += 1
        for child in node.children:
            child.accept(self)
        self.level -= 1

    @visitor.when(Task)
    def visit(self, node):
        # for content in node.contents:
        #    content.accept(self)
        self.level += 1
        for child in node.children:
            child.accept(self)
        self.level -= 1

    @visitor.when(Doing)
    def visit(self, node):
        self.m = hashlib.md5()
        self.write_padding()
        text = f"{node.symbol} "
        text += node.date.isoformat(sep=" ", timespec="minutes")
        text += " | "
        self.m.update(text.encode("utf-8"))
        for content in node.contents:
            content.accept(self)
        node.id = self.m.hexdigest()
        self.level += 1
        for child in node.children:
            child.accept(self)
        self.level -= 1

    @visitor.when(Note)
    def visit(self, node):
        # for content in node.contents:
        #    content.accept(self)
        self.level += 1
        for child in node.children:
            child.accept(self)
        self.level -= 1

    @visitor.when(Text)
    def visit(self, node):
        text = node.value
        self.m.update(text.encode("utf-8"))

    @visitor.when(Tag)
    def visit(self, node):
        text = f"@{node.name}"
        self.m.update(text.encode("utf-8"))

    @visitor.when(TextTag)
    def visit(self, node):
        text = f"@{node.name}({node.value})"
        self.m.update(text.encode("utf-8"))

    @visitor.when(DateTag)
    def visit(self, node):
        text = f"@{node.name}("
        text += node.value.date().isoformat()
        text += ")"
        self.m.update(text.encode("utf-8"))

    @visitor.when(DateTimeTag)
    def visit(self, node):
        text = f"@{node.name}("
        text += node.value.isoformat(sep=" ", timespec="minutes")
        text += ")"
        self.m.update(text.encode("utf-8"))

    @visitor.when(IntTag)
    def visit(self, node):
        text = f"@{node.name}({node.value})"
        self.m.update(text.encode("utf-8"))

    @visitor.when(FloatTag)
    def visit(self, node):
        text = f"@{node.name}({node.value})"
        self.m.update(text.encode("utf-8"))


def main():  # pragma: no cover
    configure_logging()
    log.info("start")

    lexer = TaskPaperLexer()
    parser = TaskPaperParser()
    printer = IdVisitor()

    with open("data/example.taskpaper", "r") as f:
        tokens = lexer.tokenize_file(f)
        try:
            doc = parser.parse(tokens)
        except SyntaxError:
            log.exception("Syntax Error")
    printer.visit(doc)
    log.info("end")


if __name__ == "__main__":  # pragma: no cover
    main()
