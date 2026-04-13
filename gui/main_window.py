from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QGroupBox, QPushButton,
    QCheckBox, QSlider, QSpinBox, QColorDialog, QComboBox, QMessageBox,
    QStackedWidget, QFrame, QScrollArea, QListWidget, QListWidgetItem,
    QGridLayout, QMenu, QButtonGroup, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QDateTime
from PyQt6.QtGui import QAction, QIcon, QImage, QPixmap
import logging
import time
import cv2
import numpy as np
from gui.settings_dialog import SettingsDialog
from gui.analysis_tab import AnalysisTab
from gui.presets_tab import PresetsTab
from backend.camera_interface import CameraType

# Top navbar body stack indices (single recording page for Adult + Larval)
PAGE_RECORDING = 0
PAGE_ENVIRONMENT = 1
PAGE_PROTOCOL = 2
PAGE_EXPERIMENTS = 3
PAGE_ACCOUNT = 4

# Display names (match main nav / shared UI reference)
SCREEN_ADULT = "Adult"
SCREEN_LARVAL = "Larval"
SCREEN_ENVIRONMENT = "Environment"
SCREEN_PROTOCOL_BUILDER = "Protocol Builder"
SCREEN_EXPERIMENTS = "Experiments"
SCREEN_ACCOUNT = "Account"


