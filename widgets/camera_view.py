"""Live camera preview surface (placeholder) with REC badge."""

from __future__ import annotations

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CameraView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ZimonCameraFrame")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        self._video = QLabel()
        self._video.setObjectName("ZimonCameraFrame")
        self._video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._video.setMinimumHeight(360)
        self._video.setText("LIVE CAMERA PREVIEW\n(placeholder)")
        self._video.setStyleSheet(
            "color:#8aa0c6; font-weight:800; letter-spacing:0.6px; font-size:14px;"
        )

        self._rec = QLabel("REC", self._video)
        self._rec.setObjectName("RecBadge")
        self._rec.setVisible(False)
        self._rec.adjustSize()

        lay.addWidget(self._video)

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        self._rec.move(12, 12)

    def set_recording(self, on: bool) -> None:
        self._rec.setVisible(on)

    def set_status_text(self, text: str) -> None:
        self._video.setText(text)

    def set_frame(self, frame: np.ndarray) -> None:
        """Render a camera frame (BGR/RGB/Gray ndarray) into the preview label."""
        if frame is None or frame.size == 0:
            return
        if frame.ndim == 2:
            h, w = frame.shape
            qimg = QImage(frame.data, w, h, frame.strides[0], QImage.Format.Format_Grayscale8)
        elif frame.ndim == 3 and frame.shape[2] == 3:
            # OpenCV cameras usually provide BGR; convert to RGB for Qt.
            rgb = frame[:, :, ::-1].copy()
            h, w, _ = rgb.shape
            qimg = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format.Format_RGB888)
        elif frame.ndim == 3 and frame.shape[2] == 4:
            rgba = frame[:, :, [2, 1, 0, 3]].copy()
            h, w, _ = rgba.shape
            qimg = QImage(rgba.data, w, h, rgba.strides[0], QImage.Format.Format_RGBA8888)
        else:
            return
        pix = QPixmap.fromImage(qimg).scaled(
            self._video.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._video.setPixmap(pix)
        self._video.setText("")

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor(30, 167, 255, 60))
        p.drawRoundedRect(self.rect().adjusted(2, 2, -3, -3), 12, 12)
