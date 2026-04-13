"""Rounded icon tool buttons with hover glow."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QPushButton, QSizePolicy


class ZIconButton(QPushButton):
    def __init__(
        self,
        icon: QIcon | None = None,
        *,
        tooltip: str = "",
        fixed_size: int = 44,
        checkable: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ZIconButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(fixed_size, fixed_size)
        self.setIconSize(QSize(max(18, fixed_size - 18), max(18, fixed_size - 18)))
        if icon:
            self.setIcon(icon)
        if tooltip:
            self.setToolTip(tooltip)
        self.setCheckable(checkable)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
