"""Adult page — premium dark neon ZIMON dashboard."""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from services.hardware_service import DeviceStatus, HardwareService
from services.protocol_service import ProtocolService
from services.recorder_service import RecorderService
from widgets.camera_view import CameraView
from widgets.zicons import ICONS, icon


class SettingsLikeCard(QFrame):
    """Base neon card shell used by all adult-page sections."""

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("AdultNeonCard")
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("AdultCardTitle")
        root.addWidget(title_lbl)
        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(10)
        root.addLayout(self.body)


class StimulusControlCard(SettingsLikeCard):
    def __init__(self, parent=None) -> None:
        super().__init__("STIMULUS CONTROL", parent)

        # Light header
        top = QHBoxLayout()
        self.chk_light = QCheckBox("Light")
        self.chk_light.setChecked(True)
        top.addWidget(self.chk_light)
        top.addStretch(1)
        self.btn_light_edit = QPushButton("✎")
        self.btn_light_set = QPushButton("⚙")
        for b in (self.btn_light_edit, self.btn_light_set):
            b.setObjectName("AdultSecondaryBtn")
            b.setFixedSize(30, 30)
        top.addWidget(self.btn_light_edit)
        top.addWidget(self.btn_light_set)
        self.body.addLayout(top)

        seg = QHBoxLayout()
        self.btn_ir = QPushButton("IR")
        self.btn_white = QPushButton("White")
        self.btn_rgb = QPushButton("RGB")
        self.type_group = QButtonGroup(self)
        self.type_group.setExclusive(True)
        for b in (self.btn_ir, self.btn_white, self.btn_rgb):
            b.setObjectName("AdultSecondaryBtn")
            b.setCheckable(True)
            self.type_group.addButton(b)
            seg.addWidget(b)
        self.btn_ir.setChecked(True)
        self.body.addLayout(seg)

        self.slider_intensity = QSlider(Qt.Orientation.Horizontal)
        self.slider_intensity.setRange(0, 100)
        self.slider_intensity.setValue(80)
        ir = QHBoxLayout()
        ir.addWidget(QLabel("Intensity"))
        ir.addStretch(1)
        self.lbl_intensity = QLabel("80%")
        self.lbl_intensity.setObjectName("AdultMuted")
        ir.addWidget(self.lbl_intensity)
        self.body.addLayout(ir)
        self.body.addWidget(self.slider_intensity)

        mode = QHBoxLayout()
        mode.addWidget(QLabel("Mode"))
        mode.addStretch(1)
        self.rb_cont = QRadioButton("Continuous")
        self.rb_pulse = QRadioButton("Pulse")
        self.rb_cont.setChecked(True)
        mode.addWidget(self.rb_cont)
        mode.addWidget(self.rb_pulse)
        self.body.addLayout(mode)

        ff = QFormLayout()
        ff.setHorizontalSpacing(10)
        ff.setVerticalSpacing(8)
        self.ed_freq = QLineEdit("5 Hz")
        self.ed_pw = QLineEdit("50 ms")
        self.ed_dur = QLineEdit("1 sec")
        ff.addRow("Frequency", self.ed_freq)
        ff.addRow("Pulse Width", self.ed_pw)
        ff.addRow("Duration", self.ed_dur)
        self.body.addLayout(ff)

        self.slider_freq = QSlider(Qt.Orientation.Horizontal)
        self.slider_freq.setRange(1, 20)
        self.slider_freq.setValue(5)
        self.slider_pw = QSlider(Qt.Orientation.Horizontal)
        self.slider_pw.setRange(1, 100)
        self.slider_pw.setValue(50)
        self.slider_dur = QSlider(Qt.Orientation.Horizontal)
        self.slider_dur.setRange(1, 10)
        self.slider_dur.setValue(1)
        self.body.addWidget(self.slider_freq)
        self.body.addWidget(self.slider_pw)
        self.body.addWidget(self.slider_dur)

        divider = QFrame()
        divider.setObjectName("AdultDivider")
        self.body.addWidget(divider)

        # Buzzer
        buz = QHBoxLayout()
        self.chk_buzzer = QCheckBox("Buzzer")
        self.chk_buzzer.setChecked(True)
        buz.addWidget(self.chk_buzzer)
        buz.addStretch(1)
        self.body.addLayout(buz)

        tone = QHBoxLayout()
        self.btn_noise = QPushButton("Noise")
        self.btn_file = QPushButton("File")
        self.tone_group = QButtonGroup(self)
        self.tone_group.setExclusive(True)
        for b in (self.btn_noise, self.btn_file):
            b.setObjectName("AdultSecondaryBtn")
            b.setCheckable(True)
            self.tone_group.addButton(b)
            tone.addWidget(b)
        self.btn_noise.setChecked(True)
        self.body.addLayout(tone)

        bf = QFormLayout()
        self.ed_amp = QLineEdit("70 ms")
        bf.addRow("Amplitude", self.ed_amp)
        dur_row = QWidget()
        dur_l = QHBoxLayout(dur_row)
        dur_l.setContentsMargins(0, 0, 0, 0)
        self.chk_buzz_dur = QCheckBox("Duration")
        self.chk_buzz_dur.setChecked(True)
        self.ed_buzz_dur = QLineEdit("1 sec")
        dur_l.addWidget(self.chk_buzz_dur)
        dur_l.addWidget(self.ed_buzz_dur)
        bf.addRow("", dur_row)
        self.body.addLayout(bf)
        self.body.addStretch(1)


