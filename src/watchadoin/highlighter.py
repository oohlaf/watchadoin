import logging

from PySide6.QtGui import QSyntaxHighlighter, QTextDocument, QColor, QTextCharFormat, QFont

from watchadoin.lexer import TaskPaperLexer


log = logging.getLogger()


def format(fg_color=None, bg_color=None, style=[]):
    qt_format = QTextCharFormat()
    if fg_color:
        qt_fg_color = QColor()
        qt_fg_color.setNamedColor(fg_color)
        qt_format.setForeground(qt_fg_color)
    if bg_color:
        qt_bg_color = QColor()
        qt_bg_color.setNamedColor(bg_color)
        qt_format.setBackground(qt_bg_color)
    if "bold" in style:
        qt_format.setFontWeight(QFont.Bold)
    if "italic" in style:
        qt_format.setFontItalic(True)
    if "strikeout" in style:
        qt_format.setFontStrikeOut(True)
    return qt_format


# Supported color names
# https://upload.wikimedia.org/wikipedia/commons/e/e7/SVG1.1_Color_Swatch.svg
STYLES = {
    "DEFAULT": format("white"),
    "INDENT": format("white"),
    "PROJECT": format("lightseagreen"),
    "TASK": format("wheat"),
    "TASK_DOING": format("wheat"),
    "NOTE": format("white"),
    "DOING_DATETIME": format("darksalmon"),
    "TAG_NAME": format("powderblue"),
    "TAG_VALUE_TEXT": format("plum"),
    "TAG_VALUE_DATE": format("darksalmon"),
    "TAG_VALUE_DATETIME": format("darksalmon"),
    "TAG_VALUE_FLOAT": format("mediumturquoise"),
    "TAG_VALUE_INT": format("mediumturquoise"),
    ":": format("white"),
    "@": format("powderblue"),
    "(": format("white"),
    ")": format("white"),
    "|": format("white"),
    "<": format("silver"),
    ">": format("silver"),
    "TASK_ID": format("silver"),
    "TASK_DONE": format("silver", style=["strikeout"]),
    "TAG_NAME_DONE": format("gray", style=["strikeout"]),
    "TAG_VALUE_TEXT_DONE": format("silver", style=["strikeout"]),
    "TAG_VALUE_DATE_DONE": format("silver", style=["strikeout"]),
    "TAG_VALUE_DATETIME_DONE": format("silver", style=["strikeout"]),
    "TAG_VALUE_FLOAT_DONE": format("silver", style=["strikeout"]),
    "TAG_VALUE_INT_DONE": format("silver", style=["strikeout"]),
    "@_DONE": format("gray", style=["strikeout"]),
    "(_DONE": format("gray", style=["strikeout"]),
    ")_DONE": format("gray", style=["strikeout"]),
    "ERROR": format("red"),
}


class TaskPaperHighlighter(QSyntaxHighlighter):
    def __init__(self, parent: QTextDocument) -> None:
        super().__init__(parent)
        self.lexer = TaskPaperLexer()

    def highlightBlock(self, text):
        lineno = self.currentBlock().blockNumber() + 1
        self.setFormat(0, len(text), STYLES["DEFAULT"])

        tokens = list(self.lexer.tokenize_line(text, lineno=lineno))

        # Determine the item type
        item = "EMPTY"
        item_done = False
        for tok in tokens:
            log.debug(tok)
            if tok.type == "DOING":
                item = "TASK_DOING"
                break
            elif tok.type == "PROJECT":
                item = "PROJECT"
                break
            elif tok.type == "NOTE":
                item = "NOTE"
                break
            elif tok.type == "TASK":
                item = "TASK"
            elif tok.type == "TAG_NAME" and tok.value == "done":
                item_done = True

        # Format the line token by token according to type
        for tok in tokens:
            log.debug(tok)
            length = None
            style = "DEFAULT"
            if tok.type == "TEXT":
                style = item
                if item_done and item == "TASK":
                    style += "_DONE"
            elif tok.type.startswith("TAG_VALUE_"):
                style = tok.type
                if item_done and item == "TASK":
                    style += "_DONE"
                if tok.type == "TAG_VALUE_DATE":
                    length = 10
                elif tok.type == "TAG_VALUE_DATETIME":
                    length = 16
                elif tok.type == "TAG_VALUE_FLOAT":
                    length = len(f"{tok.value}")
                elif tok.type == "TAG_VALUE_INT":
                    length = len(f"{tok.value}")
            elif tok.type == "TASK":
                style = item
            elif tok.type == "NOTE":
                style = item
                length = 0
            elif tok.type == "DOING":
                style = "DOING_DATETIME"
                length = 16
            elif tok.type in ["INDENT", "ERROR"]:
                style = tok.type
            elif tok.type in ["EMPTY", "EOF"]:
                style = "DEFAULT"
            else:
                style = tok.type
                if item_done and item == "TASK":
                    style += "_DONE"

            if length is None:
                self.setFormat(tok.index, len(tok.value), STYLES[style])
            else:
                self.setFormat(tok.index, length, STYLES[style])
