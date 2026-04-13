"""Larval dashboard - premium dark neon ZIMON layout."""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt, QDateTime, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from services.hardware_service import DeviceStatus, HardwareService
from services.protocol_service import ProtocolService
from services.recorder_service import RecorderService


class NeonCard(QFrame):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("LarvalCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)
        ttl = QLabel(title)
        ttl.setObjectName("LarvalCardTitle")
        lay.addWidget(ttl)
        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(10)
        lay.addLayout(self.body)


class WellPlatePreview(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows = 3
        self._cols = 4
        self.setObjectName("WellPlatePreview")
        self.setMinimumHeight(260)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())

    def set_plate(self, wells: int) -> None:
        mapping = {
            12: (3, 4),
            24: (4, 6),
            48: (6, 8),
            96: (8, 12),
        }
        self._rows, self._cols = mapping.get(wells, (3, 4))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(14, 14, -14, -14)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#0B1728"))
        p.drawRoundedRect(rect, 10, 10)

        cols = self._cols
        rows = self._rows
        if cols <= 0 or rows <= 0:
            return

        # Keep circles non-overlapping for all plate sizes while centered.
        spacing = 6.0
        fit_w = (rect.width() - spacing * (cols + 1)) / cols
        fit_h = (rect.height() - spacing * (rows + 1)) / rows
        d = max(2.0, min(fit_w, fit_h))

        total_w = cols * d + (cols - 1) * spacing
        total_h = rows * d + (rows - 1) * spacing
        ox = rect.x() + (rect.width() - total_w) / 2.0
        oy = rect.y() + (rect.height() - total_h) / 2.0

        pen = QPen(QColor("#00C8FF"))
        pen.setWidthF(1.2)
        p.setPen(pen)
        p.setBrush(QBrush(QColor("#102033")))

        for r in range(rows):
            for c in range(cols):
                x = ox + c * (d + spacing)
                y = oy + r * (d + spacing)
                p.drawEllipse(QRectF(x, y, d, d))

        p.end()


class AssaySidebar(NeonCard):
    def __init__(self, parent=None) -> None:
        super().__init__("TOP RECORDING ASSAYS", parent)
        self._cards: list[QPushButton] = []
        assays = [
            ("Multi-Well Plate", "Assess decision making and spatial preference."),
            ("Larval Reservoir Maze", "Track navigation and memory in structured paths."),
            ("Alternating T Maze", "Measure turning bias and exploration."),
            ("Open Field Arena", "General locomotion and anxiety-like movement."),
            ("L/D Choice Assay", "Light vs dark preference and phototaxis."),
        ]
        for i, (title, sub) in enumerate(assays):
            b = QPushButton(f"{title}\n{sub}")
            b.setObjectName("LarvalAssayItem")
            b.setCheckable(True)
            b.setMinimumHeight(66)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            self.body.addWidget(b)
            self._cards.append(b)
            if i == 0:
                b.setChecked(True)
            b.clicked.connect(lambda checked=False, src=b: self._set_active(src))
        self.btn_all = QPushButton("View all assays")
        self.btn_all.setObjectName("LarvalSecondaryBtn")
        self.body.addWidget(self.btn_all)
        self.body.addStretch(1)

    def _set_active(self, src: QPushButton) -> None:
        for c in self._cards:
            c.setChecked(c is src)


class WellPlateSelector(NeonCard):
    plate_changed = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__("SELECT WELL PLATE", parent)
        grid = QGridLayout()
        grid.setSpacing(8)
        self._buttons: dict[int, QPushButton] = {}
        values = (12, 24, 48, 96)
        for i, wells in enumerate(values):
            b = QPushButton(str(wells))
            b.setObjectName("LarvalPlateBtn")
            b.setCheckable(True)
            b.setMinimumHeight(54)
            grid.addWidget(b, i // 2, i % 2)
            self._buttons[wells] = b
            b.clicked.connect(lambda checked=False, w=wells: self.set_selected_plate(w))
        self.body.addLayout(grid)
        self.set_selected_plate(12)

    def set_selected_plate(self, wells: int) -> None:
        for w, btn in self._buttons.items():
            btn.setChecked(w == wells)
        self.plate_changed.emit(wells)


class ProtocolCard(NeonCard):
    protocol_builder_clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__("PROTOCOL", parent)
        self.btn_load = QPushButton("Load protocol file...")
        self.btn_load.setObjectName("LarvalSecondaryBtn")
        self.cmb_saved = QComboBox()
        self.cmb_saved.addItems(["Saved in brc", "Startle Response", "Light/Dark"])
        self.btn_builder = QPushButton("Open Protocol Builder")
        self.btn_builder.setObjectName("LarvalLinkBtn")
        self.body.addWidget(self.btn_load)
        self.body.addWidget(self.cmb_saved)
        self.body.addWidget(self.btn_builder)
        self.btn_builder.clicked.connect(self.protocol_builder_clicked.emit)


class CamerasCard(NeonCard):
    def __init__(self, parent=None) -> None:
        super().__init__("CAMERAS", parent)
        self.cmb_top = QComboBox()
        self.cmb_top.addItems(["Top (live preview)", "Machine vision"])
        self.btn_refresh = QPushButton("Refresh cameras")
        self.btn_refresh.setObjectName("LarvalSecondaryBtn")
        self.body.addWidget(self.cmb_top)
        self.body.addWidget(self.btn_refresh)


class HardwareCard(NeonCard):
    def __init__(self, parent=None) -> None:
        super().__init__("HARDWARE", parent)
        self._dots: dict[str, QLabel] = {}
        for key, title in (
            ("camera", "Camera"),
            ("light", "Light"),
            ("buzzer", "Buzzer"),
            ("vibration", "Vibration"),
            ("water", "Water"),
        ):
            row = QHBoxLayout()
            dot = QLabel("●")
            dot.setObjectName("LarvalDanger")
            row.addWidget(QLabel(title), 1)
            row.addWidget(dot, 0, Qt.AlignmentFlag.AlignRight)
            row.addWidget(QLabel("N/A"), 0)
            self._dots[key] = dot
            self.body.addLayout(row)

    def sync_hardware(self, hardware: HardwareService) -> None:
        mp = {d.key: d.status for d in hardware.devices()}
        for key, dot in self._dots.items():
            st = mp.get(key, DeviceStatus.DISCONNECTED)
            if st in (DeviceStatus.ERROR, DeviceStatus.DISCONNECTED):
                dot.setObjectName("LarvalDanger")
            elif st == DeviceStatus.WARNING:
                dot.setObjectName("LarvalWarn")
            else:
                dot.setObjectName("LarvalSuccess")
            dot.style().unpolish(dot)
            dot.style().polish(dot)


class LiveFeedCard(NeonCard):
    def __init__(self, parent=None) -> None:
        super().__init__("LIVE FEED", parent)

        top = QHBoxLayout()
        top.addStretch(1)
        self.lbl_cam = QLabel("No camera")
        self.lbl_cam.setObjectName("LarvalMuted")
        top.addWidget(self.lbl_cam)
        self.body.addLayout(top)

        frame = QFrame()
        frame.setObjectName("LarvalFeedFrame")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(8, 8, 8, 8)
        self.preview = WellPlatePreview()
        self.preview.set_plate(12)
        fl.addWidget(self.preview, 1)
        self.body.addWidget(frame, 1)

        self.title = QLabel("12-WELL PLATE")
        self.title.setObjectName("LarvalFeedTitle")
        subtitle = QLabel("Choose a camera, then enable preview.")
        subtitle.setObjectName("LarvalMuted")
        self.body.addWidget(self.title, 0, Qt.AlignmentFlag.AlignHCenter)
        self.body.addWidget(subtitle, 0, Qt.AlignmentFlag.AlignHCenter)

        controls = QHBoxLayout()
        self.chk_preview = QCheckBox("Camera Preview")
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, 300)
        self.lbl_timer = QLabel("00:00:00")
        self.btn_play = QPushButton("▶")
        self.btn_play.setObjectName("LarvalSecondaryBtn")
        self.btn_add = QPushButton("+")
        self.btn_add.setObjectName("LarvalSecondaryBtn")
        self.chip_300 = QLabel("300s")
        self.chip_300.setObjectName("LarvalChip")
        self.btn_close = QPushButton("x")
        self.btn_close.setObjectName("LarvalSecondaryBtn")
        controls.addWidget(self.chk_preview)
        controls.addWidget(self.timeline_slider, 1)
        controls.addWidget(self.lbl_timer)
        controls.addWidget(self.btn_play)
        controls.addWidget(self.btn_add)
        controls.addWidget(self.chip_300)
        controls.addWidget(self.btn_close)
        self.body.addLayout(controls)

    def set_selected_plate(self, wells: int) -> None:
        self.preview.set_plate(wells)
        self.title.setText(f"{wells}-WELL PLATE")


class RunCard(NeonCard):
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__("RUN", parent)
        self.btn_start = QPushButton("Start experiment")
        self.btn_start.setObjectName("LarvalSuccessBtn")
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("LarvalDangerBtn")
        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setObjectName("LarvalSecondaryBtn")
        self.btn_pause.setEnabled(False)
        self.body.addWidget(self.btn_start)
        self.body.addWidget(self.btn_stop)
        self.body.addWidget(self.btn_pause)
        self.btn_start.clicked.connect(self.start_clicked.emit)
        self.btn_stop.clicked.connect(self.stop_clicked.emit)


class ManualTestCard(NeonCard):
    def __init__(self, parent=None) -> None:
        super().__init__("MANUAL TEST", parent)
        self.btn_light = QPushButton("Light (IR) toggle")
        self.btn_buzzer = QPushButton("Buzzer toggle")
        self.btn_vibration = QPushButton("Vibration toggle")
        self.btn_water = QPushButton("Water toggle")
        for b in (self.btn_light, self.btn_buzzer, self.btn_vibration, self.btn_water):
            b.setObjectName("LarvalSecondaryBtn")
            self.body.addWidget(b)


class TimelineCard(NeonCard):
    def __init__(self, parent=None) -> None:
        super().__init__("EXPERIMENT TIMELINE", parent)
        row = QHBoxLayout()
        for text, obj in (
            ("BASELINE", "LarvalSegA"),
            ("STIMULUS", "LarvalSegB"),
            ("RECOVERY", "LarvalSegA"),
        ):
            s = QLabel(text)
            s.setObjectName(obj)
            s.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.addWidget(s, 1)
        self.body.addLayout(row)


class SessionCard(NeonCard):
    def __init__(self, parent=None) -> None:
        super().__init__("SESSION", parent)
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)
        self.lbl_duration = QLabel("00:00:00")
        self.lbl_clock = QLabel("--:--:--")
        self.lbl_phase = QLabel("Idle")
        self.lbl_stimuli = QLabel("None")
        for i, (k, v) in enumerate(
            (
                ("Duration", self.lbl_duration),
                ("Clock", self.lbl_clock),
                ("Phase", self.lbl_phase),
                ("Stimuli", self.lbl_stimuli),
            )
        ):
            k_lbl = QLabel(k)
            k_lbl.setObjectName("LarvalMuted")
            grid.addWidget(k_lbl, 0, i)
            grid.addWidget(v, 1, i)
        self.body.addLayout(grid)