class MainWindow(QMainWindow):
    def __init__(self, runner=None, arduino=None, camera=None, user_data=None):
        super().__init__()
        self.runner = runner
        self.arduino = arduino
        self.camera = camera
        self.user_data = user_data or {}
        self.logger = logging.getLogger("main_window")

        # Initialize ZebraZoom integration
        try:
            from backend.zebrazoom_integration import ZebraZoomIntegration
            self.zebrazoom = ZebraZoomIntegration()
        except Exception as e:
            self.logger.warning(f"ZebraZoom integration not available: {e}")
            self.zebrazoom = None

        # Widget references for backend integration
        self.ir_slider = None
        self.ir_enable = None
        self.white_slider = None
        self.white_enable = None
        self.pump_slider = None
        self.pump_enable = None
        self.temp_label = None
        self.arduino_status_label = None
        self._footer_clock_label = None
        self._footer_chamber_label = None
        self._footer_temp_label = None
        self._footer_clock_timer = None

        self.vib_slider = None
        self.vib_enable = None
        self.vib_duration = None
        self.vib_delay = None
        self.vib_continuous = None
        self.buzzer_slider = None
        self.buzzer_enable = None
        self.buzzer_duration = None
        self.buzzer_delay = None
        self.buzzer_continuous = None
        self.heater_slider = None
        self.heater_enable = None
        self.heater_duration = None
        self.heater_delay = None
        self.heater_continuous = None
        
        # Temperature update timer
        self.temp_timer = QTimer()
        self.temp_timer.timeout.connect(self._update_temperature)
        self.temp_timer.start(2000)  # Update every 2 seconds
        
        # Experiment timer
        self.experiment_timer = None
        self.experiment_start_time = None
        
        # Camera-related variables
        self.current_camera = None
        self.camera_preview_labels = []  # List of all preview labels (one per tab)
        self.camera_preview_widget = None  # Shared preview widget
        self.camera_settings_widget = None  # Shared settings widget
        self.camera_combo = None  # Main camera combo box (first one created)
        self.camera_combos = []  # List of all camera combo boxes for syncing
        self.camera_status_label = None
        self.camera_fps_label = None
        self.camera_resolution_label = None
        self.camera_zoom_label = None
        self.camera_settings_timer = QTimer()
        self.camera_settings_timer.timeout.connect(self._update_camera_settings_display)
        self.camera_settings_timer.start(500)  # Update every 500ms
        
        # FPS counter variables
        self.fps_frame_times = []  # List of frame timestamps
        self.fps_counter_label = None  # FPS overlay label
        self.current_fps = 0.0

        self._nav_screen_name = SCREEN_ADULT
        self.resize(1400, 900)
        self._build_ui()
        # Start maximized for best experience
        self.showMaximized()
        self._footer_clock_timer = QTimer()
        self._footer_clock_timer.timeout.connect(self._tick_dashboard_footer_clock)
        self._footer_clock_timer.start(1000)
        # Optimize loading - start timers after UI is ready
        QTimer.singleShot(100, self._connect_backend)
        QTimer.singleShot(200, self._init_camera_list)
        QTimer.singleShot(300, self._optimize_performance)

    def _optimize_performance(self):
        """Optimize performance after UI is loaded"""
        try:
            # Reduce camera settings update frequency for better performance
            if hasattr(self, 'camera_settings_timer'):
                self.camera_settings_timer.setInterval(1000)  # Update every 1 second instead of 500ms
            
            # Optimize temperature update frequency
            if hasattr(self, 'temp_timer'):
                self.temp_timer.setInterval(3000)  # Update every 3 seconds instead of 2 seconds
            
            # Enable hardware acceleration for better rendering
            self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, False)
            self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
            
            self.logger.info("Performance optimizations applied")
        except Exception as e:
            self.logger.error(f"Error applying performance optimizations: {e}")

    def _update_camera_settings_display(self):
        """Update camera settings display labels"""
        if not self.camera or not self.current_camera:
            if self.camera_status_label:
                self.camera_status_label.setText("Not connected")
            if self.camera_fps_label:
                self.camera_fps_label.setText("FPS: —")
            if self.camera_resolution_label:
                self.camera_resolution_label.setText("Resolution: —")
            if self.camera_zoom_label:
                self.camera_zoom_label.setText("Zoom: —")
            return
        
        try:
            # Update status
            if self.camera_status_label:
                self.camera_status_label.setText("Connected")
            
            # Update FPS
            if self.camera_fps_label:
                current_fps = self.camera.get_current_fps(self.current_camera)
                if current_fps:
                    self.camera_fps_label.setText(f"FPS: {current_fps:.1f}")
                else:
                    self.camera_fps_label.setText("FPS: —")
            
            # Update Resolution
            if self.camera_resolution_label:
                resolution = self.camera.get_resolution(self.current_camera)
                if resolution:
                    w, h = resolution
                    self.camera_resolution_label.setText(f"Resolution: {w}x{h}")
                else:
                    self.camera_resolution_label.setText("Resolution: —")
            
            # Update Zoom
            if self.camera_zoom_label:
                zoom = self.camera.get_setting(self.current_camera, "zoom")
                if zoom:
                    self.camera_zoom_label.setText(f"Zoom: {zoom:.1f}x")
                else:
                    self.camera_zoom_label.setText("Zoom: —")
                    
        except Exception as e:
            self.logger.error(f"Error updating camera settings display: {e}")

    def _restart_preview_with_new_resolution(self, camera_name: str):
        """Restart camera preview with new resolution - non-blocking"""
        try:
            if self.camera.start_preview(camera_name, self._update_camera_frame):
                self.logger.info(f"Restarted preview for {camera_name} with new resolution")
            else:
                self.logger.error(f"Failed to restart preview for {camera_name}")
        except Exception as e:
            self.logger.error(f"Error restarting preview: {e}")

    # ---------- UI ROOT ----------
    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        uid = self.user_data.get("id")
        self.presets_tab = PresetsTab(self, user_id=uid if uid is not None else None)
        self.analysis_tab = AnalysisTab(self.zebrazoom)

        self._workspace_scroll = QScrollArea()
        self._workspace_scroll.setWidgetResizable(True)
        self._workspace_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._workspace_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._workspace_scroll.setWidget(self._build_workspace_center_page())

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_recording_workspace_page())
        self.pages.addWidget(self._build_environment_page())
        self.pages.addWidget(self._build_protocol_builder_page())
        self.pages.addWidget(self._build_experiments_page())
        self.pages.addWidget(self._build_account_tab())

        root.addWidget(self._build_top_nav_bar(), 0)
        root.addWidget(self.pages, 1)

        self.setCentralWidget(central)
        self._recording_mode = "adult"
        self._sync_recording_nav_title()
        self._sync_window_title()
        QTimer.singleShot(
            0,
            lambda: (self._refresh_workspace_alert_banner(), self._sync_system_ready_badge()),
        )

    def _build_left_assay_panel(self):
        frame = QFrame()
        frame.setObjectName("DashboardSidePanel")
        frame.setFixedWidth(220)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(10, 12, 10, 12)
        lay.setSpacing(8)
        title = QLabel("TOP RECORDING ASSAYS")
        title.setStyleSheet(
            "color: #94a3b8; font-size: 10px; font-weight: 700; letter-spacing: 1px;"
        )
        lay.addWidget(title)
        lst = QListWidget()
        lst.setObjectName("DashboardAssayList")
        for name in (
            "Multi-Well Plate",
            "Larval Reservoir Maze",
            "Alternating T Maze",
            "Open Field Arena",
            "L/D Choice Assay",
        ):
            QListWidgetItem(name, lst)
        lst.setCurrentRow(0)
        lay.addWidget(lst, 1)
        return frame

    def _build_right_dashboard_panel(self):
        frame = QFrame()
        frame.setObjectName("DashboardSidePanel")
        frame.setFixedWidth(200)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(10, 12, 10, 12)
        lay.setSpacing(10)
        pt = QLabel("SELECT WELL PLATE")
        pt.setStyleSheet(
            "color: #94a3b8; font-size: 10px; font-weight: 700; letter-spacing: 1px;"
        )
        lay.addWidget(pt)
        grid = QGridLayout()
        grid.setSpacing(6)
        wells = [("12", 0, 0), ("24", 0, 1), ("48", 1, 0), ("96", 1, 1)]
        for label, r, c in wells:
            b = QPushButton(label)
            b.setFixedHeight(52)
            b.setStyleSheet(
                "font-weight: 700; font-size: 14px; background: rgba(99,102,241,0.15);"
            )
            grid.addWidget(b, r, c)
        lay.addLayout(grid)
        rt = QLabel("RECIPES")
        rt.setStyleSheet(
            "color: #94a3b8; font-size: 10px; font-weight: 700; letter-spacing: 1px;"
        )
        lay.addWidget(rt)
        rlist = QListWidget()
        rlist.setObjectName("DashboardRecipeList")
        for name in (
            "Custom Assay",
            "Larval Locomotion",
            "Anxiety Test",
            "Predator Exposure",
        ):
            QListWidgetItem(name, rlist)
        lay.addWidget(rlist, 1)
        return frame

    def _build_dashboard_status_bar(self):
        bar = QFrame()
        bar.setObjectName("DashboardStatusBar")
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(12, 6, 12, 6)
        self._footer_chamber_label = QLabel("Chamber: Idle")
        self._footer_temp_label = QLabel("Temperature: —")
        self._footer_clock_label = QLabel("")
        for w in (self._footer_chamber_label, self._footer_temp_label):
            hl.addWidget(w)
        hl.addStretch(1)
        hl.addWidget(self._footer_clock_label)
        return bar

    def _tick_dashboard_footer_clock(self):
        if self._footer_clock_label:
            self._footer_clock_label.setText(
                QDateTime.currentDateTime().toString("hh:mm AP  MMM d, yyyy")
            )
        if self._footer_chamber_label and self.runner:
            try:
                if self.runner.is_running():
                    self._footer_chamber_label.setText("Chamber: Recording")
                else:
                    self._footer_chamber_label.setText("Chamber: Idle")
            except Exception:
                self._footer_chamber_label.setText("Chamber: —")

    # ---------- TOP NAV (web-style) ----------
    def _build_top_nav_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("ZimonTopNav")
        bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        bar.setFixedHeight(78)
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(16, 8, 16, 8)
        hl.setSpacing(14)

        brand_icon = QLabel("🧬")
        brand_icon.setObjectName("ZimonNavLogo")
        brand_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_col = QVBoxLayout()
        brand_col.setSpacing(2)
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        zimon = QLabel("ZIMON")
        zimon.setObjectName("ZimonNavTitle")
        title_row.addWidget(zimon)
        check_env = QPushButton("Check environment")
        check_env.setObjectName("ZimonCheckEnvBtn")
        check_env.setToolTip("Open Environment — devices, cameras, and readiness")
        check_env.setCursor(Qt.CursorShape.PointingHandCursor)
        check_env.clicked.connect(self._nav_go_environment)
        title_row.addWidget(check_env, 0, Qt.AlignmentFlag.AlignVCenter)
        title_row.addStretch(1)
        brand_col.addLayout(title_row)
        sub = QLabel("Zebrafish Integrated Motion & Optical N…")
        sub.setObjectName("ZimonNavSubtitle")
        brand_col.addWidget(sub)

        brand_wrap = QHBoxLayout()
        brand_wrap.setSpacing(10)
        brand_wrap.addWidget(brand_icon, 0, Qt.AlignmentFlag.AlignTop)
        brand_wrap.addLayout(brand_col, 1)
        hl.addLayout(brand_wrap, 0)

        hl.addStretch(1)

        pill_wrap = QWidget()
        pill_lay = QHBoxLayout(pill_wrap)
        pill_lay.setContentsMargins(0, 0, 0, 0)
        pill_lay.setSpacing(6)

        def pill(text: str) -> QPushButton:
            b = QPushButton(text)
            b.setObjectName("ZimonNavPill")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            pill_lay.addWidget(b)
            return b

        self._nav_pill_adult = pill("Adult")
        self._nav_pill_larval = pill("Larval")
        self._nav_pill_environment = pill("Environment")
        self._nav_pill_protocol = pill("Protocol Builder")
        self._nav_pill_experiments = pill("Experiments")

        self._nav_route_group = QButtonGroup(self)
        for b in (
            self._nav_pill_adult,
            self._nav_pill_larval,
            self._nav_pill_environment,
            self._nav_pill_protocol,
            self._nav_pill_experiments,
        ):
            self._nav_route_group.addButton(b)
        self._nav_route_group.setExclusive(True)

        self._nav_pill_adult.clicked.connect(
            lambda: self._nav_go_recording("adult") if self._nav_pill_adult.isChecked() else None
        )
        self._nav_pill_larval.clicked.connect(
            lambda: self._nav_go_recording("larval") if self._nav_pill_larval.isChecked() else None
        )
        self._nav_pill_environment.clicked.connect(
            lambda: self._nav_go_environment() if self._nav_pill_environment.isChecked() else None
        )
        self._nav_pill_protocol.clicked.connect(
            lambda: self._nav_go_protocol() if self._nav_pill_protocol.isChecked() else None
        )
        self._nav_pill_experiments.clicked.connect(
            lambda: self._nav_go_experiments() if self._nav_pill_experiments.isChecked() else None
        )

        hl.addWidget(pill_wrap, 0)

        hl.addStretch(1)

        self.arduino_status_label = QLabel("Arduino: …")
        self.arduino_status_label.setObjectName("ZimonNavArduinoChip")
        hl.addWidget(self.arduino_status_label, 0, Qt.AlignmentFlag.AlignVCenter)

        def icon_btn(sym: str, tip: str, slot) -> QPushButton:
            b = QPushButton(sym)
            b.setObjectName("ZimonNavIconBtn")
            b.setFixedSize(40, 40)
            b.setToolTip(tip)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(slot)
            hl.addWidget(b, 0, Qt.AlignmentFlag.AlignVCenter)
            return b

        icon_btn("🔔", "Notifications", self._nav_notifications_stub)
        icon_btn("☀", "Toggle light / dark theme", self._on_toggle_theme)
        icon_btn("⚙", "Settings", self._show_settings)

        full_name = (self.user_data or {}).get("full_name", "User").strip() or "User"
        self._nav_profile_btn = QPushButton(f"  {full_name}  ▾  ")
        self._nav_profile_btn.setObjectName("ZimonNavProfileBtn")
        self._nav_profile_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        menu = QMenu(self)
        act_account = QAction("Account…", self)
        act_account.triggered.connect(self._switch_to_account_page)
        menu.addAction(act_account)
        self._nav_profile_btn.setMenu(menu)
        hl.addWidget(self._nav_profile_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        self._nav_pill_adult.setChecked(True)
        return bar

    def _nav_notifications_stub(self):
        QMessageBox.information(
            self, "Notifications", "No new notifications."
        )

    def _uncheck_nav_pills(self):
        self._nav_route_group.setExclusive(False)
        for b in self._nav_route_group.buttons():
            b.setChecked(False)
        self._nav_route_group.setExclusive(True)

    def _sync_window_title(self):
        """Taskbar / window title: ZIMON — <Screen name> | Welcome, …"""
        fn = (self.user_data or {}).get("full_name", "User")
        fn = str(fn).strip() or "User"
        role = (self.user_data or {}).get("role", "user")
        sec = getattr(self, "_nav_screen_name", SCREEN_ADULT)
        self.setWindowTitle(f"ZIMON — {sec} | Welcome, {fn} ({role})")

    def _set_nav_screen(self, screen_name: str):
        self._nav_screen_name = screen_name
        self._sync_window_title()

    def _nav_go_recording(self, mode: str):
        self._recording_mode = mode
        self.pages.setCurrentIndex(PAGE_RECORDING)
        self._uncheck_nav_pills()
        if mode == "adult":
            self._nav_pill_adult.setChecked(True)
            self._set_nav_screen(SCREEN_ADULT)
        else:
            self._nav_pill_larval.setChecked(True)
            self._set_nav_screen(SCREEN_LARVAL)
        self._sync_recording_nav_title()
        self._refresh_workspace_alert_banner()

    def _nav_go_environment(self):
        self.pages.setCurrentIndex(PAGE_ENVIRONMENT)
        self._uncheck_nav_pills()
        self._nav_pill_environment.setChecked(True)
        self._set_nav_screen(SCREEN_ENVIRONMENT)
        self._refresh_workspace_alert_banner()

    def _nav_go_protocol(self):
        self.pages.setCurrentIndex(PAGE_PROTOCOL)
        self._uncheck_nav_pills()
        self._nav_pill_protocol.setChecked(True)
        self._set_nav_screen(SCREEN_PROTOCOL_BUILDER)

    def _nav_go_experiments(self):
        self.pages.setCurrentIndex(PAGE_EXPERIMENTS)
        self._uncheck_nav_pills()
        self._nav_pill_experiments.setChecked(True)
        self._set_nav_screen(SCREEN_EXPERIMENTS)

    def _switch_to_account_page(self):
        self.pages.setCurrentIndex(PAGE_ACCOUNT)
        self._uncheck_nav_pills()
        self._set_nav_screen(SCREEN_ACCOUNT)

    def _sync_recording_nav_title(self):
        m = getattr(self, "_recording_mode", "adult")
        name = SCREEN_ADULT if m == "adult" else SCREEN_LARVAL
        if getattr(self, "_recording_screen_title", None):
            self._recording_screen_title.setText(name)
        if getattr(self, "_recording_screen_subtitle", None):
            self._recording_screen_subtitle.setText(
                "Multi-well recording, live preview, protocol load, and run controls."
                if m == "adult"
                else "Larval module — assays, cameras, stimuli, and experiment controls."
            )

    def _refresh_workspace_alert_banner(self):
        if not getattr(self, "_workspace_alert_banner", None):
            return
        parts = []
        if not self.arduino or not self.arduino.is_connected():
            parts.append(
                "Arduino not connected — use Settings to connect the serial port. "
                "Lighting and auxiliary controls need the link."
            )
        cams = []
        if self.camera:
            try:
                cams = self.camera.list_cameras() or []
            except Exception:
                cams = []
        if not cams:
            parts.append(
                "No cameras detected — check USB connections and refresh the camera list."
            )
        if parts:
            self._workspace_alert_banner.setText(" ".join(parts))
            self._workspace_alert_banner.show()
        else:
            self._workspace_alert_banner.setText("System ready — hardware linked.")
            self._workspace_alert_banner.show()

    def _build_recording_workspace_page(self) -> QWidget:
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        mid = QHBoxLayout()
        mid.setContentsMargins(8, 0, 8, 0)
        mid.setSpacing(10)
        mid.addWidget(self._build_left_assay_panel(), 0)

        center = QWidget()
        cv = QVBoxLayout(center)
        cv.setContentsMargins(8, 10, 8, 0)
        cv.setSpacing(8)

        self._recording_screen_title = QLabel(SCREEN_ADULT)
        self._recording_screen_title.setObjectName("ZimonScreenTitle")
        cv.addWidget(self._recording_screen_title)
        self._recording_screen_subtitle = QLabel(
            "Multi-well recording, live preview, protocol load, and run controls."
        )
        self._recording_screen_subtitle.setObjectName("ZimonScreenSubtitle")
        self._recording_screen_subtitle.setWordWrap(True)
        cv.addWidget(self._recording_screen_subtitle)

        status_row = QHBoxLayout()
        idle = QLabel("● IDLE")
        idle.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 12px;")
        self._run_protocol_lbl = QLabel("Protocol —")
        self._run_protocol_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self._run_id_lbl = QLabel("Run ID —")
        self._run_id_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        status_row.addWidget(idle)
        status_row.addSpacing(16)
        status_row.addWidget(self._run_protocol_lbl)
        status_row.addSpacing(16)
        status_row.addWidget(self._run_id_lbl)
        status_row.addStretch(1)
        self._run_ready_badge = QLabel("SYSTEM NOT READY")
        self._run_ready_badge.setObjectName("SystemNotReadyBadge")
        status_row.addWidget(self._run_ready_badge)
        cv.addLayout(status_row)

        self._workspace_alert_banner = QLabel()
        self._workspace_alert_banner.setObjectName("WorkspaceAlertBanner")
        self._workspace_alert_banner.setWordWrap(True)
        cv.addWidget(self._workspace_alert_banner)

        cv.addWidget(self._workspace_scroll, 1)
        mid.addWidget(center, 1)
        mid.addWidget(self._build_right_dashboard_panel(), 0)
        outer.addLayout(mid, 1)
        outer.addWidget(self._build_dashboard_status_bar())
        return w

    def _build_environment_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        header = QFrame()
        header.setObjectName("EnvironmentPageHeader")
        hh = QHBoxLayout(header)
        hh.setContentsMargins(20, 14, 20, 12)
        ht = QVBoxLayout()
        t0 = QLabel(SCREEN_ENVIRONMENT)
        t0.setObjectName("ZimonScreenTitle")
        t1 = QLabel("System readiness")
        t1.setStyleSheet("font-size: 20px; font-weight: 700; color: #f8fafc;")
        t2 = QLabel(
            "Live status from devices and API — connect Arduino and cameras in Settings; "
            "use Test actions when hardware is linked."
        )
        t2.setStyleSheet("color: #94a3b8; font-size: 13px;")
        t2.setWordWrap(True)
        ht.addWidget(t0)
        ht.addWidget(t1)
        ht.addWidget(t2)
        hh.addLayout(ht, 1)
        badge = QLabel("ACTION REQUIRED")
        badge.setObjectName("ActionRequiredBadge")
        hh.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)
        lay.addWidget(header)
        lay.addWidget(self._environment_tab(), 1)
        return page

    def _build_protocol_builder_page(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(16, 14, 16, 12)
        l.setSpacing(12)
        hrow = QHBoxLayout()
        title = QLabel(SCREEN_PROTOCOL_BUILDER)
        title.setObjectName("ZimonScreenTitle")
        sub = QLabel(
            "Design phases, attach stimuli, validate, and export JSON — "
            "below: saved presets and library paths for your account."
        )
        sub.setObjectName("ZimonScreenSubtitle")
        sub.setWordWrap(True)
        col = QVBoxLayout()
        col.addWidget(title)
        col.addWidget(sub)
        hrow.addLayout(col, 1)
        tag = QLabel("• Adult module")
        tag.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 600;")
        hrow.addWidget(tag, 0, Qt.AlignmentFlag.AlignTop)
        l.addLayout(hrow)
        warn = QLabel(
            "Hardware incomplete — connect Arduino + camera for full operation."
        )
        warn.setObjectName("ProtocolBuilderWarn")
        warn.setWordWrap(True)
        l.addWidget(warn)
        l.addWidget(self.presets_tab, 1)
        return w

    def _build_experiments_page(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(16, 14, 16, 12)
        l.setSpacing(10)
        top = QHBoxLayout()
        title = QLabel(SCREEN_EXPERIMENTS)
        title.setObjectName("ZimonScreenTitle")
        top.addWidget(title)
        top.addStretch(1)
        refresh = QPushButton("Refresh list")
        refresh.setObjectName("SecondaryOutlineBtn")
        refresh.clicked.connect(self._experiments_refresh_stub)
        top.addWidget(refresh)
        l.addLayout(top)
        hint = QLabel(
            "Browse recordings, playback, and analysis — load videos from disk; "
            "authenticated media URLs follow your API host. Timeline aligns with protocols from Adult or Protocol Builder."
        )
        hint.setObjectName("ZimonScreenSubtitle")
        hint.setWordWrap(True)
        l.addWidget(hint)
        l.addWidget(self.analysis_tab, 1)
        return w

    def _experiments_refresh_stub(self):
        QMessageBox.information(
            self,
            "Experiments",
            "List refresh: use Analysis tab actions to load files from disk.",
        )

    def _account_profile_initials(self, d):
        """Two-letter avatar text from full name or username."""
        name = (d.get("full_name") or "").strip()
        if name:
            parts = name.split()
            if len(parts) >= 2 and parts[0] and parts[1]:
                return (parts[0][0] + parts[1][0]).upper()
            if len(name) >= 2:
                return name[:2].upper()
            return (name[0].upper() + "·") if name else "?"
        u = (d.get("username") or "").strip()
        if len(u) >= 2:
            return u[:2].upper()
        return (u.upper() + "·") if u else "—"

    def _account_profile_add_detail_row(self, parent_layout, value_attr: str, caption: str):
        """One caption / value row inside the details card. Returns the row QFrame."""
        row = QFrame()
        row.setStyleSheet(
            "QFrame { background: transparent; border: none; border-bottom: 1px solid #252830; }"
        )
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 14, 0, 14)
        rl.setSpacing(20)

        cap = QLabel(caption.upper())
        cap.setStyleSheet(
            "color: #7a7d85; font-size: 11px; font-weight: 700; "
            "letter-spacing: 1.2px; min-width: 108px; max-width: 108px;"
        )
        cap.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        rl.addWidget(cap, 0)

        val = QLabel("—")
        val.setStyleSheet(
            "color: #e8e9ea; font-size: 14px; font-weight: 500;"
        )
        val.setWordWrap(True)
        val.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        rl.addWidget(val, 1)
        parent_layout.addWidget(row)
        setattr(self, value_attr, val)
        return row

    def _build_account_tab(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(16, 14, 16, 0)
        outer.setSpacing(10)

        intro = QLabel(SCREEN_ACCOUNT)
        intro.setObjectName("ZimonScreenTitle")
        outer.addWidget(intro)
        intro_sub = QLabel("Profile, session, and sign out.")
        intro_sub.setObjectName("ZimonScreenSubtitle")
        intro_sub.setWordWrap(True)
        outer.addWidget(intro_sub)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #2a2d36;
                border-radius: 12px;
                background: #0f1014;
                top: -1px;
                padding: 4px;
            }
            QTabBar::tab {
                background: #1a1c21;
                color: #9aa0aa;
                padding: 10px 22px;
                border-radius: 8px;
                margin-right: 6px;
                font-weight: 600;
                min-width: 88px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1, stop:1 #7c3aed);
                color: #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background: #24262c;
                color: #e8e9ea;
            }
        """)

        # --- Profile (designed card layout, not plain labels) ---
        profile = QWidget()
        profile_scroll = QScrollArea()
        profile_scroll.setWidgetResizable(True)
        profile_scroll.setFrameShape(QFrame.Shape.NoFrame)
        profile_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        profile_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        profile_scroll.setWidget(profile)

        pl = QVBoxLayout(profile)
        pl.setContentsMargins(16, 20, 16, 20)
        pl.setSpacing(20)

        # Hero card: avatar + identity
        hero = QFrame()
        hero.setObjectName("AccountHeroCard")
        hero.setStyleSheet("""
            QFrame#AccountHeroCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #16181f, stop:1 #101218);
                border: 1px solid #2e3240;
                border-radius: 16px;
            }
        """)
        hero_l = QHBoxLayout(hero)
        hero_l.setContentsMargins(24, 24, 24, 24)
        hero_l.setSpacing(22)

        self._acct_avatar = QLabel("—")
        self._acct_avatar.setFixedSize(80, 80)
        self._acct_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._acct_avatar.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                color: #ffffff;
                font-size: 26px;
                font-weight: 700;
                border-radius: 40px;
                border: 2px solid rgba(255, 255, 255, 0.18);
            }
        """)
        hero_l.addWidget(self._acct_avatar, 0, Qt.AlignmentFlag.AlignTop)

        id_col = QVBoxLayout()
        id_col.setSpacing(8)
        self._acct_headline = QLabel()
        self._acct_headline.setStyleSheet(
            "color: #ffffff; font-size: 22px; font-weight: 700; letter-spacing: -0.3px;"
        )
        id_col.addWidget(self._acct_headline)

        self._acct_handle = QLabel()
        self._acct_handle.setStyleSheet(
            "color: #818cf8; font-size: 14px; font-weight: 600;"
        )
        id_col.addWidget(self._acct_handle)

        self._acct_role_badge = QLabel()
        self._acct_role_badge.setStyleSheet("""
            QLabel {
                background: rgba(99, 102, 241, 0.2);
                color: #a5b4fc;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
                padding: 6px 12px;
                border-radius: 20px;
                border: 1px solid rgba(99, 102, 241, 0.45);
            }
        """)
        self._acct_role_badge.setMaximumWidth(220)
        id_col.addWidget(self._acct_role_badge)
        id_col.addStretch()
        hero_l.addLayout(id_col, 1)

        pl.addWidget(hero)

        # Details card
        details = QFrame()
        details.setObjectName("AccountDetailsCard")
        details.setStyleSheet("""
            QFrame#AccountDetailsCard {
                background: #14161a;
                border: 1px solid #2a2d36;
                border-radius: 14px;
            }
        """)
        dl = QVBoxLayout(details)
        dl.setContentsMargins(20, 18, 20, 8)
        dl.setSpacing(0)

        sec_title = QLabel("Account details")
        sec_title.setStyleSheet(
            "color: #b8bcc8; font-size: 12px; font-weight: 700; "
            "letter-spacing: 2px; padding: 0 0 8px 0;"
        )
        dl.addWidget(sec_title)

        detail_rows = [
            self._account_profile_add_detail_row(dl, "_acct_val_email", "Email"),
            self._account_profile_add_detail_row(dl, "_acct_val_username", "Username"),
            self._account_profile_add_detail_row(
                dl, "_acct_val_member_since", "Member since"
            ),
        ]
        detail_rows[-1].setStyleSheet(
            "QFrame { background: transparent; border: none; }"
        )

        pl.addWidget(details)
        pl.addStretch()

        tabs.addTab(profile_scroll, "Profile")

        # --- Session ---
        session = QWidget()
        sl = QVBoxLayout(session)
        sl.setContentsMargins(16, 20, 16, 16)
        sl.setSpacing(14)

        sbox = QFrame()
        sbox.setObjectName("AccountSessionCard")
        sbox.setStyleSheet("""
            QFrame#AccountSessionCard {
                background: #14161a;
                border: 1px solid #2a2d36;
                border-radius: 14px;
            }
        """)
        sbl = QVBoxLayout(sbox)
        sbl.setContentsMargins(22, 22, 22, 22)
        sbl.setSpacing(14)

        st = QLabel("Session")
        st.setStyleSheet(
            "color: #ffffff; font-size: 16px; font-weight: 700;"
        )
        sbl.addWidget(st)

        hint = QLabel(
            "Sign out to return to the login screen. Unsaved work in this session may be lost."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #a0a4ac; font-size: 13px; line-height: 1.45;")
        sbl.addWidget(hint)

        logout_btn = QPushButton("Log out")
        logout_btn.setMinimumHeight(44)
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5, stop:1 #6366f1);
                color: #ffffff;
                font-weight: 600;
                font-size: 13px;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #818cf8);
            }
            QPushButton:pressed {
                background: #4338ca;
            }
        """)
        logout_btn.clicked.connect(self._logout)
        sbl.addWidget(logout_btn)

        sl.addWidget(sbox)
        sl.addStretch()
        tabs.addTab(session, "Session")

        outer.addWidget(tabs, 1)
        self._refresh_account_profile()
        return page

    def _refresh_account_profile(self):
        """Update Account / Profile from self.user_data."""
        if not getattr(self, "_acct_avatar", None):
            return
        d = self.user_data or {}

        self._acct_avatar.setText(self._account_profile_initials(d))

        full = (d.get("full_name") or "").strip()
        self._acct_headline.setText(full if full else "Guest user")

        user = (d.get("username") or "").strip()
        self._acct_handle.setText(f"@{user}" if user else "No username")

        role = (d.get("role") or "user").strip().lower()
        role_display = role.replace("_", " ").title() if role else "User"
        self._acct_role_badge.setText(role_display.upper())

        if role in ("admin", "administrator"):
            self._acct_role_badge.setStyleSheet("""
                QLabel {
                    background: rgba(245, 158, 11, 0.15);
                    color: #fbbf24;
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 1px;
                    padding: 6px 12px;
                    border-radius: 20px;
                    border: 1px solid rgba(245, 158, 11, 0.45);
                }
            """)
        else:
            self._acct_role_badge.setStyleSheet("""
                QLabel {
                    background: rgba(99, 102, 241, 0.2);
                    color: #a5b4fc;
                    font-size: 11px;
                    font-weight: 700;
                    letter-spacing: 1px;
                    padding: 6px 12px;
                    border-radius: 20px;
                    border: 1px solid rgba(99, 102, 241, 0.45);
                }
            """)

        email = (d.get("email") or "").strip()
        self._acct_val_email.setText(email if email else "—")

        self._acct_val_username.setText(user if user else "—")

        since = d.get("created_at")
        self._acct_val_member_since.setText(str(since) if since else "—")

        if getattr(self, "_nav_profile_btn", None):
            fn = (d.get("full_name") or "User").strip() or "User"
            self._nav_profile_btn.setText(f"  {fn}  ▾  ")

    def _logout(self):
        """Implemented in ui.main_window for desktop session + login flow."""
        pass

    def _on_toggle_theme(self):
        try:
            from gui.theme import toggle_theme_and_reload

            nxt = toggle_theme_and_reload()
            self.logger.info("Theme switched to %s", nxt)
        except Exception as e:
            self.logger.error("Theme toggle failed: %s", e)

    # ---------- ENVIRONMENT TAB ----------
    def _environment_tab(self):
        from PyQt6.QtWidgets import QSizePolicy, QScrollArea
        
        # Create scroll area for the entire tab
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(10)

        # Top row: Camera preview and settings side by side
        top = QHBoxLayout()
        top.setSpacing(14)
        
        # Create camera widgets for this tab
        camera_preview = self._camera_preview_box()
        camera_settings = self._camera_settings_box()
        
        # Set maximum height for camera preview to leave room for controls
        camera_preview.setMaximumHeight(450)
        
        top.addWidget(camera_preview, 3)
        top.addWidget(camera_settings, 2)

        layout.addLayout(top)
        layout.addWidget(self._environment_controls())

        scroll.setWidget(page)
        return scroll

    # ---------- RECORDING WORKSPACE (Adult / Larval) ----------
    def _build_workspace_center_page(self) -> QWidget:
        """Single shared center column: camera, status, stimuli, run controls."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(10)

        top_section = QHBoxLayout()
        top_section.setSpacing(14)

        camera_preview = self._camera_preview_box()
        experiment_status = self._experiment_status_box()
        camera_preview.setMaximumHeight(400)

        top_section.addWidget(camera_preview, 3)
        top_section.addWidget(experiment_status, 2)
        layout.addLayout(top_section)
        layout.addWidget(self._stimuli_controls())

        actions_container = QGroupBox("Run & manual test")
        actions_layout = QVBoxLayout(actions_container)
        actions_layout.setContentsMargins(16, 20, 16, 16)
        actions_layout.setSpacing(12)

        timer_layout = QHBoxLayout()
        timer_layout.setSpacing(10)
        self.experiment_timer_label = QLabel("Duration: 00:00")
        self.experiment_timer_label.setStyleSheet("color: #a0a4ac; font-size: 13px;")
        timer_layout.addWidget(self.experiment_timer_label)
        timer_layout.addStretch()
        actions_layout.addLayout(timer_layout)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addStretch()
        start_btn = QPushButton("▶ Start experiment")
        start_btn.setMinimumWidth(160)
        start_btn.clicked.connect(self._on_start_experiment)
        actions.addWidget(start_btn)
        stop = QPushButton("⏹ Stop")
        stop.setObjectName("Danger")
        stop.setMinimumWidth(100)
        stop.clicked.connect(self._on_stop_experiment)
        stop.setEnabled(False)
        actions.addWidget(stop)

        self.start_btn = start_btn
        self.stop_btn = stop

        actions_layout.addLayout(actions)
        layout.addWidget(actions_container)
        return page

    # ---------- CAMERA ----------
    def _camera_preview_box(self):
        from PyQt6.QtWidgets import QSizePolicy
        box = QGroupBox("Camera Preview")
        box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(8)

        # Camera selection - always create new combo for this widget (Qt limitation)
        # But sync selection across all combos
        camera_select_layout = QHBoxLayout()
        camera_select_label = QLabel("Camera:")
        camera_select_label.setStyleSheet("color: #e8e9ea;")
        
        # Create combo box for this widget - use simple native style
        camera_combo = QComboBox()
        camera_combo.setMinimumWidth(250)
        camera_combo.setMinimumHeight(30)
        camera_combo.setMaxVisibleItems(10)
        camera_combo.setEditable(False)
        camera_combo.currentIndexChanged.connect(lambda idx: self._on_camera_selected(camera_combo.currentText()) if idx >= 0 else None)
        
        # Store reference to main combo (first one created) and add to list
        self.camera_combos.append(camera_combo)
        if self.camera_combo is None:
            self.camera_combo = camera_combo
            self.logger.info(f"Set main camera_combo reference")
        
        # Sync with existing cameras if available
        if self.camera and self.camera.list_cameras():
            cameras = self.camera.list_cameras()
            camera_combo.blockSignals(True)
            camera_combo.clear()
            camera_combo.addItems(cameras)
            if self.current_camera and self.current_camera in cameras:
                index = camera_combo.findText(self.current_camera)
                if index >= 0:
                    camera_combo.setCurrentIndex(index)
            camera_combo.blockSignals(False)
            self.logger.info(f"Synced new combo with {len(cameras)} cameras")
        
        # Refresh button
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Refresh camera list")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #1a1c21;
                border: 1px solid #2a2d36;
                border-radius: 4px;
                padding: 4px 8px;
                color: #e8e9ea;
                min-width: 30px;
                max-width: 30px;
            }
            QPushButton:hover {
                background: #24262c;
                border-color: #6366f1;
                color: #ffffff;
            }
        """)
        refresh_btn.clicked.connect(self._refresh_camera_list)
        
        camera_select_layout.addWidget(camera_select_label)
        camera_select_layout.addWidget(camera_combo, 1)
        camera_select_layout.addWidget(refresh_btn)
        layout.addLayout(camera_select_layout)

        # Preview container with FPS overlay
        preview_container = QWidget()
        preview_container.setObjectName("CameraPreviewContainer")
        preview_container.setStyleSheet("""
            QWidget#CameraPreviewContainer {
                background: #0d0f13;
                border: 1px solid #2a2d36;
                border-radius: 12px;
            }
        """)
        preview_container_layout = QVBoxLayout(preview_container)
        preview_container_layout.setContentsMargins(0, 0, 0, 0)
        preview_container_layout.setSpacing(0)
        
        # Preview label - create new and add to list
        preview = QLabel("No camera selected")
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setObjectName("CameraPlaceholder")
        preview.setMinimumHeight(250)
        preview.setScaledContents(False)  # We handle scaling manually
        # Add to list of preview labels so we can update all of them
        self.camera_preview_labels.append(preview)
        preview_container_layout.addWidget(preview, 1)
        
        # FPS counter overlay (positioned absolutely over preview)
        if not self.fps_counter_label:
            fps_counter = QLabel("FPS: 0.0", preview_container)
            fps_counter.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
            fps_counter.setStyleSheet("""
                QLabel {
                    color: #22d3ee;
                    font-weight: bold;
                    font-size: 12px;
                    padding: 2px 6px;
                    background: rgba(0, 0, 0, 180);
                    border-radius: 4px;
                }
            """)
            fps_counter.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.fps_counter_label = fps_counter
        
        layout.addWidget(preview_container, 1)
        
        return box

    def _camera_settings_box(self):
        from PyQt6.QtWidgets import QSizePolicy
        box = QGroupBox("Camera Settings")
        # Use Preferred vertical policy so it doesn't stretch excessively
        box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(8)  # Reduced spacing

        # Camera status indicator
        status_layout = QHBoxLayout()
        status_indicator = QLabel("●")
        status_indicator.setStyleSheet("color: #22d3ee; font-size: 12px;")
        status_text = QLabel("Not connected")
        status_text.setStyleSheet("color: #e8e9ea; font-weight: 500;")
        self.camera_status_label = status_text
        status_layout.addWidget(status_indicator)
        status_layout.addWidget(status_text)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Separator
        separator = QLabel("")
        separator.setStyleSheet("background: #2a2d36; min-height: 1px; max-height: 1px;")
        layout.addWidget(separator)

        # Current settings display (hide exposure/gain since using auto mode)
        self.camera_fps_label = QLabel("FPS: —")
        self.camera_resolution_label = QLabel("Resolution: —")
        self.camera_zoom_label = QLabel("Zoom: —")
        
        for label in [self.camera_fps_label, self.camera_resolution_label, self.camera_zoom_label]:
            label.setStyleSheet("padding: 6px 0px; color: #e8e9ea; font-size: 11px;")
        
        layout.addWidget(self.camera_fps_label)
        layout.addWidget(self.camera_resolution_label)
        layout.addWidget(self.camera_zoom_label)
        
        # Separator
        separator2 = QLabel("")
        separator2.setStyleSheet("background: #2a2d36; min-height: 1px; max-height: 1px; margin-top: 8px;")
        layout.addWidget(separator2)

        # Controls
        controls_label = QLabel("Controls:")
        controls_label.setStyleSheet("color: #e8e9ea; font-weight: 500; margin-top: 8px;")
        layout.addWidget(controls_label)

        # FPS control
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("FPS:"))
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 120)
        self.fps_spinbox.setValue(60)  # Changed default from 30 to 60
        self.fps_spinbox.setEnabled(False)
        self.fps_spinbox.valueChanged.connect(self._on_fps_changed)
        fps_layout.addWidget(self.fps_spinbox)
        layout.addLayout(fps_layout)

        # Zoom control
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(50, 200)  # 0.5x to 2.0x zoom
        self.zoom_slider.setValue(100)  # 1.0x default
        self.zoom_slider.setEnabled(False)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        zoom_layout.addWidget(self.zoom_slider)
        self.zoom_label = QLabel("1.0x")
        zoom_layout.addWidget(self.zoom_label)
        self.zoom_value_label = self.zoom_label
        layout.addLayout(zoom_layout)

        # Resolution control
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("Resolution:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "640x480",
            "800x600",
            "1024x768",
            "1280x720",
            "1280x1024",
            "1920x1080",
            "2048x1536"
        ])
        self.resolution_combo.setEnabled(False)
        self.resolution_combo.currentTextChanged.connect(self._on_resolution_changed)
        self.resolution_combo.setMaxVisibleItems(10)  # Show up to 10 items in dropdown
        resolution_layout.addWidget(self.resolution_combo)
        layout.addLayout(resolution_layout)

        # No stretch - content should stay compact at top
        return box
    
    def _experiment_status_box(self):
        """Create experiment status/info panel"""
        from PyQt6.QtWidgets import QSizePolicy
        box = QGroupBox("Experiment Status")
        # Preferred vertical so it doesn't stretch excessively
        box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(10)

        # Status indicator
        status_layout = QHBoxLayout()
        self.experiment_status_indicator = QLabel("●")
        self.experiment_status_indicator.setStyleSheet("color: #a0a4ac; font-size: 14px;")
        self.experiment_status_text = QLabel("Not Running")
        self.experiment_status_text.setStyleSheet("color: #e8e9ea; font-weight: 600; font-size: 13px;")
        status_layout.addWidget(self.experiment_status_indicator)
        status_layout.addWidget(self.experiment_status_text)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Separator
        separator = QLabel("")
        separator.setStyleSheet("background: #2a2d36; min-height: 1px; max-height: 1px;")
        layout.addWidget(separator)

        # Active stimuli
        stimuli_label = QLabel("Active Stimuli:")
        stimuli_label.setStyleSheet("color: #a0a4ac; font-size: 12px; padding-top: 4px;")
        layout.addWidget(stimuli_label)
        
        self.active_stimuli_list = QLabel("None")
        self.active_stimuli_list.setStyleSheet("color: #e8e9ea; font-size: 11px; padding-left: 8px;")
        self.active_stimuli_list.setWordWrap(True)
        layout.addWidget(self.active_stimuli_list)

        # Recording status
        recording_layout = QHBoxLayout()
        recording_label = QLabel("Recording:")
        recording_label.setStyleSheet("color: #a0a4ac; font-size: 12px;")
        self.recording_status = QLabel("● Not Recording")
        self.recording_status.setStyleSheet("color: #dc2626; font-size: 11px;")
        recording_layout.addWidget(recording_label)
        recording_layout.addWidget(self.recording_status)
        recording_layout.addStretch()
        layout.addLayout(recording_layout)

        # No vertical stretch - content stays compact at top
        return box

    # ---------- ENVIRONMENT CONTROLS ----------
    def _environment_controls(self):
        box = QGroupBox("Environment Variables")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(14)

        # Add a quick info header
        info_header = QLabel("Control environmental conditions for consistent experiments")
        info_header.setStyleSheet("color: #a0a4ac; font-size: 11px; padding-bottom: 8px;")
        layout.addWidget(info_header)

        layout.addLayout(self._slider_row("IR Light"))
        layout.addLayout(self._slider_row("White Light"))
        layout.addLayout(self._slider_row("Pump"))

        # Separator before temperature
        separator = QLabel("")
        separator.setStyleSheet("background: #2a2d36; min-height: 1px; max-height: 1px; margin: 8px 0;")
        layout.addWidget(separator)

        # Temperature display with icon-like styling
        temp_container = QHBoxLayout()
        temp_container.setContentsMargins(0, 4, 0, 0)
        temp_icon = QLabel("🌡")
        temp_icon.setStyleSheet("font-size: 16px; padding-right: 4px;")
        temp = QLabel("Temperature:")
        temp.setStyleSheet("color: #e8e9ea; font-weight: 500;")
        temp_value = QLabel("-- °C")
        temp_value.setObjectName("Temperature")
        temp_container.addWidget(temp_icon)
        temp_container.addWidget(temp)
        temp_container.addWidget(temp_value)
        temp_container.addStretch()
        layout.addLayout(temp_container)
        
        # Store temperature label reference
        self.temp_label = temp_value

        return box

    # ---------- STIMULI ----------
    def _stimuli_controls(self):
        box = QGroupBox("Stimuli Control")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(14)

        # Add info header
        info_header = QLabel("Configure stimuli parameters for behavioral experiments")
        info_header.setStyleSheet("color: #9aa0aa; font-size: 11px; padding-bottom: 4px;")
        layout.addWidget(info_header)

        layout.addLayout(self._stimulus_row("Vibration"))
        layout.addLayout(self._stimulus_row("Buzzer"))
        layout.addLayout(self._stimulus_row("Heater"))
        layout.addLayout(self._rgb_row())

        return box

    # ---------- HELPERS ----------
    def _slider_row(self, name):
        row = QHBoxLayout()
        row.setSpacing(12)
        row.setContentsMargins(0, 0, 0, 0)

        label = QLabel(name)
        label.setMinimumWidth(80)
        enable = QCheckBox("Enable")
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(0)
        slider.setEnabled(False)  # Disabled until enable checkbox is checked

        # Store references based on name
        if name == "IR Light":
            self.ir_slider = slider
            self.ir_enable = enable
        elif name == "White Light":
            self.white_slider = slider
            self.white_enable = enable
        elif name == "Pump":
            self.pump_slider = slider
            self.pump_enable = enable

        # Connect enable checkbox to slider
        enable.toggled.connect(lambda checked, s=slider: s.setEnabled(checked))
        enable.toggled.connect(lambda checked, s=slider, n=name: self._on_enable_toggled(checked, s, n))
        
        # Connect slider to backend
        slider.valueChanged.connect(lambda val, n=name: self._on_slider_changed(val, n))

        row.addWidget(label)
        row.addWidget(enable)
        row.addWidget(slider, 1)

        return row

    def _stimulus_row(self, name):
        row = QHBoxLayout()
        row.setSpacing(10)
        row.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(name)
        name_label.setMinimumWidth(80)
        row.addWidget(name_label)
        
        enable_cb = QCheckBox("Enable")
        row.addWidget(enable_cb)

        intensity_label = QLabel("Intensity")
        intensity_label.setMinimumWidth(60)
        row.addWidget(intensity_label)
        
        intensity_slider = QSlider(Qt.Orientation.Horizontal)
        intensity_slider.setRange(0, 100)
        intensity_slider.setValue(0)
        intensity_slider.setEnabled(False)
        row.addWidget(intensity_slider, 1)

        duration_label = QLabel("Duration")
        duration_label.setMinimumWidth(60)
        row.addWidget(duration_label)
        
        duration_spin = QSpinBox()
        duration_spin.setRange(0, 9999)
        duration_spin.setSuffix(" ms")
        duration_spin.setValue(0)
        row.addWidget(duration_spin)

        delay_label = QLabel("Delay")
        delay_label.setMinimumWidth(50)
        row.addWidget(delay_label)
        
        delay_spin = QSpinBox()
        delay_spin.setRange(0, 9999)
        delay_spin.setSuffix(" ms")
        delay_spin.setValue(0)
        row.addWidget(delay_spin)

        continuous_cb = QCheckBox("Continuous")
        row.addWidget(continuous_cb)

        # Store references for each stimulus
        if name == "Vibration":
            self.vib_slider = intensity_slider
            self.vib_enable = enable_cb
            self.vib_duration = duration_spin
            self.vib_delay = delay_spin
            self.vib_continuous = continuous_cb
        elif name == "Buzzer":
            self.buzzer_slider = intensity_slider
            self.buzzer_enable = enable_cb
            self.buzzer_duration = duration_spin
            self.buzzer_delay = delay_spin
            self.buzzer_continuous = continuous_cb
        elif name == "Heater":
            self.heater_slider = intensity_slider
            self.heater_enable = enable_cb
            self.heater_duration = duration_spin
            self.heater_delay = delay_spin
            self.heater_continuous = continuous_cb

        # Connect enable checkbox
        enable_cb.toggled.connect(lambda checked, s=intensity_slider: s.setEnabled(checked))
        enable_cb.toggled.connect(lambda checked, s=intensity_slider, n=name: self._on_stimulus_enable_toggled(checked, s, n))
        
        # Connect slider
        intensity_slider.valueChanged.connect(lambda val, n=name: self._on_stimulus_slider_changed(val, n))

        # Connect continuous checkbox to disable/enable duration and delay
        def on_continuous_toggled(checked):
            duration_spin.setEnabled(not checked)
            delay_spin.setEnabled(not checked)
            duration_label.setEnabled(not checked)
            delay_label.setEnabled(not checked)
            if checked:
                duration_spin.setValue(0)
                delay_spin.setValue(0)
        
        continuous_cb.toggled.connect(on_continuous_toggled)
        
        return row

    def _rgb_row(self):
        row = QHBoxLayout()
        row.setSpacing(10)
        row.setContentsMargins(0, 0, 0, 0)

        rgb_label = QLabel("RGB Light")
        rgb_label.setMinimumWidth(80)
        row.addWidget(rgb_label)
        
        enable_cb = QCheckBox("Enable")
        row.addWidget(enable_cb)

        pick = QPushButton("Pick Color")
        pick.setMinimumWidth(100)
        pick.clicked.connect(lambda: QColorDialog.getColor())
        row.addWidget(pick)

        row.addStretch()
        return row

    def _placeholder_tab(self, name):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 8, 0, 0)
        label = QLabel(f"{name} — Coming soon")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #9aa0aa; font-size: 14px;")
        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()
        return page

    # ---------- BACKEND INTEGRATION ----------
    def _connect_backend(self):
        """Connect UI controls to backend Arduino controller"""
        if not self.arduino:
            self.logger.warning("Arduino controller not available")
            self._update_arduino_status(False, "Not initialized")
            return
        
        # Check if already connected (non-blocking check only)
        if self.arduino.is_connected():
            port = getattr(self.arduino, 'port', 'Unknown')
            self.logger.info("Arduino already connected")
            self._update_arduino_status(True, f"Connected ({port})")
        else:
            # Don't auto-connect on startup to avoid blocking UI
            # User can connect manually via Settings
            self.logger.info("Arduino not connected - use Settings to connect")
            self._update_arduino_status(False, "Not connected")
    
    def _show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.arduino, self, self.zebrazoom)
        dialog.exec()
        # Update status after settings dialog closes
        self._update_connection_status()
        # Update zebrazoom reference if it was changed
        if hasattr(dialog, 'zebrazoom') and dialog.zebrazoom:
            self.zebrazoom = dialog.zebrazoom
            # Update analysis tab if it exists
            self._update_zebrazoom_in_analysis()
    
    def _update_zebrazoom_in_analysis(self):
        """Update ZebraZoom reference in analysis tab"""
        # Update the analysis tab's zebrazoom reference
        if hasattr(self, 'analysis_tab'):
            self.analysis_tab.zebrazoom = self.zebrazoom
            # Remove warning if ZebraZoom is now available
            if self.zebrazoom and self.zebrazoom.is_available():
                # Remove warning label if exists
                layout = self.analysis_tab.layout()
                if layout:
                    for j in range(layout.count()):
                        item = layout.itemAt(j)
                        if item and item.widget():
                            widget_item = item.widget()
                            if isinstance(widget_item, QLabel) and "⚠️" in widget_item.text():
                                widget_item.deleteLater()
    
    def _update_connection_status(self):
        """Update connection status by testing actual connection"""
        if not self.arduino:
            self._update_arduino_status(False, "Not initialized")
            return
            
        # Test if actually connected
        try:
            if self.arduino.is_connected():
                port = getattr(self.arduino, 'port', 'Unknown')
                self._update_arduino_status(True, f"Connected ({port})")
            else:
                # Try to reconnect if we have a port
                port = getattr(self.arduino, 'port', None)
                if port:
                    try:
                        if self.arduino.connect(port):
                            self._update_arduino_status(True, f"Connected ({port})")
                        else:
                            self._update_arduino_status(False, "Not connected")
                    except:
                        self._update_arduino_status(False, "Not connected")
                else:
                    self._update_arduino_status(False, "Not connected")
        except Exception as e:
            self.logger.error(f"Error checking connection: {e}")
            self._update_arduino_status(False, "Error")
        self._refresh_workspace_alert_banner()
        self._sync_system_ready_badge()

    def _sync_system_ready_badge(self):
        if not getattr(self, "_run_ready_badge", None):
            return
        ok_hw = self.arduino and self.arduino.is_connected()
        cams = []
        if self.camera:
            try:
                cams = self.camera.list_cameras() or []
            except Exception:
                pass
        if ok_hw and cams:
            self._run_ready_badge.setText("SYSTEM READY")
            self._run_ready_badge.setStyleSheet(
                "color: #22c55e; font-weight: 700; font-size: 11px; "
                "padding: 4px 10px; background: rgba(34,197,94,0.12); "
                "border-radius: 8px; border: 1px solid rgba(34,197,94,0.35);"
            )
        else:
            self._run_ready_badge.setText("SYSTEM NOT READY")
            self._run_ready_badge.setStyleSheet("")

    def _update_arduino_status(self, connected, message):
        """Update Arduino connection status label"""
        if self.arduino_status_label:
            self.arduino_status_label.setText(f"Arduino: {message}")
            ok = "#059669" if connected else "#dc2626"
            self.arduino_status_label.setStyleSheet(
                f"color: {ok}; font-size: 11px; padding: 6px 12px; font-weight: 600;"
            )
        self._refresh_workspace_alert_banner()
        self._sync_system_ready_badge()

    def _map_to_pwm(self, value_0_100):
        """Map slider value (0-100) to PWM value (0-255)"""
        return int((value_0_100 / 100.0) * 255)

    def _on_enable_toggled(self, checked, slider, name):
        """Handle enable checkbox toggle for environment controls"""
        if not checked:
            # Disable slider and set value to 0
            slider.setValue(0)
            self._send_arduino_command(name, 0)
        else:
            # Send current slider value
            self._send_arduino_command(name, slider.value())

    def _on_slider_changed(self, value, name):
        """Handle slider value change for environment controls"""
        if not self.arduino or not self.arduino.is_connected():
            return
        
        # Check if enabled
        enable_cb = None
        if name == "IR Light":
            enable_cb = self.ir_enable
        elif name == "White Light":
            enable_cb = self.white_enable
        elif name == "Pump":
            enable_cb = self.pump_enable
        
        if enable_cb and enable_cb.isChecked():
            self._send_arduino_command(name, value)

    def _on_stimulus_enable_toggled(self, checked, slider, name):
        """Handle enable checkbox toggle for stimulus controls"""
        if not checked:
            slider.setValue(0)
            self._send_stimulus_command(name, 0)
        else:
            self._send_stimulus_command(name, slider.value())

    def _on_stimulus_slider_changed(self, value, name):
        """Handle slider value change for stimulus controls"""
        if not self.arduino or not self.arduino.is_connected():
            return
        
        enable_cb = None
        if name == "Vibration":
            enable_cb = self.vib_enable
        elif name == "Buzzer":
            enable_cb = self.buzzer_enable
        elif name == "Heater":
            enable_cb = self.heater_enable
        
        if enable_cb and enable_cb.isChecked():
            self._send_stimulus_command(name, value)

    def _send_arduino_command(self, name, value_0_100):
        """Send command to Arduino for environment controls"""
        if not self.arduino:
            self.logger.warning("Arduino controller not available")
            return
            
        if not self.arduino.is_connected():
            self.logger.warning("Arduino not connected - please connect via Settings")
            # Update status to show user needs to connect
            self._update_arduino_status(False, "Not connected - use Settings")
            return
        
        pwm_value = self._map_to_pwm(value_0_100)
        
        cmd_map = {
            "IR Light": f"IR {pwm_value}",
            "White Light": f"WHITE {pwm_value}",
            "Pump": f"PUMP {pwm_value}"
        }
        
        cmd = cmd_map.get(name)
        if cmd:
            try:
                reply = self.arduino.send(cmd)
                self.logger.info(f"Arduino command: {cmd} -> {reply}")
            except Exception as e:
                self.logger.error(f"Failed to send Arduino command {cmd}: {e}", exc_info=True)

    def _send_stimulus_command(self, name, value_0_100):
        """Send command to Arduino for stimulus controls"""
        if not self.arduino:
            self.logger.warning("Arduino controller not available")
            return
            
        if not self.arduino.is_connected():
            self.logger.warning("Arduino not connected")
            return
        
        pwm_value = self._map_to_pwm(value_0_100)
        
        # Map stimulus names to Arduino commands
        # Note: Buzzer and Heater may not be implemented in Arduino yet
        cmd_map = {
            "Vibration": f"VIB {pwm_value}",
            "Buzzer": None,  # Not implemented in Arduino firmware
            "Heater": None   # Not implemented in Arduino firmware
        }
        
        cmd = cmd_map.get(name)
        if cmd:
            try:
                reply = self.arduino.send(cmd)
                self.logger.info(f"Arduino command: {cmd} -> {reply}")
            except Exception as e:
                self.logger.error(f"Failed to send Arduino command {cmd}: {e}", exc_info=True)
        elif cmd is None:
            self.logger.warning(f"Stimulus '{name}' not implemented in Arduino firmware")

    def _update_temperature(self):
        """Update temperature display from Arduino"""
        if not self.arduino:
            if self.temp_label:
                self.temp_label.setText("-- °C")
            if self._footer_temp_label:
                self._footer_temp_label.setText("Temperature: —")
            return
            
        # Check connection more reliably
        is_connected = False
        try:
            if self.arduino.is_connected():
                # Try a quick test to see if actually working
                is_connected = True
        except:
            pass
            
        if not is_connected:
            if self.temp_label:
                self.temp_label.setText("-- °C")
            if self._footer_temp_label:
                self._footer_temp_label.setText("Temperature: —")
            return
        
        try:
            temp = self.arduino.read_temperature_c()
            if temp is not None:
                if self.temp_label:
                    self.temp_label.setText(f"{temp:.1f} °C")
                if self._footer_temp_label:
                    self._footer_temp_label.setText(f"Temperature: {temp:.1f} °C")
            else:
                if self.temp_label:
                    self.temp_label.setText("-- °C")
                if self._footer_temp_label:
                    self._footer_temp_label.setText("Temperature: —")
        except Exception as e:
            self.logger.error(f"Failed to read temperature: {e}")
            if self.temp_label:
                self.temp_label.setText("ERR °C")
            if self._footer_temp_label:
                self._footer_temp_label.setText("Temperature: ERR")

    def _on_start_experiment(self):
        """Handle start experiment button click"""
        if not self.runner:
            self.logger.warning("Experiment runner not available")
            return
        
        # Build experiment config from UI state
        # Collect active stimuli with their parameters
        stimuli_config = {}
        
        # Vibration
        if hasattr(self, 'vib_enable') and self.vib_enable and self.vib_enable.isChecked():
            intensity = self.vib_slider.value() if self.vib_slider else 0
            continuous = self.vib_continuous.isChecked() if self.vib_continuous else False
            stimuli_config["VIB"] = {
                "level": self._map_to_pwm(intensity),
                "continuous": continuous,
                "duration_ms": 0 if continuous else (self.vib_duration.value() if self.vib_duration else 0),
                "delay_ms": 0 if continuous else (self.vib_delay.value() if self.vib_delay else 0)
            }
        
        # Buzzer
        if hasattr(self, 'buzzer_enable') and self.buzzer_enable and self.buzzer_enable.isChecked():
            intensity = self.buzzer_slider.value() if self.buzzer_slider else 0
            continuous = self.buzzer_continuous.isChecked() if self.buzzer_continuous else False
            stimuli_config["BUZZER"] = {
                "level": self._map_to_pwm(intensity),
                "continuous": continuous,
                "duration_ms": 0 if continuous else (self.buzzer_duration.value() if self.buzzer_duration else 0),
                "delay_ms": 0 if continuous else (self.buzzer_delay.value() if self.buzzer_delay else 0)
            }
        
        # Heater
        if hasattr(self, 'heater_enable') and self.heater_enable and self.heater_enable.isChecked():
            intensity = self.heater_slider.value() if self.heater_slider else 0
            continuous = self.heater_continuous.isChecked() if self.heater_continuous else False
            stimuli_config["HEATER"] = {
                "level": self._map_to_pwm(intensity),
                "continuous": continuous,
                "duration_ms": 0 if continuous else (self.heater_duration.value() if self.heater_duration else 0),
                "delay_ms": 0 if continuous else (self.heater_delay.value() if self.heater_delay else 0)
            }
        
        # Calculate experiment duration (long enough for all stimuli)
        max_duration = 60  # Default 60 seconds
        if stimuli_config:
            # For now, use a reasonable default, could calculate from stimuli
            max_duration = 300  # 5 minutes default
        
        config = {
            "duration_s": max_duration,
            "stimuli": stimuli_config
        }
        
        try:
            if self.runner.start(config):
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                
                # Update status
                if hasattr(self, 'experiment_status_indicator'):
                    self.experiment_status_indicator.setStyleSheet("color: #4fc3f7; font-size: 14px;")
                    self.experiment_status_text.setText("Running")
                
                # Update active stimuli display
                if hasattr(self, 'active_stimuli_list'):
                    active_stimuli_names = list(stimuli_config.keys())
                    if active_stimuli_names:
                        self.active_stimuli_list.setText(", ".join(active_stimuli_names))
                    else:
                        self.active_stimuli_list.setText("None")
                
                # Start timer
                self.experiment_start_time = time.time()
                if not self.experiment_timer:
                    self.experiment_timer = QTimer()
                    self.experiment_timer.timeout.connect(self._update_experiment_timer)
                self.experiment_timer.start(1000)  # Update every second
                
                # Update recording status
                if hasattr(self, 'recording_status'):
                    self.recording_status.setText("● Recording")
                    self.recording_status.setStyleSheet("color: #4fc3f7; font-size: 11px;")
                
                self.logger.info("Experiment started")
            else:
                self.logger.warning("Failed to start experiment (already running?)")
        except Exception as e:
            self.logger.error(f"Error starting experiment: {e}")

    def _on_stop_experiment(self):
        """Handle stop experiment button click"""
        if not self.runner:
            return
        
        try:
            self.runner.stop()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
            # Update status
            if hasattr(self, 'experiment_status_indicator'):
                self.experiment_status_indicator.setStyleSheet("color: #9aa0aa; font-size: 14px;")
                self.experiment_status_text.setText("Not Running")
            
            # Stop timer
            if self.experiment_timer:
                self.experiment_timer.stop()
            if hasattr(self, 'experiment_timer_label'):
                self.experiment_timer_label.setText("Duration: 00:00")
            self.experiment_start_time = None
            
            # Update recording status
            if hasattr(self, 'recording_status'):
                self.recording_status.setText("● Not Recording")
                self.recording_status.setStyleSheet("color: #d04f4f; font-size: 11px;")
            
            # Clear active stimuli
            if hasattr(self, 'active_stimuli_list'):
                self.active_stimuli_list.setText("None")
            
            self.logger.info("Experiment stopped")
        except Exception as e:
            self.logger.error(f"Error stopping experiment: {e}")
    
    def _update_experiment_timer(self):
        """Update experiment timer display"""
        if self.experiment_start_time and hasattr(self, 'experiment_timer_label'):
            elapsed = time.time() - self.experiment_start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.experiment_timer_label.setText(f"Duration: {minutes:02d}:{seconds:02d}")
    
    # ---------- CAMERA METHODS ----------
    def _init_camera_list(self):
        """Initialize camera list in combo box"""
        self.logger.info("_init_camera_list called")
        self.logger.info(f"camera_combos list has {len(self.camera_combos)} items")
        
        if not self.camera:
            self.logger.warning("Camera controller not available")
            for combo in self.camera_combos:
                if combo:
                    combo.clear()
                    combo.addItem("Camera controller not available")
            return
        
        # Use camera_combos list instead of single camera_combo reference
        if not self.camera_combos:
            self.logger.warning("No camera combo boxes found")
            return
        
        cameras = self.camera.list_cameras()
        self.logger.info(f"Cameras found: {cameras}")
        
        # Update ALL camera combo boxes
        for combo in self.camera_combos:
            if combo:
                combo.blockSignals(True)
                combo.clear()
                if cameras:
                    combo.addItems(cameras)
                else:
                    combo.addItem("No cameras found")
                combo.blockSignals(False)
        
        if cameras:
            self.logger.info(f"Added {len(cameras)} cameras to {len(self.camera_combos)} combo boxes")
            
            # Set main reference if not set
            if not self.camera_combo and self.camera_combos:
                self.camera_combo = self.camera_combos[0]
            
            # Auto-select first camera
            for combo in self.camera_combos:
                if combo:
                    combo.setCurrentIndex(0)
            
            self._on_camera_selected(cameras[0])
        else:
            self.logger.warning("No cameras detected. Make sure your webcam is connected and not in use by another application.")
    
    def _refresh_camera_list(self):
        """Refresh camera list"""
        if not self.camera or not self.camera_combo:
            return
        
        self.logger.info("Refreshing camera list...")
        
        # Stop current preview
        if self.current_camera:
            self.camera.stop_preview(self.current_camera)
            self.current_camera = None
        
        # Refresh camera detection
        self.camera.refresh_cameras()
        
        # Update all combo boxes
        cameras = self.camera.list_cameras()
        for combo in self.camera_combos:
            if combo:
                combo.blockSignals(True)
                combo.clear()
                if cameras:
                    combo.addItems(cameras)
                else:
                    combo.addItem("No cameras found")
                combo.blockSignals(False)
        
        if cameras:
            self.logger.info(f"Found {len(cameras)} cameras: {cameras}")
            # Auto-select first camera
            if self.camera_combo:
                self.camera_combo.setCurrentIndex(0)
                self._on_camera_selected(cameras[0])
        else:
            self.logger.warning("No cameras found after refresh")

        self._refresh_workspace_alert_banner()
        self._sync_system_ready_badge()

    def _sync_all_camera_combos(self):
        """Sync all camera combo boxes with main combo"""
        if not self.camera_combo:
            return
        
        cameras = [self.camera_combo.itemText(i) for i in range(self.camera_combo.count())]
        current_text = self.camera_combo.currentText()
        
        for combo in self.camera_combos:
            if combo and combo != self.camera_combo:
                combo.blockSignals(True)
                combo.clear()
                combo.addItems(cameras)
                index = combo.findText(current_text)
                if index >= 0:
                    combo.setCurrentIndex(index)
                combo.blockSignals(False)
    
    def _on_camera_selected(self, camera_name: str):
        """Handle camera selection"""
        if not self.camera or not camera_name or camera_name == "No cameras found" or camera_name == "Camera controller not available":
            return

        # Stop previous preview cleanly
        if self.current_camera and self.current_camera != camera_name:
            self.camera.stop_preview(self.current_camera)
            time.sleep(0.2)

        self.current_camera = camera_name
        resolutions = []
        # Dynamically check resolutions for webcam
        cam_info = self.camera.cameras.get(camera_name)
        if cam_info and cam_info["type"] == CameraType.WEBCAM:
            resolutions = self.camera.get_supported_resolutions(camera_name)
            resolutions = [f"{w}x{h}" for (w, h) in resolutions]
        elif cam_info and cam_info["type"] == CameraType.BASLER:
            # Just use the known safe presets for basler
            resolutions = [
                "640x480", "800x600", "1024x768", "1280x720", "1280x960",
                "1280x1024", "1600x1200", "1920x1080", "2048x1536"
            ]

        # Update the combo box
        if hasattr(self, 'resolution_combo'):
            self.resolution_combo.blockSignals(True)
            self.resolution_combo.clear()
            if resolutions:
                for r in resolutions:
                    self.resolution_combo.addItem(r)
                # Default to 1280x1024 for Basler, highest for webcam
                if cam_info and cam_info["type"] == CameraType.BASLER:
                    default_index = resolutions.index("1280x1024") if "1280x1024" in resolutions else 0
                else:
                    default_index = 0  # Highest resolution for webcam
                self.resolution_combo.setCurrentIndex(default_index)
            else:
                self.resolution_combo.addItem("1280x1024")
                self.resolution_combo.setCurrentIndex(0)
            self.resolution_combo.setEnabled(True)
            self.resolution_combo.blockSignals(False)

        # Set and store this resolution as current before preview
        if hasattr(self, 'resolution_combo') and self.resolution_combo.count() > 0:
            default_res = self.resolution_combo.currentText()
            if default_res:
                parts = default_res.split('x')
                if len(parts) == 2:
                    w, h = int(parts[0]), int(parts[1])
                    self.camera.set_setting(camera_name, "resolution", (w, h))

        # Start preview
        # Disable UI controls during start
        if hasattr(self, 'resolution_combo'):
            self.resolution_combo.setEnabled(False)
        if hasattr(self, 'fps_spinbox'):
            self.fps_spinbox.setEnabled(False)
        if hasattr(self, 'zoom_slider'):
            self.zoom_slider.setEnabled(False)
        
        # Start preview first, then disable controller controls
        if self.camera.start_preview(camera_name, self._update_camera_frame):
            self.logger.info(f"Started preview for {camera_name}")
            # Enable controls after successful start
            self.fps_spinbox.setEnabled(True)
            self.zoom_slider.setEnabled(True)
            self.resolution_combo.setEnabled(True)

            # Load current settings
            if self.camera:
                fps = self.camera.get_setting(camera_name, "fps") or 60  # Changed fallback from 30 to 60
                zoom = self.camera.get_setting(camera_name, "zoom") or 1.0
                self.fps_spinbox.setValue(int(fps))
                self.zoom_slider.setValue(int(zoom * 100))
        else:
            self.logger.error(f"Failed to start preview for {camera_name}")
            # Re-enable controls on failure
            if hasattr(self, 'resolution_combo'):
                self.resolution_combo.setEnabled(True)
            if hasattr(self, 'fps_spinbox'):
                self.fps_spinbox.setEnabled(True)
            if hasattr(self, 'zoom_slider'):
                self.zoom_slider.setEnabled(True)

    
    def _update_camera_frame(self, frame: np.ndarray):
        """Update camera preview with new frame - optimized for performance"""
        if not self.camera_preview_labels:
            return
        
        try:
            # Limit UI updates to ~30 FPS for smooth performance
            current_time = time.time()
            if not hasattr(self, '_last_ui_update'):
                self._last_ui_update = 0
            
            if current_time - self._last_ui_update < 0.033:  # ~30 FPS UI update
                return
            self._last_ui_update = current_time
            
            # Simple FPS counter
            self.fps_frame_times.append(current_time)
            self.fps_frame_times = [t for t in self.fps_frame_times[-30:] if current_time - t < 1.0]
            
            if len(self.fps_frame_times) > 1:
                time_span = self.fps_frame_times[-1] - self.fps_frame_times[0]
                self.current_fps = len(self.fps_frame_times) / time_span if time_span > 0 else 0
            
            # Update FPS label
            if self.fps_counter_label:
                self.fps_counter_label.setText(f"FPS: {self.current_fps:.1f}")
            
            # Convert frame to RGB - handle different camera formats
            try:
                if frame is None:
                    return
                    
                # Handle different frame formats from different cameras
                if len(frame.shape) == 2:
                    # Grayscale frame - convert to RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
                elif len(frame.shape) == 3:
                    if frame.shape[2] == 3:
                        # BGR frame - convert to RGB
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    elif frame.shape[2] == 4:
                        # BGRA frame - convert to RGB
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                    else:
                        # Unknown format, use as-is
                        rgb_frame = frame
                else:
                    # Unknown format, use as-is
                    rgb_frame = frame
                    
            except Exception as e:
                self.logger.error(f"Error converting frame format: {e}, frame shape: {frame.shape if frame is not None else 'None'}")
                return
            
            # Get first visible preview label
            preview_label = None
            for label in self.camera_preview_labels:
                if label and label.isVisible():
                    preview_label = label
                    break
            
            if preview_label is None:
                return
            
            # Cache label dimensions to avoid repeated calls
            if not hasattr(self, '_cached_label_size') or self._cached_label_size != (preview_label.width(), preview_label.height()):
                self._cached_label_size = (preview_label.width(), preview_label.height())
                self._cached_scaled_size = (
                    max(preview_label.width(), 320),
                    max(preview_label.height(), 240)
                )
            
            # Create QImage directly from numpy array - robust error handling
            try:
                h, w = rgb_frame.shape[:2]
                
                # Determine bytes per line based on frame format
                if len(rgb_frame.shape) == 3:
                    bytes_per_line = w * rgb_frame.shape[2]
                else:
                    bytes_per_line = w * 3  # Default to 3 channels
                
                # Use ascontiguousarray to ensure memory layout
                rgb_frame_contiguous = np.ascontiguousarray(rgb_frame)
                
                # Create QImage with error checking
                if len(rgb_frame_contiguous.shape) == 3 and rgb_frame_contiguous.shape[2] == 3:
                    qt_image = QImage(rgb_frame_contiguous.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                elif len(rgb_frame_contiguous.shape) == 2:
                    # Grayscale
                    qt_image = QImage(rgb_frame_contiguous.data, w, h, bytes_per_line, QImage.Format.Format_Grayscale8)
                else:
                    # Fallback format
                    qt_image = QImage(rgb_frame_contiguous.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                
                if qt_image.isNull():
                    self.logger.warning(f"Failed to create QImage from frame shape: {rgb_frame_contiguous.shape}")
                    return
                
                # Scale pixmap once using cached size and zoom
                # Get current zoom setting
                zoom = self.camera.get_setting(self.current_camera, "zoom") if self.camera and self.current_camera else 1.0
                zoom = zoom if zoom is not None else 1.0
                
                # Apply zoom to scaling
                scaled_width = int(self._cached_scaled_size[0] * zoom)
                scaled_height = int(self._cached_scaled_size[1] * zoom)
                
                scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                    scaled_width,
                    scaled_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.FastTransformation
                )
                
                # Update label
                preview_label.setPixmap(scaled_pixmap)
                
            except Exception as e:
                self.logger.error(f"Error creating QImage from frame: {e}, frame shape: {rgb_frame.shape if rgb_frame is not None else 'None'}")
                return
            
        except Exception as e:
            self.logger.error(f"Error updating camera frame: {e}")
    
    def _on_fps_changed(self, value: int):
        """Handle FPS change - uses CameraController safety"""
        if not self.current_camera or not self.camera:
            return
        
        # Check if controls are disabled at controller level
        if self.camera.are_ui_controls_disabled():
            return
        
        # Disable control during operation
        self.fps_spinbox.setEnabled(False)
        
        # Set setting through controller (will check safety)
        if self.camera.set_setting(self.current_camera, "fps", value):
            self.logger.info(f"FPS changed to {value}")
        
        # Re-enable control after a short delay
        QTimer.singleShot(200, lambda: self.fps_spinbox.setEnabled(True))
    
    def _on_zoom_changed(self, value: int):
        """Handle zoom change - uses CameraController safety"""
        zoom_value = value / 100.0
        if hasattr(self, "zoom_value_label") and self.zoom_value_label:
            self.zoom_value_label.setText(f"{zoom_value:.1f}x")
        
        if not self.current_camera or not self.camera:
            return
        
        # Check if controls are disabled at controller level
        if self.camera.are_ui_controls_disabled():
            return
        
        # Disable control during operation
        self.zoom_slider.setEnabled(False)
        
        # Set setting through controller (will check safety)
        if self.camera.set_setting(self.current_camera, "zoom", zoom_value):
            self.logger.info(f"Zoom changed to {zoom_value}")
        self.zoom_slider.setEnabled(True)

    def _on_resolution_changed(self, resolution_str: str):
        """Handle resolution change - now supports Basler cameras"""
        if not self.current_camera or not self.camera:
            return
        
        # Check if controls are disabled at controller level
        if self.camera.are_ui_controls_disabled():
            return
        
        # Check camera type
        camera_name = self.current_camera
        cam_info = self.camera.cameras.get(camera_name)
        
        # For Basler cameras, log that we're attempting resolution change
        if cam_info and cam_info.get("type") == CameraType.BASLER:
            self.logger.info(f"Attempting Basler resolution change to {resolution_str}")
        elif cam_info and cam_info.get("type") == CameraType.WEBCAM:
            self.logger.info(f"Setting webcam resolution to {resolution_str}")
        
        # Disable control during operation to prevent rapid changes
        self.resolution_combo.setEnabled(False)
        
        try:
            # Parse resolution string (e.g., "1920x1080")
            parts = resolution_str.split("x")
            if len(parts) != 2:
                return
                
            width = int(parts[0])
            height = int(parts[1])
            
            # Set setting through controller (will check safety and Basler protection)
            if self.camera.set_setting(camera_name, "resolution", (width, height)):
                self.logger.info(f"Resolution changed to {width}x{height}")
                
                # Stop current preview
                self.camera.stop_preview(camera_name)
                
                # Restart preview with new resolution after short delay
                QTimer.singleShot(100, lambda: self._restart_preview_with_new_resolution(camera_name))
            else:
                self.logger.warning("Resolution change rejected by CameraController")
            
        except Exception as e:
            self.logger.error(f"Error changing resolution: {e}")
        finally:
            # Re-enable control after operation
            QTimer.singleShot(500, lambda: self.resolution_combo.setEnabled(True))

