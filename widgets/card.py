"""Premium rounded card container."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class ZCard(QFrame):
    """Selectable / hoverable card with optional title, subtitle, and body."""

    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        *,
        object_name: str = "ZCard",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(object_name)
        self._selected = False
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(14, 12, 14, 14)
        self._lay.setSpacing(6)
        self._title_lbl: QLabel | None = None
        self._sub_lbl: QLabel | None = None
        if title:
            self._title_lbl = QLabel(title)
            self._title_lbl.setObjectName("ZCardTitle")
            self._lay.addWidget(self._title_lbl)
        if subtitle:
            self._sub_lbl = QLabel(subtitle)
            self._sub_lbl.setObjectName("ZCardSubtitle")
            self._sub_lbl.setWordWrap(True)
            self._lay.addWidget(self._sub_lbl)

    def body_layout(self) -> QVBoxLayout:
        return self._lay

    def add_body(self, w: QWidget) -> None:
        self._lay.addWidget(w)

    def set_selected(self, on: bool) -> None:
        self._selected = on
        self.setProperty("selected", on)
        self.style().unpolish(self)
        self.style().polish(self)

    def is_selected(self) -> bool:
        return self._selected
