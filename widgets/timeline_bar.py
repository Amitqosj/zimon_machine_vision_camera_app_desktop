"""Horizontal segmented phase bar: Baseline / Stimulus / Recovery."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class TimelineBar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("TimelineBar")
        self.setMinimumHeight(44)
        self._segments: list[tuple[str, float, QColor]] = [
            ("Baseline", 0.33, QColor("#1ea7ff")),
            ("Stimulus", 0.34, QColor("#00d4ff")),
            ("Recovery", 0.33, QColor("#7c4dff")),
        ]

    def set_segments(
        self, parts: list[tuple[str, float, QColor]] | None = None
    ) -> None:
        if parts:
            self._segments = parts
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(4, 4, -4, -4)
        painter.setPen(QPen(QColor("#1ea7ff"), 1))
        painter.setBrush(QColor("#0b1324"))
        painter.drawRoundedRect(QRectF(r), 12, 12)

        total = sum(w for _, w, _ in self._segments) or 1.0
        x = float(r.x()) + 4
        y = float(r.y()) + 4
        h = float(r.height()) - 8
        wtot = float(r.width()) - 8
        for label, frac, col in self._segments:
            seg_w = max(24.0, wtot * (frac / total))
            seg = QRectF(x, y, seg_w, h)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(col)
            painter.drawRoundedRect(seg, 8, 8)
            painter.setPen(QColor("#eaf4ff"))
            f = QFont(self.font().family(), 10)
            f.setBold(True)
            painter.setFont(f)
            painter.drawText(seg, Qt.AlignmentFlag.AlignCenter, label)
            x += seg_w + 2
