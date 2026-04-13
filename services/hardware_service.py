"""Hardware readiness and device state (dummy + hook points for real drivers)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class DeviceStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    READY = "ready"
    ERROR = "error"
    WARNING = "warning"


@dataclass
class DeviceInfo:
    key: str
    name: str
    icon: str
    status: DeviceStatus = DeviceStatus.DISCONNECTED
    detail: str = ""
    meta: dict = field(default_factory=dict)


class HardwareService(QObject):
    """Aggregates subsystem state; emits when refreshed."""

    devices_changed = pyqtSignal()
    log_message = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._devices: dict[str, DeviceInfo] = {}
        self._last_check_s: float | None = None
        self._prev_arduino_ok: bool | None = None
        self._prev_camera_count: int | None = None
        self._init_defaults()

    def _init_defaults(self) -> None:
        self._devices = {
            "camera": DeviceInfo("camera", "Camera", "📷", DeviceStatus.CONNECTED, "Top / machine vision"),
            "light": DeviceInfo("light", "Light", "💡", DeviceStatus.READY, "IR / white / RGB"),
            "buzzer": DeviceInfo("buzzer", "Buzzer", "🔊", DeviceStatus.READY, "Tone generator"),
            "vibration": DeviceInfo("vibration", "Vibration", "〰️", DeviceStatus.READY, "PWM shaker"),
            "water": DeviceInfo("water", "Water Flow", "💧", DeviceStatus.WARNING, "Flow sensor idle"),
            "storage": DeviceInfo("storage", "Storage", "🗄️", DeviceStatus.READY, "NVMe scratch"),
            "recorder": DeviceInfo("recorder", "Recording Service", "⏺️", DeviceStatus.READY, "Writer idle"),
            "scheduler": DeviceInfo("scheduler", "Scheduler Engine", "⏱️", DeviceStatus.CONNECTED, "Queue empty"),
        }

    def devices(self) -> list[DeviceInfo]:
        return list(self._devices.values())

    def get(self, key: str) -> DeviceInfo | None:
        return self._devices.get(key)

    def set_status(self, key: str, status: DeviceStatus, detail: str = "") -> None:
        d = self._devices.get(key)
        if not d:
            return
        d.status = status
        if detail:
            d.detail = detail
        self.devices_changed.emit()

    def run_full_diagnostic(self) -> None:
        self.log_message.emit("Diagnostic: probing subsystems…")
        import time

        self._last_check_s = time.time()
        # Placeholder transitions
        self.set_status("water", DeviceStatus.READY, "Prime OK")
        self.log_message.emit("Diagnostic: complete — all channels nominal (simulated).")
        self.devices_changed.emit()

    def last_check_s(self) -> float | None:
        return self._last_check_s

    def summary_counts(self) -> tuple[int, int, int]:
        total = len(self._devices)
        failed = sum(1 for d in self._devices.values() if d.status == DeviceStatus.ERROR)
        disconnected = sum(
            1 for d in self._devices.values() if d.status == DeviceStatus.DISCONNECTED
        )
        return total, failed + disconnected, total - failed - disconnected

    def system_ready(self) -> bool:
        bad = {DeviceStatus.ERROR, DeviceStatus.DISCONNECTED}
        return all(d.status not in bad for d in self._devices.values())

    def test_device(self, key: str) -> None:
        d = self._devices.get(key)
        if not d:
            return
        self.log_message.emit(f"Test pulse sent → {d.name} ({d.key}) [placeholder]")
        self.devices_changed.emit()

    def retry_device(self, key: str) -> None:
        self.log_message.emit(f"Retry connect → {key} [placeholder]")
        self.set_status(key, DeviceStatus.READY, "Re-initialized")

    def refresh_device(self, key: str) -> None:
        self.log_message.emit(f"Refresh → {key} [placeholder]")
        self.devices_changed.emit()

    def bind_live_hardware(
        self,
        *,
        arduino_connected: Callable[[], bool] | None = None,
        camera_names: Callable[[], list[str]] | None = None,
    ) -> None:
        """Optional hooks from real controllers (called periodically by UI)."""
        self._arduino_connected = arduino_connected
        self._camera_names = camera_names

    def apply_live_snapshot(self) -> None:
        """Merge real hardware hints when callbacks are set."""
        arduino_fn = getattr(self, "_arduino_connected", None)
        cam_fn = getattr(self, "_camera_names", None)
        if callable(arduino_fn):
            try:
                ok = bool(arduino_fn())
            except Exception:
                ok = False
            if self._prev_arduino_ok is not None and ok != self._prev_arduino_ok:
                self.log_message.emit("Arduino connected." if ok else "Arduino disconnected.")
            self._prev_arduino_ok = ok
            self.set_status(
                "light",
                DeviceStatus.READY if ok else DeviceStatus.DISCONNECTED,
                "Serial link OK" if ok else "Arduino offline",
            )
            self.set_status(
                "buzzer",
                DeviceStatus.READY if ok else DeviceStatus.DISCONNECTED,
                "Serial link OK" if ok else "Arduino offline",
            )
        if callable(cam_fn):
            try:
                names = cam_fn() or []
            except Exception:
                names = []
            n = len(names)
            if self._prev_camera_count is not None:
                if n == 0 and self._prev_camera_count > 0:
                    self.log_message.emit("No cameras detected.")
                elif n > 0 and self._prev_camera_count == 0:
                    self.log_message.emit(f"Cameras available: {n}.")
            self._prev_camera_count = n
            self.set_status(
                "camera",
                DeviceStatus.CONNECTED if names else DeviceStatus.DISCONNECTED,
                f"{len(names)} device(s)" if names else "No cameras",
            )


def attach_hardware_refresh(service: HardwareService, interval_ms: int = 2000) -> QTimer:
    t = QTimer(service)
    t.setInterval(interval_ms)
    t.timeout.connect(service.apply_live_snapshot)
    t.start()
    return t
