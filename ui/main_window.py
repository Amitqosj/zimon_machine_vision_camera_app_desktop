"""ZIMON primary shell: navigation, stacked modules, docks, status bar."""

from __future__ import annotations

import os
import sys

from PyQt6.QtCore import QDateTime, Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from database.auth import clear_active_session
from gui.login_window import LoginWindow
from services.camera_worker import CameraWorker
from services.hardware_service import HardwareService, attach_hardware_refresh
from services.protocol_service import ProtocolService
from services.recorder_service import RecorderService
from pages.adult_page import AdultPage
from pages.environment_page import EnvironmentPage
from pages.experiments_page import ExperimentsPage
from pages.larval_page import LarvalPage
from pages.protocol_builder_page import ProtocolBuilderPage
from ui.navbar import NavBar
from widgets.toast_manager import ToastManager, normalize_message


class ZimonMainWindow(QMainWindow):
    """Post-login laboratory control UI (no authentication screens)."""

    def __init__(self, user_data=None, runner=None, arduino=None, camera=None) -> None:
        super().__init__()
        self.setObjectName("ZimonMainWindow")
        self.user_data = user_data or {}
        self.runner = runner
        self.arduino = arduino
        self.camera = camera

        self._hardware = HardwareService(self)
        self._protocols = ProtocolService(self)
        self._recorder = RecorderService(self)

        self._hardware.bind_live_hardware(
            arduino_connected=self._arduino_connected_fn,
            camera_names=self._camera_names_fn,
        )
        self._hw_timer = attach_hardware_refresh(self._hardware, 2500)

        self._camera_worker: CameraWorker | None = None
        self._nav_screen = "Adult"
        self._accent_alt = False
        self._last_validation_sig = ""

        self.resize(1440, 900)
        self.setMinimumSize(1100, 720)

        self._load_theme()
        self._build_menu_toolbar()
        self._build_central()
        self._build_docks()
        self._build_status()

        self._toast = ToastManager(self)
        self._hardware.log_message.connect(self._on_hardware_log)
        self._hardware.devices_changed.connect(self._sync_status_ready)
        self._protocols.validation_changed.connect(self._on_protocol_validation_toasts)
        self._recorder.state_changed.connect(self._on_recorder_state_toast)

        self._clock = QTimer(self)
        self._clock.timeout.connect(self._tick_clock)
        self._clock.start(1000)
        self._tick_clock()

        self.showMaximized()
        self._sync_window_title()
        self._go_adult()

    # --- backend hook stubs -------------------------------------------------
    def _arduino_connected_fn(self) -> bool:
        try:
            return bool(self.arduino and self.arduino.is_connected())
        except Exception:
            return False

    def _camera_names_fn(self) -> list[str]:
        try:
            if not self.camera:
                return []
            return list(self.camera.list_cameras() or [])
        except Exception:
            return []

    def _load_theme(self) -> None:
        path = os.path.join(os.path.dirname(__file__), "..", "styles", "theme.qss")
        path = os.path.abspath(path)
        with open(path, "r", encoding="utf-8") as f:
            self._base_qss = f.read()
        self.setStyleSheet(self._base_qss)

    def _toggle_accent_theme(self) -> None:
        self._accent_alt = not self._accent_alt
        qss = self._base_qss
        if self._accent_alt:
            qss = qss.replace("#1ea7ff", "#00e5ff").replace("#050b18", "#060d1a").replace(
                "#0b1324", "#0c1528"
            )
        self.setStyleSheet(qss)
        self._navbar.set_theme_icon_sun(not self._accent_alt)

    def _build_menu_toolbar(self) -> None:
        """Shell uses in-app NavBar only — no OS menu strip or extra toolbars above it."""
        mb = self.menuBar()
        mb.clear()
        mb.setNativeMenuBar(False)
        mb.setVisible(False)

    def _build_central(self) -> None:
        wrap = QWidget()
        wrap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._navbar = NavBar(self.user_data)
        self._navbar.page_changed.connect(self._on_nav_page)
        self._navbar.check_environment_clicked.connect(self._go_environment)
        self._navbar.theme_toggle_clicked.connect(self._toggle_accent_theme)
        self._navbar.settings_clicked.connect(self._open_settings)
        self._navbar.help_clicked.connect(self._about)
        prof_menu = QMenu(self)
        prof_menu.addAction("About…", self._about)
        prof_menu.addSeparator()
        self._act_status_bar = prof_menu.addAction("Status bar")
        self._act_status_bar.setCheckable(True)
        self._act_status_bar.setChecked(True)
        self._act_status_bar.toggled.connect(self._set_status_bar_visible)
        prof_menu.addSeparator()
        prof_menu.addAction("Logout…", self._logout)
        self._navbar.set_profile_menu(prof_menu)
        lay.addWidget(self._navbar)

        self._stack = QStackedWidget()
        self._stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._page_adult = AdultPage(self._hardware, self._protocols, self._recorder)
        self._page_larval = LarvalPage(self._hardware, self._protocols, self._recorder)
        self._page_env = EnvironmentPage(self._hardware)
        self._page_protocol = ProtocolBuilderPage(self._protocols)
        self._page_experiments = ExperimentsPage()
        for page in (
            self._page_adult,
            self._page_larval,
            self._page_env,
            self._page_protocol,
            self._page_experiments,
        ):
            page.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )

        self._stack.addWidget(self._page_adult)
        self._stack.addWidget(self._page_larval)
        self._stack.addWidget(self._page_env)
        self._stack.addWidget(self._page_protocol)
        self._stack.addWidget(self._page_experiments)

        lay.addWidget(self._stack, 1)
        self.setCentralWidget(wrap)

    def _on_nav_page(self, index: int) -> None:
        names = ["Adult", "Larval", "Environment", "Protocol Builder", "Experiments"]
        self._stack.setCurrentIndex(index)
        self._nav_screen = names[index] if 0 <= index < len(names) else "Adult"
        self._sync_nav()

    def _open_settings(self) -> None:
        try:
            from gui.settings_dialog import SettingsDialog

            dlg = SettingsDialog(self)
            dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, "Settings", normalize_message(str(e)))

    def _go_adult(self) -> None:
        self._navbar.set_active_index(0)
        self._stack.setCurrentIndex(0)
        self._nav_screen = "Adult"
        self._sync_nav()

    def _go_larval(self) -> None:
        self._navbar.set_active_index(1)
        self._stack.setCurrentIndex(1)
        self._nav_screen = "Larval"
        self._sync_nav()

    def _go_environment(self) -> None:
        self._navbar.set_active_index(2)
        self._stack.setCurrentIndex(2)
        self._nav_screen = "Environment"
        self._sync_nav()

    def _go_protocol(self) -> None:
        self._navbar.set_active_index(3)
        self._stack.setCurrentIndex(3)
        self._nav_screen = "Protocol Builder"
        self._sync_nav()

    def _go_experiments(self) -> None:
        self._navbar.set_active_index(4)
        self._stack.setCurrentIndex(4)
        self._nav_screen = "Experiments"
        self._sync_nav()

    def _sync_nav(self) -> None:
        self._lbl_active.setText(f"Module: {self._nav_screen}")
        self._sync_window_title()
        self._sync_status_ready()

    def _sync_window_title(self) -> None:
        fn = str(self.user_data.get("full_name", "User")).strip() or "User"
        role = str(self.user_data.get("role", "user"))
        self.setWindowTitle(f"ZIMON — {self._nav_screen} | {fn} ({role})")

    def _build_docks(self) -> None:
        self._dock_session = QDockWidget("Session", self)
        self._dock_session.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setContentsMargins(8, 8, 8, 8)
        self._session_proto = QLabel("—")
        self._session_proto.setWordWrap(True)
        self._session_run = QLabel("—")
        self._session_ready = QLabel("—")
        sl.addWidget(QLabel("Active protocol"))
        sl.addWidget(self._session_proto)
        sl.addWidget(QLabel("Experiment ID"))
        sl.addWidget(self._session_run)
        sl.addWidget(QLabel("Hardware"))
        sl.addWidget(self._session_ready)
        sl.addStretch(1)
        refresh = QPushButton("Refresh summary")
        refresh.setObjectName("ZBtnOutline")
        refresh.clicked.connect(self._refresh_session_dock)
        sl.addWidget(refresh)
        self._dock_session.setWidget(sw)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._dock_session)

        self._dock_activity = QDockWidget("Activity", self)
        self._dock_activity.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea
        )
        self._activity = QPlainTextEdit()
        self._activity.setReadOnly(True)
        self._activity.setMaximumBlockCount(4000)
        self._dock_activity.setWidget(self._activity)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._dock_activity)

        # Hidden at launch — navigation is navbar-only; logs still append if docks are shown later.
        self._dock_session.setVisible(False)
        self._dock_activity.setVisible(False)

        self._protocols.model_changed.connect(self._refresh_session_dock)
        self._recorder.state_changed.connect(self._refresh_session_dock)
        self._refresh_session_dock()

    def _toggle_session_dock(self, on: bool) -> None:
        self._dock_session.setVisible(on)

    def _toggle_activity_dock(self, on: bool) -> None:
        self._dock_activity.setVisible(on)

    def _append_activity(self, text: str) -> None:
        msg = normalize_message(text)
        ts = QDateTime.currentDateTime().toString("hh:mm:ss")
        self._activity.appendPlainText(f"[{ts}] {msg}")

    def _on_hardware_log(self, text: str) -> None:
        msg = normalize_message(text)
        self._append_activity(msg)
        self._toast.show(msg, "auto")

    def _on_protocol_validation_toasts(self, items: list[str]) -> None:
        if not items:
            self._last_validation_sig = ""
            return
        sig = "|".join(normalize_message(x) for x in items)
        if sig == self._last_validation_sig:
            return
        self._last_validation_sig = sig
        combined = normalize_message("; ".join(items))
        if combined:
            self._toast.show(combined, "warning")

    def _on_recorder_state_toast(self, state: str) -> None:
        msg = normalize_message(f"Recorder: {state}")
        if msg:
            self._toast.show(msg, "info")

    def _on_camera_worker_status(self, text: str) -> None:
        self._append_activity(text)

    def _refresh_session_dock(self) -> None:
        self._session_proto.setText(self._protocols.model().name)
        self._session_run.setText(self._recorder.experiment_id)
        self._session_ready.setText("YES" if self._hardware.system_ready() else "NO")

    def _set_status_bar_visible(self, visible: bool) -> None:
        self.statusBar().setVisible(visible)

    def _build_status(self) -> None:
        sb = self.statusBar()
        self._st_conn = QLabel("Connection: initializing…")
        self._st_time = QLabel("")
        self._st_ready = QLabel("System ready: —")
        self._lbl_active = QLabel("Module: —")
        for w in (self._st_conn, self._st_ready, self._lbl_active):
            sb.addWidget(w)
        sb.addPermanentWidget(self._st_time)

    def _tick_clock(self) -> None:
        self._st_time.setText(QDateTime.currentDateTime().toString("ddd MMM d  hh:mm:ss AP"))

    def _sync_status_ready(self) -> None:
        ok = self._hardware.system_ready()
        self._st_ready.setText(f"System ready: {'YES' if ok else 'NO'}")
        if self.arduino and self.arduino.is_connected():
            self._st_conn.setText("Arduino: connected")
        elif self.arduino:
            self._st_conn.setText("Arduino: disconnected")
        else:
            self._st_conn.setText("Arduino: not configured")
        cams = self._camera_names_fn()
        if cams:
            self._st_conn.setText(f"{self._st_conn.text()}  |  Cameras: {len(cams)}")
        if self.runner and hasattr(self.runner, "is_running") and self.runner.is_running():
            self._lbl_active.setText(f"Module: {self._nav_screen}  |  Chamber: recording")

    def _start_camera_worker_stub(self) -> None:
        if self._camera_worker and self._camera_worker.isRunning():
            QMessageBox.information(self, "Camera worker", "Already running.")
            return
        self._camera_worker = CameraWorker(self)
        self._camera_worker.status.connect(self._on_camera_worker_status)
        self._camera_worker.start()
        self._append_activity("Camera worker thread started (placeholder).")

    def _about(self) -> None:
        QMessageBox.about(
            self,
            "About ZIMON",
            "<b>ZIMON</b><br/>"
            "Zebrafish Integrated Motion & Optical Neuroanalysis Chamber<br/><br/>"
            "Desktop control shell — connect hardware services for live operation.",
        )

    def _logout(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Logout",
            "Logout and return to the login screen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        clear_active_session()
        self._login = LoginWindow()
        self._login.login_success.connect(self._on_relogin)
        self._login.show()
        self.close()

    def _on_relogin(self, user_data) -> None:
        self.user_data = user_data or {}
        self._login.close()
        self._login = None
        nw = ZimonMainWindow(
            user_data=self.user_data,
            runner=self.runner,
            arduino=self.arduino,
            camera=self.camera,
        )
        nw.show()
        mod = sys.modules.get("main")
        if mod is not None:
            setattr(mod, "MAIN_WINDOW", nw)


# Backward-compatible entry point for main.py
MainWindow = ZimonMainWindow