class CameraPreviewCard(SettingsLikeCard):
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__("LIVE CAMERA PREVIEW", parent)
        host = QFrame()
        host.setObjectName("AdultPreviewFrame")
        hl = QVBoxLayout(host)
        hl.setContentsMargins(8, 8, 8, 8)
        self.view = CameraView()
        self.view.setMinimumHeight(280)
        self.view.set_status_text("Live aquarium preview")
        hl.addWidget(self.view, 1)
        self.body.addWidget(host, 1)

        controls = QHBoxLayout()
        self.btn_start = QPushButton("Start")
        self.btn_start.setObjectName("AdultPrimaryBtn")
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("AdultSecondaryBtn")
        self.cmb_duration = QComboBox()
        self.cmb_duration.addItems(["00:00", "00:30", "01:00"])
        self.rb_manual = QRadioButton("Manual")
        self.rb_protocol = QRadioButton("Protocol")
        self.rb_manual.setChecked(True)
        self.cmb_fps = QComboBox()
        self.cmb_fps.addItems(["30", "60"])
        controls.addWidget(self.btn_start)
        controls.addWidget(self.btn_stop)
        controls.addWidget(QLabel("Duration"))
        controls.addWidget(self.cmb_duration)
        controls.addStretch(1)
        controls.addWidget(self.rb_manual)
        controls.addWidget(self.rb_protocol)
        controls.addWidget(QLabel("FPS"))
        controls.addWidget(self.cmb_fps)
        self.body.addLayout(controls)

        self.btn_start.clicked.connect(self.start_clicked.emit)
        self.btn_stop.clicked.connect(self.stop_clicked.emit)


class TimelineCard(SettingsLikeCard):
    def __init__(self, parent=None) -> None:
        super().__init__("TIMELINE", parent)
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        grid.addWidget(QLabel(""), 0, 0)
        for c, name in enumerate(("Baseline", "Light Pulse", "Recovery"), start=1):
            h = QLabel(name)
            h.setObjectName("AdultTimelineHeader")
            grid.addWidget(h, 0, c)

        rows = ("Light", "Buzzer", "Vibration")
        shades = {
            "Light": ("#1a2a44", "#00C8FF", "#1a2a44"),
            "Buzzer": ("#1a2a44", "#5B5CFF", "#1a2a44"),
            "Vibration": ("#1a2a44", "#8FA0FF", "#1a2a44"),
        }
        for r, row_name in enumerate(rows, start=1):
            l = QLabel(row_name)
            l.setObjectName("AdultMuted")
            grid.addWidget(l, r, 0)
            for c in range(3):
                seg = QFrame()
                seg.setObjectName("AdultTimeSeg")
                seg.setStyleSheet(
                    f"QFrame {{ background:{shades[row_name][c]}; border:1px solid #15324D; border-radius:6px; }}"
                )
                seg.setMinimumHeight(16)
                grid.addWidget(seg, r, c + 1)
        self.body.addLayout(grid)

        row = QHBoxLayout()
        row.addWidget(QLabel("Protocol:"))
        self.cmb_protocol = QComboBox()
        self.cmb_protocol.addItems(["Startle Response", "Light/Dark Test"])
        row.addWidget(self.cmb_protocol, 1)
        self.body.addLayout(row)


