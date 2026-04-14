"""
Process-wide service instances for the API (Arduino + ExperimentRunner).
Camera is owned by qt_bridge on the Qt thread.
"""
from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Any, Optional

from backend.api import settings_store

if TYPE_CHECKING:
    from backend.arduino_controller import ArduinoController
    from backend.experiment_runner import ExperimentRunner

_lock = threading.RLock()
_arduino: Optional["ArduinoController"] = None
_runner: Optional["ExperimentRunner"] = None

_zz_lock = threading.Lock()
_zebrazoom: Any = None
_zebrazoom_key: str = ""

_runner_log = logging.getLogger("zimon.experiment")


def get_arduino():
    global _arduino
    with _lock:
        if _arduino is None:
            from backend.arduino_controller import ArduinoController

            _arduino = ArduinoController(port=None)
        return _arduino


def get_runner():
    global _runner
    with _lock:
        if _runner is None:
            from backend.api.qt_bridge import QtCameraForExperimentRunner
            from backend.experiment_runner import ExperimentRunner

            _runner = ExperimentRunner(
                app=None,
                camera_controller=QtCameraForExperimentRunner(),
                arduino_controller=get_arduino(),
                logger=_runner_log.info,
            )
        return _runner


def invalidate_zebrazoom() -> None:
    global _zebrazoom, _zebrazoom_key
    with _zz_lock:
        _zebrazoom = None
        _zebrazoom_key = ""


def get_zebrazoom():
    """ZebraZoomIntegration using path from config/api_settings.json (Settings UI)."""
    global _zebrazoom, _zebrazoom_key
    data = settings_store.load_settings()
    exe = (data.get("zebrazoom_exe") or "").strip()
    with _zz_lock:
        if _zebrazoom is not None and exe == _zebrazoom_key:
            return _zebrazoom
        from backend.zebrazoom_integration import ZebraZoomIntegration

        _zebrazoom = ZebraZoomIntegration(zebrazoom_path=exe if exe else None)
        _zebrazoom_key = exe
        return _zebrazoom
