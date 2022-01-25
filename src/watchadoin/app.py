import logging
import subprocess
import sys

from pathlib import Path

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QImage, qRgba
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtSvg import QSvgRenderer

from watchadoin.codeeditor import CodeEditor


log = logging.getLogger()


def configure_logging():  # pragma: no cover
    log.setLevel(logging.DEBUG)
    console_log = logging.StreamHandler(stream=sys.stderr)
    log.addHandler(console_log)


def create_svg_icon(path, img_type=QImage, dark=True):
    img = QImage(64, 64, QImage.Format_ARGB32)
    img.fill(qRgba(0, 0, 0, 0))
    svgrenderer = QSvgRenderer(path)
    paint = QPainter(img)
    paint.setRenderHint(QPainter.Antialiasing)
    paint.setRenderHint(QPainter.SmoothPixmapTransform)
    svgrenderer.render(paint)
    if dark:
        paint.setCompositionMode(QPainter.CompositionMode_SourceIn)
        paint.fillRect(QRect(-1, -1, 65, 65), QColor(Qt.white))
    paint.end()
    if img_type == QImage:
        return img
    elif img_type == QPixmap:
        return QPixmap.fromImage(img)
    elif img_type == QIcon:
        return QIcon(QPixmap.fromImage(img))


class SystemTray(QSystemTrayIcon):
    ICON_PATH = Path(__file__).parent.parent.parent / "resources" / "icons"

    def __init__(self, app, parent=None):
        self.app = app
        icon = create_svg_icon(str(SystemTray.ICON_PATH / "format-list-checks.svg"), img_type=QIcon)
        super().__init__(icon, parent)
        self.setToolTip("Watcha Doin")
        menu = self.create_menu()
        self.setContextMenu(menu)

    def create_menu(self):
        menu = QMenu()
        self.add_menu_item(menu, "About", self.open_about)
        self.add_menu_item(menu, "To Do", self.open_todo)
        self.add_menu_item(menu, "Restart", self.restart)
        self.add_menu_item(menu, "Quit", self.quit)
        return menu

    def add_menu_item(self, menu, title, handler, icon=None):
        item = menu.addAction(title)
        item.triggered.connect(handler)
        if not icon:
            icon = title.lower().replace(" ", "_")
        if not Path(icon).exists():
            icon = (SystemTray.ICON_PATH / icon).with_suffix(".png")
        item.setIcon(QIcon(str(icon)))

    def quit(self):
        log.info("Quit")
        self.app.quit()

    def restart(self):
        log.info("Restarting")
        subprocess.Popen(["python", __file__])
        sys.exit()

    def open_about(self):
        QMessageBox.about(None, "About Watcha Doin", "Copyright message")

    def open_todo(self):
        editor = CodeEditor()
        editor.setWindowTitle("Code Editor Example")
        with open("data/example.taskpaper", "r") as f:
            data = f.read()
        editor.setPlainText(data)
        editor.show()


def main():  # pragma: no cover
    configure_logging()
    log.info("Start")
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    if SystemTray.isSystemTrayAvailable():
        tray_icon = SystemTray(app)
        tray_icon.show()
    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover
    main()
