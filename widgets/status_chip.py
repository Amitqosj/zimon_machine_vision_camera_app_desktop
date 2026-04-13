"""Status pill / badge (Connected, Idle, etc.)."""

from __future__ import annotations

from enum import Enum

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel


class ChipTone(str, Enum):
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"
    NEUTRAL = "neutral"
    ACCENT = "accent"


class StatusChip(QFrame):
    def __init__(
        self,
        text: str,
        *,
        tone: ChipTone = ChipTone.NEUTRAL,
        show_dot: bool = True,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatusChip")
        self.setProperty("tone", tone.value)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 4, 10, 4)
        lay.setSpacing(8)
        self._dot = QLabel("●")
        self._dot.setObjectName("StatusChipDot")
        self._dot.setVisible(show_dot)
        self._txt = QLabel(text)
        self._txt.setObjectName("StatusChipText")
        lay.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self._txt, 0, Qt.AlignmentFlag.AlignVCenter)

    def set_text(self, text: str) -> None:
        self._txt.setText(text)

    def set_tone(self, tone: ChipTone) -> None:
        self.setProperty("tone", tone.value)
        self.style().unpolish(self)
        self.style().polish(self)
