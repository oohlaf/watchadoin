import pytest

from watchadoin.lexer import TaskPaperLexer


def pytest_collect_file(parent, path):
    if path.ext == ".data" and path.basename.startswith("test"):
        return TaskPaperLexerFile.from_parent(parent, fspath=path)


class TaskPaperLexerFile(pytest.File):
    def collect(self):
        name = ""
        input = ""
        output = ""
        section = "name"
        lineno = 0
        test_lineno = 0
        with self.fspath.open() as f:
            for line in f:
                if line.startswith("#"):
                    pass
                elif line.startswith("=== testcase"):
                    if section == "output":
                        yield TaskPaperLexerItem.from_parent(
                            self,
                            name=name,
                            input=input,
                            output=output,
                            lineno=test_lineno,
                        )
                    section = "name"
                    name = ""
                    test_lineno = lineno
                elif line.startswith("<-- input"):
                    if section == "name":
                        section = "input"
                        input = ""
                elif line.startswith("--> output"):
                    if section == "input":
                        section = "output"
                        output = ""
                elif line.startswith("=== eof"):
                    if section == "output":
                        yield TaskPaperLexerItem.from_parent(
                            self,
                            name=name,
                            input=input,
                            output=output,
                            lineno=test_lineno,
                        )
                    return
                else:
                    if section == "name":
                        name = line.strip().replace(" ", "_")
                    elif section == "input":
                        input += line
                    elif section == "output":
                        output += line
                lineno += 1


class TaskPaperLexerItem(pytest.Item):
    def __init__(self, name, parent, input, output, lineno):
        super().__init__(name, parent)
        self.input = input
        self.output = output
        self.lineno = lineno

    def runtest(self):
        lexer = TaskPaperLexer()
        result = "\n".join([repr(token) for token in lexer.tokenize_text(self.input, eof=False)]) + "\n"
        if result != self.output:
            raise TaskPaperLexerException(self, result, self.output)

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
        else:
            return self._repr_failure_py(excinfo, style)

    def reportinfo(self):
        return self.fspath, self.lineno, f"usecase: {self.name}"


class TaskPaperLexerException(Exception):
    """Custom exception for error reporting."""
