"""Painted multi-track timeline (phases + stimulus rows)."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget


@dataclass
class TimelineMarker:
    t0: float
    t1: float
    label: str
    color: QColor


@dataclass
class TimelineModel:
    total_s: float
    phase_splits: list[tuple[str, float]]  # (name, duration)
    tracks: dict[str, list[TimelineMarker]]


class TimelineWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(140)
        self._model: TimelineModel | None = None

    def set_model(self, model: TimelineModel | None) -> None:
        self._model = model
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = QColor("#050814")
        border = QColor("#1f2a44")
        painter.fillRect(self.rect(), bg)
        painter.setPen(QPen(border, 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 10, 10)

        if not self._model or self._model.total_s <= 0:
            painter.setPen(QColor("#8aa0c6"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Timeline preview")
            return

        margin_l, margin_r, margin_t, margin_b = 72, 16, 18, 28
        w = self.width() - margin_l - margin_r
        h = self.height() - margin_t - margin_b
        x0 = margin_l
        y0 = margin_t

        # Phase strip
        for name, dur in self._model.phase_splits:
            x1 = x0 + (dur / self._model.total_s) * w
            rect = QRectF(x0, y0, max(1.0, x1 - x0), 18)
            col = QColor("#00aaff") if name.lower().startswith("stim") else QColor("#223154")
            painter.fillRect(rect, col)
            painter.setPen(QColor("#eaf2ff"))
            f = painter.font()
            f.setBold(True)
            painter.setFont(f)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, name)
            f.setBold(False)
            painter.setFont(f)
            x0 = x1

        # Axis
        axis_y = y0 + 18 + 8
        painter.setPen(QPen(QColor("#2a3a5c"), 1))
        painter.drawLine(int(margin_l), int(axis_y), int(margin_l + w), int(axis_y))

        painter.setPen(QColor("#8aa0c6"))
        painter.drawText(int(margin_l), int(self.height() - 10), "0s")
        painter.drawText(
            int(margin_l + w - 40),
            int(self.height() - 10),
            f"{self._model.total_s:.0f}s",
        )

        # Tracks
        track_labels = list(self._model.tracks.keys())
        row_h = max(18.0, (h - 26) / max(1, len(track_labels)))
        y = axis_y + 6
        painter.setFont(QFont(self.font().family(), 10))

        for label in track_labels:
            painter.setPen(QColor("#c7d7f5"))
            painter.drawText(12, int(y + row_h / 2 + 4), label)
            for m in self._model.tracks.get(label, []):
                xa = margin_l + (m.t0 / self._model.total_s) * w
                xb = margin_l + (m.t1 / self._model.total_s) * w
                rr = QRectF(xa, y + 3, max(2.0, xb - xa), row_h - 6)
                painter.fillRect(rr, m.color)
                painter.setPen(QColor(255, 255, 255, 40))
                painter.drawRoundedRect(rr, 4, 4)
            y += row_h
