"""Stacked toast notifications (bottom-right overlay on main window)."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject, Qt, QTimer
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget


def normalize_message(text: str) -> str:
    """Collapse whitespace and line breaks into single spaces."""
    if not text:
        return ""
    t = " ".join(text.replace("\r", " ").replace("\n", " ").split())
    return t.strip()


def classify_toast_level(message: str) -> str:
    m = message.lower()
    err_keys = (
        "disconnect",
        "disconnected",
        "error",
        "fail",
        "failed",
        "offline",
        "not configured",
        "no cameras",
        "missing",
        "invalid",
        "not ready",
        "action required",
    )
    warn_keys = ("warning", "incomplete", "attention", "retry", "caution")
    if any(k in m for k in err_keys):
        return "error"
    if any(k in m for k in warn_keys):
        return "warning"
    return "info"


_STYLES = {
    "error": (
        "ToastToast",
        "background-color: rgba(40, 12, 16, 0.96); color: #ffeef0; "
        "border: 1px solid rgba(255, 77, 90, 0.75); border-radius: 12px; padding: 12px 16px;",
    ),
    "warning": (
        "ToastToast",
        "background-color: rgba(40, 32, 8, 0.96); color: #fff6e0; "
        "border: 1px solid rgba(255, 176, 32, 0.65); border-radius: 12px; padding: 12px 16px;",
    ),
    "info": (
        "ToastToast",
        "background-color: rgba(10, 18, 36, 0.96); color: #eaf4ff; "
        "border: 1px solid rgba(30, 167, 255, 0.55); border-radius: 12px; padding: 12px 16px;",
    ),
    "success": (
        "ToastToast",
        "background-color: rgba(8, 28, 20, 0.96); color: #e8fff4; "
        "border: 1px solid rgba(0, 208, 132, 0.55); border-radius: 12px; padding: 12px 16px;",
    ),
}


class ToastManager(QObject):
    """Non-modal toasts anchored bottom-right of a QMainWindow."""

    _MAX_VISIBLE = 6
    _DEFAULT_MS = 5200

    def __init__(self, window: QMainWindow) -> None:
        super().__init__(window)
        self._window = window
        self._host = QWidget(window)
        self._host.setObjectName("ToastHost")
        # Full-window overlay must not paint an opaque background or it covers the whole UI.
        self._host.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._host.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self._host.setAutoFillBackground(False)
        self._host.setStyleSheet("#ToastHost { background: transparent; }")
        self._outer = QVBoxLayout(self._host)
        self._outer.setContentsMargins(20, 20, 24, 96)
        self._outer.addStretch(1)
        self._row = QHBoxLayout()
        self._row.addStretch(1)
        self._col = QVBoxLayout()
        self._col.setSpacing(10)
        self._row.addLayout(self._col)
        self._outer.addLayout(self._row)
        window.installEventFilter(self)
        self._sync_geometry()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: U100
        if obj is self._window and event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Show,
        ):
            self._sync_geometry()
        return False

    def _sync_geometry(self) -> None:
        self._host.setGeometry(0, 0, self._window.width(), self._window.height())
        self._host.raise_()

    def show(self, message: str, level: str = "auto", duration_ms: int | None = None) -> None:
        msg = normalize_message(message)
        if not msg:
            return
        if level == "auto":
            level = classify_toast_level(msg)
        if level not in _STYLES:
            level = "info"
        while self._col.count() >= self._MAX_VISIBLE:
            self._remove_at(0)

        name, css = _STYLES[level]
        frame = QFrame()
        frame.setObjectName(name)
        frame.setStyleSheet(css)
        frame.setMaximumWidth(420)
        frame.setMinimumWidth(260)
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(4, 2, 4, 2)
        lbl = QLabel(msg)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: inherit;")
        lay.addWidget(lbl, 1)
        self._col.addWidget(frame)
        self._sync_geometry()
        self._host.raise_()
        ms = duration_ms if duration_ms is not None else self._DEFAULT_MS
        QTimer.singleShot(ms, lambda f=frame: self._remove_frame(f))

    def _remove_at(self, index: int) -> None:
        it = self._col.itemAt(index)
        if it is None:
            return
        w = it.widget()
        if w is not None:
            self._col.removeWidget(w)
            w.deleteLater()

    def _remove_frame(self, frame: QFrame) -> None:
        self._col.removeWidget(frame)
        frame.deleteLater()
        self._sync_geometry()
