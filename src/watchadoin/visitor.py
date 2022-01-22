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


class PrintVisitor:
    def __init__(self, f="-") -> None:
        if f == "-":
            self.f = sys.stdout
        else:
            self.f = f
        self.level = 0

    def write_padding(self):
        self.f.write("\t" * self.level)

    @visitor.on("node")
    def visit(self, node):
        pass

    @visitor.when(TaskPaperDocument)
    def visit(self, node):
        for child in node.get_children():
            child.accept(self)

    @visitor.when(Empty)
    def visit(self, node):
        self.f.write("\n")

    @visitor.when(Project)
    def visit(self, node):
        self.write_padding()
        self.f.write(f"{node.name}:")
        if node.has_tag():
            self.f.write(" ")
            node.get_tag().accept(self)
        self.f.write("\n")
        self.level += 1
        for child in node.get_children():
            child.accept(self)
        self.level -= 1

    @visitor.when(Task)
    def visit(self, node):
        self.write_padding()
        self.f.write(f"{node.symbol} ")
        for content in node.get_content():
            content.accept(self)
        self.f.write("\n")
        self.level += 1
        for child in node.get_children():
            child.accept(self)
        self.level -= 1

    @visitor.when(Doing)
    def visit(self, node):
        self.write_padding()
        self.f.write(f"{node.symbol} ")
        self.f.write(node.date.isoformat(sep=" ", timespec="minutes"))
        self.f.write(" | ")
        for content in node.get_content():
            content.accept(self)
        self.f.write("\n")
        self.level += 1
        for child in node.get_children():
            child.accept(self)
        self.level -= 1

    @visitor.when(Note)
    def visit(self, node):
        self.write_padding()
        for content in node.get_content():
            content.accept(self)
        self.f.write("\n")
        self.level += 1
        for child in node.get_children():
            child.accept(self)
        self.level -= 1

    @visitor.when(Text)
    def visit(self, node):
        self.f.write(node.value)

    @visitor.when(Tag)
    def visit(self, node):
        self.f.write(f"@{node.name}")

    @visitor.when(TextTag)
    def visit(self, node):
        self.f.write(f"@{node.name}({node.value})")

    @visitor.when(DateTag)
    def visit(self, node):
        self.f.write(f"@{node.name}(")
        self.f.write(node.value.date().isoformat())
        self.f.write(")")

    @visitor.when(DateTimeTag)
    def visit(self, node):
        self.f.write(f"@{node.name}(")
        self.f.write(node.value.isoformat(sep=" ", timespec="minutes"))
        self.f.write(")")

    @visitor.when(IntTag)
    def visit(self, node):
        self.f.write(f"@{node.name}({node.value})")

    @visitor.when(FloatTag)
    def visit(self, node):
        self.f.write(f"@{node.name}({node.value})")


def main():  # pragma: no cover
    configure_logging()
    log.info("start")

    lexer = TaskPaperLexer()
    parser = TaskPaperParser()
    printer = PrintVisitor()

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