class AssaySidebarCard(SettingsLikeCard):
    protocol_builder_clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__("ASSAY SELECT", parent)
        top = QHBoxLayout()
        self.btn_top = QPushButton("TOP")
        self.btn_side = QPushButton("SIDE")
        group = QButtonGroup(self)
        group.setExclusive(True)
        for b in (self.btn_top, self.btn_side):
            b.setObjectName("AdultSecondaryBtn")
            b.setCheckable(True)
            group.addButton(b)
            top.addWidget(b)
        self.btn_top.setChecked(True)
        self.body.addLayout(top)

        self.lbl_ready = QLabel("System Ready: YES")
        self.lbl_ready.setObjectName("AdultSuccess")
        self.body.addWidget(self.lbl_ready)

        q = SettingsLikeCard("Quick Actions")
        self.btn_startle = QPushButton("Startle Response  ›")
        self.btn_lightdark = QPushButton("Light/Dark Test  ›")
        self.btn_load = QPushButton("Load Assay  ›")
        self.btn_new = QPushButton("Create New  ›")
        self.btn_builder = QPushButton("Protocol Builder  ›")
        for b in (
            self.btn_startle,
            self.btn_lightdark,
            self.btn_load,
            self.btn_new,
            self.btn_builder,
        ):
            b.setObjectName("AdultListBtn")
            q.body.addWidget(b)
        q.body.addStretch(1)
        self.body.addWidget(q)
        self.body.addStretch(1)

        self.btn_builder.clicked.connect(self.protocol_builder_clicked.emit)


class FooterStatusBar(QFrame):
    run_clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("AdultFooter")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(12)
        self.lbl_msg = QLabel("●  All devices connected and ready. You're good to begin.")
        self.lbl_msg.setObjectName("AdultFooterMsg")
        lay.addWidget(self.lbl_msg, 1)
        self.btn_run = QPushButton("Run Protocol")
        self.btn_run.setObjectName("AdultPrimaryBtn")
        self.btn_run.setMinimumWidth(180)
        self.btn_run.clicked.connect(self.run_clicked.emit)
        lay.addWidget(self.btn_run, 0, Qt.AlignmentFlag.AlignRight)

    def set_ready(self, ready: bool) -> None:
        if ready:
            self.lbl_msg.setText("●  All devices connected and ready. You're good to begin.")
            self.lbl_msg.setObjectName("AdultFooterMsg")
        else:
            self.lbl_msg.setText("●  Some devices are not ready. Check Environment first.")
            self.lbl_msg.setObjectName("AdultFooterWarn")
        self.lbl_msg.style().unpolish(self.lbl_msg)
        self.lbl_msg.style().polish(self.lbl_msg)


