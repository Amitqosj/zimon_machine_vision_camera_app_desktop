"""Background capture thread placeholder (wire to OpenCV / PyPylon later)."""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal


class CameraWorker(QThread):
    """Emits synthetic status ticks; replace frame_grab with real camera loop."""

    status = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        n = 0
        while not self._stop:
            self.msleep(500)
            n += 1
            self.status.emit(f"camera worker heartbeat #{n} (idle)")
