"""
Run PyQt6 QCoreApplication + CameraController on a dedicated thread so the same
camera stack as the desktop app can be used by the API process.
"""
from __future__ import annotations

import queue
import sys
import threading
from typing import Any, Callable, Optional, TypeVar

import numpy as np

T = TypeVar("T")

_call_queue: queue.Queue = queue.Queue()
_qt_ready = threading.Event()
_camera_controller: Any = None
_stream_lock = threading.Lock()
_stream_jpeg: Optional[bytes] = None


def _encode_frame_jpeg(arr: np.ndarray) -> None:
    global _stream_jpeg
    try:
        import cv2

        if arr is None or arr.size == 0:
            return
        _, buf = cv2.imencode(".jpg", arr, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
        with _stream_lock:
            _stream_jpeg = buf.tobytes()
    except Exception:
        pass


def _make_stream_callback():
    def on_frame(frame: np.ndarray):
        _encode_frame_jpeg(frame)

    return on_frame


def _qt_main():
    global _camera_controller
    from PyQt6.QtCore import QCoreApplication, QTimer

    app = QCoreApplication(sys.argv)
    from backend.camera_interface import CameraController

    _camera_controller = CameraController()

    def drain():
        try:
            while True:
                fn, args, kwargs, resq = _call_queue.get_nowait()
                try:
                    r = fn(*args, **kwargs)
                    resq.put(("ok", r))
                except Exception as e:
                    resq.put(("err", e))
        except queue.Empty:
            pass

    timer = QTimer()
    timer.timeout.connect(drain)
    timer.start(5)
    _qt_ready.set()
    app.exec()


_qt_thread: Optional[threading.Thread] = None


def start_qt_thread() -> None:
    global _qt_thread
    if _qt_thread is not None and _qt_thread.is_alive():
        return
    _qt_ready.clear()
    _qt_thread = threading.Thread(target=_qt_main, name="zimon-qt", daemon=True)
    _qt_thread.start()
    if not _qt_ready.wait(timeout=120):
        raise RuntimeError("Qt camera thread did not become ready")


def run_on_qt(fn: Callable[..., T], *args, **kwargs) -> T:
    if not _qt_ready.is_set():
        _qt_ready.wait(timeout=120)
    resq: queue.Queue = queue.Queue(maxsize=1)
    _call_queue.put((fn, args, kwargs, resq))
    status, val = resq.get(timeout=180)
    if status == "err":
        raise val
    return val


def list_cameras() -> list[str]:
    return run_on_qt(lambda: _camera_controller.list_cameras())


def refresh_cameras() -> list[str]:
    def _refresh():
        _camera_controller.refresh_cameras()
        return _camera_controller.list_cameras()

    return run_on_qt(_refresh)


def start_preview(camera_name: str) -> bool:
    cb = _make_stream_callback()

    def _start():
        return _camera_controller.start_preview(camera_name, cb)

    return run_on_qt(_start)


def stop_preview(camera_name: str) -> None:
    run_on_qt(lambda: _camera_controller.stop_preview(camera_name))


def list_previewing_cameras() -> list[str]:
    """Camera names with an active preview worker (same as PyQt 'streaming' state)."""

    def _fn():
        if _camera_controller is None:
            return []
        return list(_camera_controller.workers.keys())

    return run_on_qt(_fn)


def set_camera_setting(camera_name: str, setting: str, value: Any) -> bool:
    return run_on_qt(lambda: _camera_controller.set_setting(camera_name, setting, value))


def get_camera_meta(camera_name: str) -> dict[str, Any]:
    def _meta():
        c = _camera_controller
        if camera_name not in c.cameras:
            return {}
        info = c.cameras[camera_name]
        return {
            "type": getattr(info.get("type"), "value", str(info.get("type"))),
            "fps": c.get_current_fps(camera_name),
            "resolution": c.get_resolution(camera_name),
            "zoom": c.get_setting(camera_name, "zoom"),
        }

    return run_on_qt(_meta)


def get_stream_jpeg() -> Optional[bytes]:
    with _stream_lock:
        return _stream_jpeg


def supported_resolutions(camera_name: str) -> list[tuple[int, int]]:
    def _fn():
        return list(_camera_controller.get_supported_resolutions(camera_name))

    return run_on_qt(_fn)


class QtCameraForExperimentRunner:
    """
    Same role as PyQt main.py passing CameraController into ExperimentRunner:
    recording runs on the Qt thread alongside preview.
    """

    def start_recording(self, camera_list: list, prefix: str) -> bool:
        def _fn():
            if _camera_controller is None:
                return False
            if hasattr(_camera_controller, "start_recording"):
                _camera_controller.start_recording(camera_list, prefix)
                return True
            return False

        try:
            return bool(run_on_qt(_fn))
        except Exception:
            return False

    def stop_recording(self) -> None:
        def _fn():
            if _camera_controller is None:
                return
            if hasattr(_camera_controller, "stop_recording"):
                _camera_controller.stop_recording()

        try:
            run_on_qt(_fn)
        except Exception:
            pass
