"""Application-wide Qt stylesheet loading (dark / light) with QSettings persistence."""
import os

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

ORG = "ZIMON"
APP = "ZIMON"
KEY = "theme"


def _gui_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def read_theme() -> str:
    s = QSettings(ORG, APP)
    v = s.value(KEY, "dark")
    return "light" if str(v).lower() == "light" else "dark"


def stylesheet_path(theme: str | None = None) -> str:
    t = theme or read_theme()
    name = "styles_light.qss" if t == "light" else "styles.qss"
    return os.path.join(_gui_dir(), name)


def load_application_stylesheet(app: QApplication | None = None) -> None:
    app = app or QApplication.instance()
    if app is None:
        return
    path = stylesheet_path()
    with open(path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())


def toggle_theme_and_reload() -> str:
    s = QSettings(ORG, APP)
    nxt = "light" if read_theme() == "dark" else "dark"
    s.setValue(KEY, nxt)
    load_application_stylesheet()
    return nxt