class ControlsCard(NeonCard):
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__("CONTROLS", parent)
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)

        # Left
        left = QFrame()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.addWidget(QLabel("Frame Rate (FPS)"))
        self.lbl_fps = QLabel("30 FPS")
        self.lbl_fps.setObjectName("LarvalCyan")
        ll.addWidget(self.lbl_fps)
        fps_row = QHBoxLayout()
        self.btn_fps_minus = QPushButton("-")
        self.btn_fps_plus = QPushButton("+")
        self.btn_apply = QPushButton("APPLY")
        for b in (self.btn_fps_minus, self.btn_fps_plus, self.btn_apply):
            b.setObjectName("LarvalSecondaryBtn")
        fps_row.addWidget(self.btn_fps_minus)
        fps_row.addWidget(self.btn_fps_plus)
        fps_row.addWidget(self.btn_apply)
        ll.addLayout(fps_row)
        grid.addWidget(left, 0, 0)

        # Center
        center = QFrame()
        cl = QVBoxLayout(center)
        cl.setContentsMargins(0, 0, 0, 0)
        run = QHBoxLayout()
        self.btn_start = QPushButton("Start")
        self.btn_start.setObjectName("LarvalSuccessBtn")
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("LarvalDangerBtn")
        run.addWidget(self.btn_start)
        run.addWidget(self.btn_stop)
        cl.addLayout(run)
        cap = QHBoxLayout()
        cap.addWidget(QLabel("Rec. cap (s)"))
        self.ed_cap = QLineEdit("300")
        cap.addWidget(self.ed_cap)
        self.chip_lights = QLabel("Lights off")
        self.chip_lights.setObjectName("LarvalChip")
        cap.addWidget(self.chip_lights)
        cl.addLayout(cap)
        ir = QLabel("IR Light / 880 nm")
        ir.setObjectName("LarvalMiniCard")
        wh = QLabel("White Light / 5500 K")
        wh.setObjectName("LarvalMiniCard")
        cl.addWidget(ir)
        cl.addWidget(wh)
        grid.addWidget(center, 0, 1)

        # Right
        right = QFrame()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(QLabel("AUXILIARY"))
        for label in ("Buzzer", "Vibration", "Water circulation"):
            rr = QHBoxLayout()
            rr.addWidget(QLabel(label))
            rr.addStretch(1)
            sw = QCheckBox()
            sw.setChecked(False)
            sw.setObjectName("LarvalSwitch")
            rr.addWidget(sw)
            rl.addLayout(rr)
        grid.addWidget(right, 0, 2)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 1)
        self.body.addLayout(grid)

        self.btn_start.clicked.connect(self.start_clicked.emit)
        self.btn_stop.clicked.connect(self.stop_clicked.emit)


