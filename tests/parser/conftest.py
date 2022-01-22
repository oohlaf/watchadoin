import io
import pytest

from watchadoin.lexer import TaskPaperLexer
from watchadoin.parser import TaskPaperParser
from watchadoin.visitor import PrintVisitor


def pytest_collect_file(parent, path):
    if path.ext == ".data" and path.basename.startswith("test"):
        return TaskPaperParserFile.from_parent(parent, fspath=path)


class TaskPaperParserFile(pytest.File):
    def collect(self):
        name = ""
        input = ""
        output_lexer = ""
        output_printer = ""
        section = "name"
        lineno = 0
        test_lineno = 0
        with self.fspath.open() as f:
            for line in f:
                if line.startswith("#"):
                    pass
                elif line.startswith("=== testcase"):
                    if section == "output printer":
                        yield TaskPaperParserItem.from_parent(
                            self,
                            input=input,
                            name=name,
                            output_lexer=output_lexer,
                            output_printer=output_printer,
                            lineno=test_lineno,
                        )
                    section = "name"
                    name = ""
                    test_lineno = lineno
                elif line.startswith("<-- input"):
                    if section == "name":
                        section = "input"
                        input = ""
                elif line.startswith("--> output lexer"):
                    if section == "input":
                        section = "output lexer"
                        output_lexer = ""
                elif line.startswith("--> output printer"):
                    if section == "output lexer":
                        section = "output printer"
                        output_printer = ""
                elif line.startswith("=== eof"):
                    if section == "output printer":
                        yield TaskPaperParserItem.from_parent(
                            self,
                            name=name,
                            input=input,
                            output_lexer=output_lexer,
                            output_printer=output_printer,
                            lineno=test_lineno,
                        )
                    return
                else:
                    if section == "name":
                        name = line.strip().replace(" ", "_")
                    elif section == "input":
                        input += line
                    elif section == "output lexer":
                        output_lexer += line
                    elif section == "output printer":
                        output_printer += line
                lineno += 1


class TaskPaperParserItem(pytest.Item):
    def __init__(self, name, parent, input, output_lexer, output_printer, lineno):
        super().__init__(name, parent)
        self.input = input
        self.output_lexer = output_lexer
        self.output_printer = output_printer
        self.lineno = lineno

    def runtest(self):
        lexer = TaskPaperLexer()
        tokens = list(lexer.tokenize_text(self.input, eof=True))
        input_tokens = tokens[:-2 or None]
        result = "\n".join([repr(token) for token in input_tokens]) + "\n"
        if result != self.output_lexer:
            raise TaskPaperLexerException(self, result, self.output_lexer)

        parser = TaskPaperParser()
        token_iter = iter(tokens)
        doc = parser.parse(token_iter)
        output = io.StringIO()
        printer = PrintVisitor(f=output)
        printer.visit(doc)
        result = output.getvalue()
        if result != self.output_printer:
            # For alignment purposes we swap tabs for spaces.
            # The actual conparison above was done with the original tabs.
            raise TaskPaperParserException(self, result.replace("\t", "  "), self.output_printer.replace("\t", "  "))

    def repr_failure(self, excinfo, style=None):
        if isinstance(excinfo.value, TaskPaperLexerException):
            result = excinfo.value.args[1].splitlines()
            expected = excinfo.value.args[2].splitlines()

            diff = len(result) - len(expected)
            if diff < 0:
                result.extend(["" for _ in range(abs(diff))])
            elif diff > 0:
                expected.extend(["" for _ in range(abs(diff))])

            header = "\n".join(["Usecase execution failed", "{:<55}   {:<55}".format("Result:", "Expected:")])
            report = "\n".join(
                [
                    f"{left:<55}   {right:<55}" if left == right else f"{left:<55} ! {right:<55}"
                    for (left, right) in zip(result, expected)
                ]
            )
            return "\n".join([header, report])
        elif isinstance(excinfo.value, TaskPaperParserException):
            result = excinfo.value.args[1].splitlines()
            expected = excinfo.value.args[2].splitlines()

            diff = len(result) - len(expected)
            if diff < 0:
                result.extend(["" for _ in range(abs(diff))])
            elif diff > 0:
                expected.extend(["" for _ in range(abs(diff))])

            header = "\n".join(["Usecase execution failed", "{:<55}   {:<55}".format("Result:", "Expected:")])
            report = "\n".join(
                [
                    f"{left:<55}   {right:<55}" if left == right else f"{left:<55} ! {right:<55}"
                    for (left, right) in zip(result, expected)
                ]
            )
            return "\n".join([header, report])
        else:
            return self._repr_failure_py(excinfo, style)

    def reportinfo(self):
        return self.fspath, self.lineno, f"usecase: {self.name}"


class TaskPaperLexerException(Exception):
    """Custom exception for error reporting after lexing."""


class TaskPaperParserException(Exception):
    """Custom exception for error reporting after parsing."""