class AdultPage(QWidget):
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
        self.setObjectName("AdultPageRoot")
        self.setStyleSheet(
            """
            QWidget#AdultPageRoot { background:#06111F; }
            QFrame#AdultNeonCard {
                background:#0D1420;
                border:1px solid #15324D;
                border-radius:14px;
            }
            QFrame#AdultNeonCard:hover {
                border:1px solid rgba(0,200,255,0.55);
            }
            QLabel#AdultCardTitle {
                color:#CFE8FF;
                font-size:12px;
                font-weight:800;
                letter-spacing:1.0px;
            }
            QLabel { color:#FFFFFF; font-size:12px; }
            QLabel#AdultMuted { color:#8AA6C1; font-size:11px; }
            QLabel#AdultSuccess { color:#22C55E; font-size:12px; font-weight:700; }
            QLabel#AdultTimelineHeader {
                color:#CFE8FF; font-size:11px; font-weight:700;
                background:#102033; border:1px solid #15324D; border-radius:6px; padding:4px 8px;
            }
            QFrame#AdultPreviewFrame {
                background:#102033;
                border:1px solid rgba(0,200,255,0.45);
                border-radius:12px;
            }
            QPushButton#AdultPrimaryBtn {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #00C8FF,stop:1 #007BFF);
                color:#FFFFFF; border:1px solid rgba(0,200,255,0.7); border-radius:10px;
                min-height:36px; padding:0 14px; font-size:13px; font-weight:700;
            }
            QPushButton#AdultPrimaryBtn:hover {
                border:1px solid #00C8FF;
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #23D3FF,stop:1 #248FFF);
            }
            QPushButton#AdultSecondaryBtn {
                background:#102033; color:#CFE8FF;
                border:1px solid #15324D; border-radius:10px;
                min-height:36px; padding:0 12px; font-size:13px; font-weight:700;
            }
            QPushButton#AdultSecondaryBtn:hover {
                border:1px solid rgba(0,200,255,0.65);
                background:#14283f;
            }
            QPushButton#AdultListBtn {
                background:#0B1728; color:#CFE8FF; border:1px solid #15324D; border-radius:10px;
                min-height:34px; padding:0 10px; font-size:12px; font-weight:700; text-align:left;
            }
            QPushButton#AdultListBtn:hover {
                border:1px solid rgba(0,200,255,0.6);
                background:#11253b;
            }
            QLineEdit, QComboBox {
                min-height:32px; border:1px solid #15324D; border-radius:8px; background:#102033;
                color:#FFFFFF; padding:0 10px; font-size:13px;
            }
            QLineEdit:focus, QComboBox:focus { border:1px solid #00C8FF; }
            QRadioButton, QCheckBox { color:#CFE8FF; font-size:12px; }
            QSlider::groove:horizontal { height:4px; background:#15324D; border-radius:2px; }
            QSlider::sub-page:horizontal { background:#00C8FF; border-radius:2px; }
            QSlider::handle:horizontal {
                width:14px; margin:-5px 0; border-radius:7px; background:#00C8FF; border:1px solid #56C6FF;
            }
            QFrame#AdultDivider { background:#15324D; min-height:1px; max-height:1px; border:none; }
            QFrame#AdultFooter {
                background:#0B1728; border:1px solid #15324D; border-radius:14px;
            }
            QLabel#AdultFooterMsg { color:#22C55E; font-size:12px; font-weight:600; }
            QLabel#AdultFooterWarn { color:#FACC15; font-size:12px; font-weight:600; }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(12)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_wrap = QWidget()
        lw = QVBoxLayout(left_wrap)
        lw.setContentsMargins(0, 0, 0, 0)
        self.stimulus = StimulusControlCard()
        lw.addWidget(self.stimulus)
        lw.addStretch(1)
        left_scroll.setWidget(left_wrap)
        left_scroll.setMinimumWidth(300)
        left_scroll.setMaximumWidth(340)

        center = QWidget()
        cl = QVBoxLayout(center)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(12)
        self.preview = CameraPreviewCard()
        self.timeline = TimelineCard()
        cl.addWidget(self.preview, 1)
        cl.addWidget(self.timeline, 0)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self.assay = AssaySidebarCard()
        rl.addWidget(self.assay)
        rl.addStretch(1)
        right.setMinimumWidth(250)
        right.setMaximumWidth(290)

        top.addWidget(left_scroll, 0)
        top.addWidget(center, 1)
        top.addWidget(right, 0)
        root.addLayout(top, 1)

        self.footer = FooterStatusBar()
        root.addWidget(self.footer, 0)

    def _wire(self) -> None:
        self.preview.start_clicked.connect(self._start_recording)
        self.preview.stop_clicked.connect(self._stop_recording)
        self.footer.run_clicked.connect(self._start_recording)
        self.stimulus.slider_intensity.valueChanged.connect(
            lambda v: self.stimulus.lbl_intensity.setText(f"{v}%")
        )
        self.assay.protocol_builder_clicked.connect(self._open_protocol_builder)
        self._hw.devices_changed.connect(self._sync_hardware)
        self._proto.model_changed.connect(self._sync_protocol)
        self._rec.state_changed.connect(self._sync_recorder_state)

    def _open_protocol_builder(self) -> None:
        mw = self.window()
        if mw is not None and hasattr(mw, "_go_protocol"):
            mw._go_protocol()

    def _start_recording(self) -> None:
        self._rec.start()
        self.preview.view.set_recording(True)
        self.preview.view.set_status_text("Recording in progress")

    def _stop_recording(self) -> None:
        self._rec.stop()
        self.preview.view.set_recording(False)
        self.preview.view.set_status_text("Live aquarium preview")

    def _sync_protocol(self) -> None:
        model = self._proto.model()
        if self.timeline.cmb_protocol.findText(model.name) < 0:
            self.timeline.cmb_protocol.addItem(model.name)
        self.timeline.cmb_protocol.setCurrentText(model.name)

    def _sync_hardware(self) -> None:
        ready = self._hw.system_ready()
        self.footer.set_ready(ready)
        self.assay.lbl_ready.setText("System Ready: YES" if ready else "System Ready: NO")
        self.assay.lbl_ready.setObjectName("AdultSuccess" if ready else "AdultFooterWarn")
        self.assay.lbl_ready.style().unpolish(self.assay.lbl_ready)
        self.assay.lbl_ready.style().polish(self.assay.lbl_ready)

    def _sync_recorder_state(self, state: str) -> None:
        if state in ("stopped", "idle"):
            self.preview.view.set_recording(False)
        elif state == "running":
            self.preview.view.set_recording(True)

    def _tick(self) -> None:
        self._sync_protocol()
        self._sync_hardware()
        if self._rec.is_running():
            sec = int(self._rec.elapsed_s())
            m, s = divmod(sec, 60)
            self.preview.cmb_duration.setCurrentText(f"{m:02d}:{s:02d}")
        self.preview.setToolTip(f"Updated {datetime.now():%H:%M:%S}")

        mp = {d.key: d.status for d in self._hw.devices()}
        cam_status = mp.get("camera", DeviceStatus.DISCONNECTED)
        if cam_status in (DeviceStatus.DISCONNECTED, DeviceStatus.ERROR):
            self.preview.view.set_status_text("Camera offline")