class RecipesSidebar(NeonCard):
    def __init__(self, parent=None) -> None:
        super().__init__("RECIPES", parent)
        recipes = (
            ("Custom Assay", "User-defined parameters"),
            ("Larval Locomotion", "Standard locomotion profile"),
            ("Anxiety Test", "Open field + transitions"),
            ("Predator Exposure", "Cue from overhead"),
            ("Protocol Builder", "Design JSON timeline"),
        )
        for title, sub in recipes:
            btn = QPushButton(f"{title}\n{sub}")
            btn.setObjectName("LarvalRecipeItem")
            btn.setMinimumHeight(56)
            self.body.addWidget(btn)
        self.body.addStretch(1)


class RightSidebar(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        self.run_card = RunCard()
        self.manual_card = ManualTestCard()
        self.plate_selector = WellPlateSelector()
        self.recipes_card = RecipesSidebar()

        lay.addWidget(self.run_card)
        lay.addWidget(self.manual_card)
        lay.addWidget(self.plate_selector)
        lay.addWidget(self.recipes_card)
        lay.addStretch(1)


class EventLogCard(NeonCard):
    def __init__(self, parent=None) -> None:
        super().__init__("STIMULUS / EVENT LOG", parent)
        row = QHBoxLayout()
        self.lbl_empty = QLabel("No events yet.")
        self.lbl_empty.setObjectName("LarvalMuted")
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setObjectName("LarvalLinkBtn")
        row.addWidget(self.lbl_empty, 1)
        row.addWidget(self.btn_clear, 0)
        self.body.addLayout(row)


class FooterStatusBar(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("LarvalFooter")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(6)
        self.hint = QLabel(
            "For 'Custom Assay': set RGB to ~80% intensity, 60 FPS, and ~20 min duration when chamber allows it."
        )
        self.hint.setObjectName("LarvalMuted")
        self.warn = QLabel(
            "Arduino disconnected - connect serial in Settings. No cameras detected - check USB / API camera stack."
        )
        self.warn.setObjectName("LarvalWarn")
        row = QHBoxLayout()
        self.status = QLabel("System: Disconnected   |   Camera: Idle   |   Chamber: Idle   |   Temperature: -   |   Water flow: -")
        self.status.setObjectName("LarvalMuted")
        self.clock = QLabel("")
        self.clock.setObjectName("LarvalMuted")
        row.addWidget(self.status, 1)
        row.addWidget(self.clock, 0)
        lay.addWidget(self.hint)
        lay.addWidget(self.warn)
        lay.addLayout(row)


class LarvalPage(QWidget):
    def __init__(
        self,
        hardware: HardwareService,
        protocols: ProtocolService,
        recorder: RecorderService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._hw = hardware
        self._proto = protocols
        self._rec = recorder
        self._build()
        self._wire()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(500)
        self._tick()

    def _build(self) -> None:
        self.setObjectName("LarvalPageRoot")
        self.setStyleSheet(
            """
            QWidget#LarvalPageRoot { background:#06111F; }
            QFrame#LarvalCard {
                background:#0D1420;
                border:1px solid #15324D;
                border-radius:14px;
            }
            QFrame#LarvalCard:hover { border:1px solid rgba(0,200,255,0.55); }
            QLabel, QCheckBox, QRadioButton { color:#FFFFFF; font-size:12px; }
            QLabel#LarvalCardTitle { color:#CFE8FF; font-size:12px; font-weight:800; letter-spacing:1.0px; }
            QLabel#LarvalMuted { color:#8AA6C1; font-size:11px; }
            QLabel#LarvalCyan { color:#00C8FF; font-size:14px; font-weight:800; }
            QLabel#LarvalSuccess { color:#22C55E; font-weight:700; }
            QLabel#LarvalDanger { color:#FF5D73; font-weight:700; }
            QLabel#LarvalWarn { color:#FACC15; font-weight:700; }
            QLabel#LarvalChip {
                background:#102033; border:1px solid #15324D; border-radius:10px; padding:4px 10px;
                color:#CFE8FF; font-size:11px; font-weight:700;
            }
            QLabel#LarvalFeedTitle { color:#CFE8FF; font-size:12px; font-weight:800; }
            QLabel#LarvalMiniCard {
                background:#102033; border:1px solid #15324D; border-radius:8px; padding:8px 10px; color:#CFE8FF;
            }
            QLabel#LarvalSegA, QLabel#LarvalSegB {
                border-radius:8px; padding:6px 8px; font-size:11px; font-weight:800;
                border:1px solid #15324D; color:#CFE8FF;
            }
            QLabel#LarvalSegA { background:#102033; }
            QLabel#LarvalSegB { background:#5B5CFF; border:1px solid #00C8FF; }
            QFrame#LarvalFeedFrame {
                background:#102033; border:1px solid rgba(0,200,255,0.45); border-radius:12px;
            }
            QPushButton#LarvalPrimaryBtn {
                min-height:36px; border-radius:10px; padding:0 14px; font-size:13px; font-weight:700;
                color:#FFFFFF; border:1px solid rgba(0,200,255,0.7);
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #00C8FF,stop:1 #007BFF);
            }
            QPushButton#LarvalSuccessBtn {
                min-height:36px; border-radius:10px; padding:0 14px; font-size:13px; font-weight:700;
                color:#FFFFFF; border:1px solid rgba(34,197,94,0.8); background:#0E3320;
            }
            QPushButton#LarvalSuccessBtn:hover { background:#124429; border:1px solid #22C55E; }
            QPushButton#LarvalDangerBtn {
                min-height:36px; border-radius:10px; padding:0 14px; font-size:13px; font-weight:700;
                color:#FFFFFF; border:1px solid rgba(255,93,115,0.8); background:#32151B;
            }
            QPushButton#LarvalDangerBtn:hover { background:#421C23; border:1px solid #FF5D73; }
            QPushButton#LarvalSecondaryBtn {
                min-height:34px; border-radius:10px; padding:0 12px; font-size:12px; font-weight:700;
                color:#CFE8FF; border:1px solid #15324D; background:#102033;
            }
            QPushButton#LarvalSecondaryBtn:hover { border:1px solid rgba(0,200,255,0.65); background:#14283f; }
            QPushButton#LarvalLinkBtn {
                min-height:30px; border:none; background:transparent; color:#00C8FF; font-weight:700;
                text-align:left;
            }
            QPushButton#LarvalAssayItem, QPushButton#LarvalRecipeItem {
                min-height:56px; border-radius:10px; border:1px solid #15324D; background:#0B1728;
                color:#CFE8FF; text-align:left; padding:8px 10px; font-size:11px; font-weight:700;
            }
            QPushButton#LarvalAssayItem:checked { border:1px solid #00C8FF; background:#11253b; }
            QPushButton#LarvalAssayItem:hover, QPushButton#LarvalRecipeItem:hover {
                border:1px solid rgba(0,200,255,0.6); background:#11253b;
            }
            QPushButton#LarvalPlateBtn {
                min-height:54px; border-radius:10px; border:1px solid #15324D; background:#102033;
                color:#CFE8FF; font-size:13px; font-weight:800;
            }
            QPushButton#LarvalPlateBtn:hover { border:1px solid rgba(0,200,255,0.65); background:#14283f; }
            QPushButton#LarvalPlateBtn:checked {
                border:1px solid #00C8FF; background:#12314C; color:#FFFFFF;
            }
            QLineEdit, QComboBox {
                min-height:32px; border:1px solid #15324D; border-radius:8px; background:#102033;
                color:#FFFFFF; padding:0 10px; font-size:13px;
            }
            QLineEdit:focus, QComboBox:focus { border:1px solid #00C8FF; }
            QSlider::groove:horizontal { height:4px; background:#15324D; border-radius:2px; }
            QSlider::sub-page:horizontal { background:#00C8FF; border-radius:2px; }
            QSlider::handle:horizontal {
                width:14px; margin:-5px 0; border-radius:7px; background:#00C8FF; border:1px solid #56C6FF;
            }
            QFrame#LarvalFooter { background:#0B1728; border:1px solid #15324D; border-radius:14px; }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        # Top status strip
        self.status_strip = QFrame()
        self.status_strip.setObjectName("LarvalCard")
        sh = QHBoxLayout(self.status_strip)
        sh.setContentsMargins(12, 8, 12, 8)
        self.lbl_idle = QLabel("● Idle")
        self.lbl_idle.setObjectName("LarvalMuted")
        self.lbl_protocol = QLabel("Protocol -")
        self.lbl_run_id = QLabel("Run ID -")
        sh.addWidget(self.lbl_idle)
        sh.addSpacing(12)
        sh.addWidget(self.lbl_protocol)
        sh.addSpacing(12)
        sh.addWidget(self.lbl_run_id)
        sh.addStretch(1)
        sh.addWidget(QLabel("SYSTEM"))
        self.lbl_ready = QLabel("NOT READY")
        self.lbl_ready.setObjectName("LarvalWarn")
        sh.addWidget(self.lbl_ready)
        root.addWidget(self.status_strip)

        # Warning
        self.warning_bar = QFrame()
        self.warning_bar.setObjectName("LarvalCard")
        wh = QHBoxLayout(self.warning_bar)
        wh.setContentsMargins(12, 8, 12, 8)
        self.lbl_warning = QLabel(
            "Arduino not connected - use Settings to connect the serial port. "
            "Lighting and auxiliary controls need the link."
        )
        self.lbl_warning.setObjectName("LarvalWarn")
        self.lbl_warning.setWordWrap(True)
        wh.addWidget(self.lbl_warning)
        root.addWidget(self.warning_bar)

        # Main responsive 3-column body.
        cols = QHBoxLayout()
        cols.setSpacing(12)
        body = QWidget()
        body.setLayout(cols)
        body.setSizePolicy(body.sizePolicy().horizontalPolicy(), body.sizePolicy().verticalPolicy())

        # Left sidebar uses full height and internal scroll.
        left_sc = QScrollArea()
        left_sc.setWidgetResizable(True)
        left_sc.setFrameShape(QFrame.Shape.NoFrame)
        left_sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_wrap = QWidget()
        ll = QVBoxLayout(left_wrap)
        ll.setContentsMargins(0, 0, 0, 0)
        self.assays = AssaySidebar()
        ll.addWidget(self.assays)
        ll.addStretch(1)
        left_sc.setWidget(left_wrap)
        left_sc.setMinimumWidth(260)
        left_sc.setMaximumWidth(300)
        left_sc.setSizePolicy(left_sc.sizePolicy().horizontalPolicy(), left_sc.sizePolicy().verticalPolicy())
        cols.addWidget(left_sc, 0)

        # Center
        center = QWidget()
        cl = QVBoxLayout(center)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(12)

        top_grid = QHBoxLayout()
        top_grid.setSpacing(12)
        col_a = QWidget()
        a = QVBoxLayout(col_a)
        a.setContentsMargins(0, 0, 0, 0)
        a.setSpacing(12)
        self.protocol_card = ProtocolCard()
        self.cameras_card = CamerasCard()
        self.hardware_card = HardwareCard()
        a.addWidget(self.protocol_card)
        a.addWidget(self.cameras_card)
        a.addWidget(self.hardware_card)
        a.addStretch(1)
        col_a.setMinimumWidth(220)
        col_a.setMaximumWidth(260)

        self.live_feed = LiveFeedCard()

        top_grid.addWidget(col_a, 0)
        top_grid.addWidget(self.live_feed, 1)
        cl.addLayout(top_grid)

        self.timeline_card = TimelineCard()
        self.session_card = SessionCard()
        self.controls_card = ControlsCard()
        self.event_log = EventLogCard()
        cl.addWidget(self.timeline_card)
        cl.addWidget(self.session_card)
        cl.addWidget(self.controls_card)
        cl.addWidget(self.event_log)
        center_sc = QScrollArea()
        center_sc.setWidgetResizable(True)
        center_sc.setFrameShape(QFrame.Shape.NoFrame)
        center_sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        center_sc.setWidget(center)
        cols.addWidget(center_sc, 1)

        # Right sidebar uses full height and internal scroll.
        right_sc = QScrollArea()
        right_sc.setWidgetResizable(True)
        right_sc.setFrameShape(QFrame.Shape.NoFrame)
        right_sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_wrap = QWidget()
        rl = QVBoxLayout(right_wrap)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(12)
        self.right_sidebar = RightSidebar()
        self.run_card = self.right_sidebar.run_card
        self.manual_card = self.right_sidebar.manual_card
        self.plate_selector = self.right_sidebar.plate_selector
        self.recipes = self.right_sidebar.recipes_card
        rl.addWidget(self.right_sidebar)
        rl.addStretch(1)
        right_sc.setWidget(right_wrap)
        right_sc.setMinimumWidth(280)
        right_sc.setMaximumWidth(320)
        right_sc.setSizePolicy(right_sc.sizePolicy().horizontalPolicy(), right_sc.sizePolicy().verticalPolicy())
        cols.addWidget(right_sc, 0)

        cols.setStretch(0, 0)
        cols.setStretch(1, 1)
        cols.setStretch(2, 0)
        root.addWidget(body, 1)

        self.footer = FooterStatusBar()
        root.addWidget(self.footer)

    def _wire(self) -> None:
        self.run_card.start_clicked.connect(self._start)
        self.run_card.stop_clicked.connect(self._stop)
        self.controls_card.start_clicked.connect(self._start)
        self.controls_card.stop_clicked.connect(self._stop)
        self.protocol_card.protocol_builder_clicked.connect(self._open_protocol_builder)
        self.live_feed.chk_preview.toggled.connect(self._toggle_preview)
        self.event_log.btn_clear.clicked.connect(lambda: self.event_log.lbl_empty.setText("No events yet."))
        self.manual_card.btn_light.clicked.connect(lambda: self._hw.test_device("light"))
        self.manual_card.btn_buzzer.clicked.connect(lambda: self._hw.test_device("buzzer"))
        self.manual_card.btn_vibration.clicked.connect(lambda: self._hw.test_device("vibration"))
        self.manual_card.btn_water.clicked.connect(lambda: self._hw.test_device("water"))
        self.plate_selector.plate_changed.connect(self.live_feed.set_selected_plate)
        self._hw.devices_changed.connect(self._sync_hardware)
        self._proto.model_changed.connect(self._sync_protocol)
        self._rec.state_changed.connect(self._sync_recorder)

    def _open_protocol_builder(self) -> None:
        mw = self.window()
        if mw is not None and hasattr(mw, "_go_protocol"):
            mw._go_protocol()

    def _toggle_preview(self, on: bool) -> None:
        if on:
            self.event_log.lbl_empty.setText("Preview enabled")
        else:
            self.event_log.lbl_empty.setText("Preview disabled")

    def _start(self) -> None:
        self._rec.start()
        self.event_log.lbl_empty.setText("Recording started")

    def _stop(self) -> None:
        self._rec.stop()
        self.event_log.lbl_empty.setText("Recording stopped")

    def _sync_protocol(self) -> None:
        m = self._proto.model()
        self.lbl_protocol.setText(f"Protocol: {m.name}")

    def _sync_hardware(self) -> None:
        self.hardware_card.sync_hardware(self._hw)
        ready = self._hw.system_ready()
        self.lbl_ready.setText("READY" if ready else "NOT READY")
        self.lbl_ready.setObjectName("LarvalSuccess" if ready else "LarvalWarn")
        self.lbl_ready.style().unpolish(self.lbl_ready)
        self.lbl_ready.style().polish(self.lbl_ready)

    def _sync_recorder(self, state: str) -> None:
        if state == "running":
            self.lbl_idle.setText("● Running")
            self.lbl_idle.setObjectName("LarvalSuccess")
        elif state == "paused":
            self.lbl_idle.setText("● Paused")
            self.lbl_idle.setObjectName("LarvalWarn")
        else:
            self.lbl_idle.setText("● Idle")
            self.lbl_idle.setObjectName("LarvalMuted")
        self.lbl_idle.style().unpolish(self.lbl_idle)
        self.lbl_idle.style().polish(self.lbl_idle)

    def _tick(self) -> None:
        self._sync_protocol()
        self._sync_hardware()
        self.lbl_run_id.setText(f"Run ID: {self._rec.experiment_id}")
        sec = int(self._rec.elapsed_s())
        h, rem = divmod(sec, 3600)
        m, s = divmod(rem, 60)
        self.live_feed.lbl_timer.setText(f"{h:02d}:{m:02d}:{s:02d}")
        self.session_card.lbl_duration.setText(f"{h:02d}:{m:02d}:{s:02d}")
        self.session_card.lbl_clock.setText(datetime.now().strftime("%H:%M:%S"))
        self.footer.clock.setText(QDateTime.currentDateTime().toString("ddd MMM d, yyyy  h:mm AP"))
