"""Recording / experiment session facade (stubs for backend wiring)."""

from __future__ import annotations

import time
import uuid

from PyQt6.QtCore import QObject, pyqtSignal


class RecorderService(QObject):
    state_changed = pyqtSignal(str)
    tick = pyqtSignal(float)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._running = False
        self._paused = False
        self._t0: float | None = None
        self._accum = 0.0
        self.experiment_id = f"EXP_{time.strftime('%Y_%m%d')}_{uuid.uuid4().hex[:2].upper()}"

    def is_running(self) -> bool:
        return self._running

    def is_paused(self) -> bool:
        return self._paused

    def elapsed_s(self) -> float:
        if not self._running:
            return self._accum
        base = self._accum
        if self._paused or self._t0 is None:
            return base
        return base + (time.perf_counter() - self._t0)

    def start(self) -> None:
        self._running = True
        self._paused = False
        self._t0 = time.perf_counter()
        self.state_changed.emit("running")

    def pause(self) -> None:
        if not self._running or self._paused:
            return
        if self._t0 is not None:
            self._accum += time.perf_counter() - self._t0
        self._paused = True
        self.state_changed.emit("paused")

    def resume(self) -> None:
        if not self._running or not self._paused:
            return
        self._t0 = time.perf_counter()
        self._paused = False
        self.state_changed.emit("running")

    def stop(self) -> None:
        if self._running and not self._paused and self._t0 is not None:
            self._accum += time.perf_counter() - self._t0
        self._running = False
        self._paused = False
        self._t0 = None
        self.state_changed.emit("stopped")

    def reset_session(self) -> None:
        self.stop()
        self._accum = 0.0
        self.experiment_id = f"EXP_{time.strftime('%Y_%m%d')}_{uuid.uuid4().hex[:2].upper()}"
        self.state_changed.emit("idle")
