"""Device readiness card for Environment and dashboards."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from services.hardware_service import DeviceInfo, DeviceStatus


def _pill_colors(status: DeviceStatus) -> tuple[str, str]:
    if status == DeviceStatus.CONNECTED or status == DeviceStatus.READY:
        return "#00c853", "CONNECTED" if status == DeviceStatus.CONNECTED else "READY"
    if status == DeviceStatus.WARNING:
        return "#ffb300", "WARNING"
    if status == DeviceStatus.ERROR:
        return "#ff5252", "ERROR"
    return "#ff5252", "DISCONNECTED"


class StatusCard(QFrame):
    test_clicked = pyqtSignal(str)
    retry_clicked = pyqtSignal(str)
    refresh_clicked = pyqtSignal(str)

    def __init__(self, device: DeviceInfo, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ZimonPanel")
        self._key = device.key
        self._title = QLabel(f"{device.icon}  {device.name}")
        self._title.setObjectName("ZimonH1")
        self._detail = QLabel(device.detail or "—")
        self._detail.setStyleSheet("color:#9db3d8;")
        self._detail.setWordWrap(True)

        self._pill = QFrame()
        self._pill.setObjectName("StatusPill")
        ph = QHBoxLayout(self._pill)
        ph.setContentsMargins(10, 6, 10, 6)
        ph.setSpacing(8)
        self._dot = QLabel()
        self._dot.setObjectName("PillDot")
        self._pill_text = QLabel()
        self._pill_text.setStyleSheet("font-weight:800; color:#eaf2ff;")
        ph.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignVCenter)
        ph.addWidget(self._pill_text, 0, Qt.AlignmentFlag.AlignVCenter)

        self._btn_test = QPushButton("Test")
        self._btn_test.setObjectName("ZimonGhostBtn")
        self._btn_test.clicked.connect(lambda: self.test_clicked.emit(self._key))

        self._btn_retry = QPushButton("Retry")
        self._btn_retry.setObjectName("ZimonOutlineBtn")
        self._btn_retry.clicked.connect(lambda: self.retry_clicked.emit(self._key))

        self._btn_refresh = QPushButton("Refresh")
        self._btn_refresh.setObjectName("ZimonOutlineBtn")
        self._btn_refresh.clicked.connect(lambda: self.refresh_clicked.emit(self._key))

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self._btn_test, 1)
        row.addWidget(self._btn_retry, 1)
        row.addWidget(self._btn_refresh, 1)

        grid = QGridLayout(self)
        grid.setContentsMargins(14, 14, 14, 14)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.addWidget(self._title, 0, 0, 1, 2)
        grid.addWidget(self._pill, 0, 2, 1, 1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(self._detail, 1, 0, 1, 3)
        grid.addLayout(row, 2, 0, 1, 3)

        self.apply_device(device)

    def apply_device(self, device: DeviceInfo) -> None:
        self._detail.setText(device.detail or "—")
        color, label = _pill_colors(device.status)
        self._dot.setStyleSheet(
            f"background-color:{color}; border:1px solid rgba(255,255,255,0.35);"
        )
        self._pill_text.setText(label)
