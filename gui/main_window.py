from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QGroupBox, QPushButton,
    QCheckBox, QSlider, QSpinBox, QColorDialog, QComboBox, QMessageBox,
    QStackedWidget, QFrame, QScrollArea, QListWidget, QListWidgetItem,
    QGridLayout,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QDateTime
from PyQt6.QtGui import QIcon, QImage, QPixmap
import logging
import time
import cv2
import numpy as np
from gui.settings_dialog import SettingsDialog
from gui.analysis_tab import AnalysisTab
from gui.presets_tab import PresetsTab
from backend.camera_interface import CameraType


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

        self.setWindowTitle("ZIMON — Behaviour Tracking System")
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
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        mid_wrap = QWidget()
        mid_outer = QVBoxLayout(mid_wrap)
        mid_outer.setContentsMargins(0, 0, 0, 0)
        mid_outer.setSpacing(0)

        mid_cols = QHBoxLayout()
        mid_cols.setContentsMargins(8, 0, 8, 0)
        mid_cols.setSpacing(10)
        mid_cols.addWidget(self._build_left_assay_panel(), 0)

        main_area = QWidget()
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(8, 12, 8, 0)
        main_layout.setSpacing(10)
        main_layout.addLayout(self._build_header())

        self.pages = QStackedWidget()
        self.pages.addWidget(self._environment_tab())
        self.pages.addWidget(self._experiment_tab())
        uid = self.user_data.get("id")
        self.presets_tab = PresetsTab(self, user_id=uid if uid is not None else None)
        self.pages.addWidget(self.presets_tab)
        self.analysis_tab = AnalysisTab(self.zebrazoom)
        self.pages.addWidget(self.analysis_tab)
        self.pages.addWidget(self._build_account_tab())

        main_layout.addWidget(self.pages, 1)
        mid_cols.addWidget(main_area, 1)
        mid_cols.addWidget(self._build_right_dashboard_panel(), 0)
        mid_outer.addLayout(mid_cols, 1)
        mid_outer.addWidget(self._build_dashboard_status_bar())
        root.addWidget(mid_wrap, 1)

        self.setCentralWidget(central)

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

    # ---------- SIDEBAR ----------
    # Wider rail: icon + label per row (readable “proper” navbar)
    _SIDEBAR_WIDTH = 168
    _SIDEBAR_NAV_BTN = 48

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(self._SIDEBAR_WIDTH)
        sidebar.setMinimumWidth(self._SIDEBAR_WIDTH)
        sidebar.setMaximumWidth(self._SIDEBAR_WIDTH)
        sidebar.setStyleSheet("""
            QFrame#Sidebar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1d23, stop:1 #0d0f13);
                border-right: 2px solid #2a2d36;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 20, 14, 20)
        layout.setSpacing(10)
        
        # Logo section at top
        logo_container = QFrame()
        logo_container.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
            }
        """)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(8)
        
        # Modern logo with better icon
        logo = QLabel("🧬")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("""
            QLabel {
                font-size: 36px;
                padding: 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #6366f1, stop:1 #8b5cf6);
                border-radius: 20px;
                color: white;
                font-weight: bold;
            }
        """)
        logo_layout.addWidget(logo)
        
        # App name with better styling
        app_name = QLabel("ZIMON")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_name.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 15px;
                font-weight: 700;
                padding: 10px 8px;
                background: rgba(99, 102, 241, 0.15);
                border-radius: 8px;
                border: 1px solid rgba(99, 102, 241, 0.3);
                letter-spacing: 3px;
            }
        """)
        logo_layout.addWidget(app_name)
        
        layout.addWidget(logo_container)
        
        # Separator with better styling
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent, stop:0.5 #2a2d36, stop:1 transparent);
                max-height: 2px;
                border: none;
            }
        """)
        layout.addWidget(sep)
        
        layout.addSpacing(12)
        
        nav_btn_style = """
                QPushButton {
                    background: rgba(255, 255, 255, 0.05);
                    border: 2px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    font-size: 22px;
                    color: #b8bcc8;
                    font-family: "Segoe UI Emoji", "Apple Color Emoji", sans-serif;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: rgba(99, 102, 241, 0.15);
                    border: 2px solid rgba(99, 102, 241, 0.4);
                    color: #ffffff;
                }
                QPushButton:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #6366f1, stop:1 #8b5cf6);
                    border: 2px solid #6366f1;
                    color: #ffffff;
                    font-weight: bold;
                }
                QPushButton:pressed {
                    background: rgba(79, 70, 229, 0.8);
                    border: 2px solid #4f46e5;
                }
            """
        nav_label_style = """
                QLabel {
                    color: #c4c8d0;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 0px;
                }
            """

        self.nav_buttons = []
        nav_items = [
            ("🏠", "Home", "Environment", 0),
            ("🧪", "Lab", "Experiment", 1),
            ("💾", "Presets", "Presets", 2),
            ("📊", "Data", "Analysis", 3),
        ]
        
        for icon, short_name, tooltip, page_idx in nav_items:
            row = QFrame()
            row.setStyleSheet("QFrame { background: transparent; border: none; }")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(10)
            
            btn = QPushButton(icon)
            btn.setToolTip(tooltip)
            btn.setFixedSize(self._SIDEBAR_NAV_BTN, self._SIDEBAR_NAV_BTN)
            btn.setCheckable(True)
            btn.setStyleSheet(nav_btn_style)
            btn.clicked.connect(lambda checked, idx=page_idx: self._switch_page(idx))
            row_layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignVCenter)
            
            label = QLabel(short_name)
            label.setToolTip(tooltip)
            label.setStyleSheet(nav_label_style)
            label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            row_layout.addWidget(label, 1, Qt.AlignmentFlag.AlignVCenter)
            
            layout.addWidget(row)
            self.nav_buttons.append(btn)
        
        # Select first button by default
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)
        
        layout.addStretch()
        
        # Bottom section with settings
        bottom_container = QFrame()
        bottom_container.setStyleSheet("QFrame { background: transparent; border: none; }")
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)
        
        secondary_btn_style = """
            QPushButton {
                background: rgba(148, 163, 184, 0.1);
                border: 2px solid rgba(148, 163, 184, 0.2);
                border-radius: 12px;
                font-size: 20px;
                color: #94a3b8;
                font-family: "Segoe UI Emoji", "Apple Color Emoji", sans-serif;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(99, 102, 241, 0.15);
                border: 2px solid rgba(99, 102, 241, 0.4);
                color: #ffffff;
            }
            QPushButton:pressed {
                background: rgba(79, 70, 229, 0.3);
                border: 2px solid #4f46e5;
            }
        """
        account_btn_style = secondary_btn_style + """
            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                border: 2px solid #6366f1;
                color: #ffffff;
            }
        """
        bottom_label_style = nav_label_style

        # Settings — same row layout as main nav
        settings_row = QFrame()
        settings_row.setStyleSheet("QFrame { background: transparent; border: none; }")
        sr = QHBoxLayout(settings_row)
        sr.setContentsMargins(0, 2, 0, 2)
        sr.setSpacing(10)
        settings_btn = QPushButton("⚙️")
        settings_btn.setToolTip("Settings")
        settings_btn.setFixedSize(self._SIDEBAR_NAV_BTN, self._SIDEBAR_NAV_BTN)
        settings_btn.setStyleSheet(secondary_btn_style)
        settings_btn.clicked.connect(self._show_settings)
        sr.addWidget(settings_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        settings_label = QLabel("Settings")
        settings_label.setToolTip("Settings")
        settings_label.setStyleSheet(bottom_label_style)
        settings_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        sr.addWidget(settings_label, 1, Qt.AlignmentFlag.AlignVCenter)
        bottom_layout.addWidget(settings_row)
        
        # Account (page index 4) — below Settings
        account_row = QFrame()
        account_row.setStyleSheet("QFrame { background: transparent; border: none; }")
        ar = QHBoxLayout(account_row)
        ar.setContentsMargins(0, 2, 0, 2)
        ar.setSpacing(10)
        account_btn = QPushButton("👤")
        account_btn.setToolTip("Account")
        account_btn.setFixedSize(self._SIDEBAR_NAV_BTN, self._SIDEBAR_NAV_BTN)
        account_btn.setCheckable(True)
        account_btn.setStyleSheet(account_btn_style)
        account_btn.clicked.connect(self._switch_to_account_page)
        ar.addWidget(account_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        self.account_sidebar_btn = account_btn
        account_label = QLabel("Account")
        account_label.setToolTip("Account")
        account_label.setStyleSheet(bottom_label_style)
        account_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        ar.addWidget(account_label, 1, Qt.AlignmentFlag.AlignVCenter)
        bottom_layout.addWidget(account_row)
        
        layout.addWidget(bottom_container)
        
        return sidebar
    
    def _switch_page(self, index):
        """Switch to a page and update nav button states"""
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        if getattr(self, "account_sidebar_btn", None):
            self.account_sidebar_btn.setChecked(False)
        
        # Update page title
        titles = ["Environment", "Experiment", "Presets", "Analysis"]
        if hasattr(self, 'page_title') and index < len(titles):
            self.page_title.setText(titles[index])
    
    def _switch_to_account_page(self):
        """Open Account page (stack index 4); exclusive with main nav."""
        self.pages.setCurrentIndex(4)
        for btn in self.nav_buttons:
            btn.setChecked(False)
        if getattr(self, "account_sidebar_btn", None):
            self.account_sidebar_btn.setChecked(True)
        if hasattr(self, "page_title"):
            self.page_title.setText("Account")
    
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
        outer.setContentsMargins(0, 8, 0, 0)
        outer.setSpacing(16)

        intro = QLabel("Account")
        intro.setStyleSheet(
            "font-size: 18px; font-weight: 600; color: #e8e9ea; padding: 4px 0px 0px 0px;"
        )
        outer.addWidget(intro)

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

    def _logout(self):
        """Overridden in ui.main_window for real logout."""
        pass

    # ---------- HEADER ----------
    def _build_header(self):
        layout = QHBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 8)

        self.page_title = QLabel("Environment")
        self.page_title.setObjectName("PageTitle")
        layout.addWidget(self.page_title)

        layout.addStretch()

        theme_btn = QPushButton("Theme")
        theme_btn.setObjectName("ThemeToggleBtn")
        theme_btn.setToolTip("Toggle light / dark theme")
        theme_btn.clicked.connect(self._on_toggle_theme)
        layout.addWidget(theme_btn)

        status_label = QLabel("🔌 Arduino: Checking...")
        status_label.setObjectName("ArduinoStatus")
        self.arduino_status_label = status_label
        layout.addWidget(status_label)

        return layout

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

    # ---------- EXPERIMENT TAB ----------
    def _experiment_tab(self):
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

        # Top section: Camera and experiment status side by side
        top_section = QHBoxLayout()
        top_section.setSpacing(14)
        
        # Create camera preview widget (shares preview label reference)
        camera_preview = self._camera_preview_box()
        experiment_status = self._experiment_status_box()
        
        # Set maximum height for camera preview
        camera_preview.setMaximumHeight(400)
        
        top_section.addWidget(camera_preview, 3)
        top_section.addWidget(experiment_status, 2)

        layout.addLayout(top_section)
        layout.addWidget(self._stimuli_controls())

        # Action buttons with experiment info
        actions_container = QGroupBox("Experiment Control")
        actions_layout = QVBoxLayout(actions_container)
        actions_layout.setContentsMargins(16, 20, 16, 16)
        actions_layout.setSpacing(12)

        # Experiment timer/info
        timer_layout = QHBoxLayout()
        timer_layout.setSpacing(10)
        self.experiment_timer_label = QLabel("Duration: 00:00")
        self.experiment_timer_label.setStyleSheet("color: #a0a4ac; font-size: 13px;")
        timer_layout.addWidget(self.experiment_timer_label)
        timer_layout.addStretch()
        actions_layout.addLayout(timer_layout)

        # Buttons
        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addStretch()
        start_btn = QPushButton("▶ Start Experiment")
        start_btn.setMinimumWidth(160)
        start_btn.clicked.connect(self._on_start_experiment)
        actions.addWidget(start_btn)
        stop = QPushButton("⏹ Stop")
        stop.setObjectName("Danger")
        stop.setMinimumWidth(100)
        stop.clicked.connect(self._on_stop_experiment)
        stop.setEnabled(False)
        actions.addWidget(stop)
        
        # Store button references
        self.start_btn = start_btn
        self.stop_btn = stop

        actions_layout.addLayout(actions)
        layout.addWidget(actions_container)

        scroll.setWidget(page)
        return scroll

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
    
    def _update_arduino_status(self, connected, message):
        """Update Arduino connection status label"""
        if self.arduino_status_label:
            self.arduino_status_label.setText(f"Arduino: {message}")
            ok = "#059669" if connected else "#dc2626"
            self.arduino_status_label.setStyleSheet(
                f"color: {ok}; font-size: 11px; padding: 6px 12px; font-weight: 600;"
            )

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
        if hasattr(self, 'zoom_value_label') and self.zoom_value_label:
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


def _update_camera_frame(self, frame: np.ndarray):
    """Update camera preview with new frame - optimized for performance"""
    if not self.camera_preview_labels:
        return
    
    try:
        # Process all frames for accurate FPS counting
        current_time = time.time()
        
        # Simple FPS counter
        self.fps_frame_times.append(current_time)
        self.fps_frame_times = [t for t in self.fps_frame_times[-60:] if current_time - t < 1.0]
        
        if len(self.fps_frame_times) > 1:
            time_span = self.fps_frame_times[-1] - self.fps_frame_times[0]
            self.current_fps = len(self.fps_frame_times) / time_span if time_span > 0 else 0
        
        # Update FPS label
        if self.fps_counter_label:
            self.fps_counter_label.setText(f"FPS: {self.current_fps:.1f}")
        
        # Convert frame to RGB - handle different camera formats (optimized for speed)
        try:
            if frame is None:
                return
                
            # Handle different frame formats from different cameras
            if len(frame.shape) == 2:
                # Grayscale frame - convert to RGB (faster for Basler Mono8)
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
        
        # Create QImage directly from numpy array - optimized for high FPS
        try:
            h, w = rgb_frame.shape[:2]
            
            # Determine bytes per line based on frame format
            if len(rgb_frame.shape) == 3:
                bytes_per_line = w * rgb_frame.shape[2]
            else:
                bytes_per_line = w * 3  # Default to 3 channels
            
            # Use ascontiguousarray to ensure memory layout (faster for high FPS)
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
            
            # Use FastTransformation for high FPS
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
    
    def _restart_preview_with_new_resolution(self, camera_name: str):
        """Restart camera preview with new resolution - non-blocking"""
        try:
            if self.camera.start_preview(camera_name, self._update_camera_frame):
                self.logger.info(f"Restarted preview for {camera_name} with new resolution")
            else:
                self.logger.error(f"Failed to restart preview for {camera_name}")
        except Exception as e:
            self.logger.error(f"Error restarting preview: {e}")
    
    def _update_resolution_display(self):
        """Update resolution display after change"""
        if self.current_camera and self.camera:
            resolution = self.camera.get_resolution(self.current_camera)
            if resolution and self.camera_resolution_label:
                w, h = resolution
                self.camera_resolution_label.setText(f"Resolution: {w}x{h}")
                # Update combo box to show actual resolution
                if hasattr(self, 'resolution_combo'):
                    resolution_str = f"{w}x{h}"
                    self.resolution_combo.blockSignals(True)
                    index = self.resolution_combo.findText(resolution_str)
                    if index >= 0:
                        self.resolution_combo.setCurrentIndex(index)
                    else:
                        # Add if not in list
                        self.resolution_combo.addItem(resolution_str)
                        self.resolution_combo.setCurrentText(resolution_str)
                    self.resolution_combo.blockSignals(False)


# End of MainWindow class
            
