"""Adult module — three-column execution dashboard (reference layout)."""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from services.hardware_service import DeviceStatus, HardwareService
from services.protocol_service import ProtocolService
from services.recorder_service import RecorderService
from widgets.camera_view import CameraView
from widgets.card import ZCard
from widgets.timeline_bar import TimelineBar
from widgets.zicons import ICONS, icon


class AssayCard(ZCard):
    clicked = pyqtSignal()

    def mousePressEvent(self, e) -> None:
        self.clicked.emit()
        super().mousePressEvent(e)


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
        self._assay_cards: list[ZCard] = []
        self._recipe_cards: list[ZCard] = []
        self._well_btns: list[QPushButton] = []

        self._build()
        self._wire()
        self._clock = QTimer(self)
        self._clock.timeout.connect(self._tick)
        self._clock.start(500)
        self._tick()

    def _panel_title(self, text: str) -> QLabel:
        t = QLabel(text)
        t.setObjectName("ZPanelTitle")
        return t

    def _banner(self, text: str) -> QFrame:
        b = QFrame()
        b.setObjectName("ZBannerWarn")
        lay = QHBoxLayout(b)
        lay.setContentsMargins(12, 10, 12, 10)
        ic = QLabel()
        ic.setPixmap(icon("fa5s.exclamation-triangle", "#ffb020", 18).pixmap(18, 18))
        lay.addWidget(ic)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color:#ffd79a; font-weight:600;")
        lay.addWidget(lbl, 1)
        return b

    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(14)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)
        split.setOpaqueResize(True)
        split.setHandleWidth(8)
        split.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        split.addWidget(self._left_sidebar())
        split.addWidget(self._center_column())
        split.addWidget(self._right_sidebar())
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setStretchFactor(2, 0)

        split.setSizes([280, 980, 280])
        root.addWidget(split, 1)

    def _left_sidebar(self) -> QWidget:
        w = QScrollArea()
        w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        w.setWidgetResizable(True)
        w.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setSpacing(12)
        lay.addWidget(self._panel_title("TOP RECORDING ASSAYS"))

        assays = [
            ("Multi-Well Plate", "96-well grid tracking", ICONS["grid"]),
            ("Larval Reservoir Maze", "Reservoir navigation", ICONS["route"]),
            ("Alternating T Maze", "Choice alternation", ICONS["split"]),
            ("Open Field Arena", "Exploration arena", ICONS["square_dashed"]),
            ("L/D Choice Assay", "Light / dark preference", ICONS["circle_half"]),
        ]
        for i, (title, sub, fa) in enumerate(assays):
            c = AssayCard(title, sub)
            c.setCursor(Qt.CursorShape.PointingHandCursor)
            ico = QLabel()
            ico.setPixmap(icon(fa, "#1ea7ff", 22).pixmap(22, 22))
            row = QHBoxLayout()
            row.addWidget(ico)
            row.addStretch(1)
            c.body_layout().addLayout(row)
            c.clicked.connect(lambda _=False, idx=i, card=c: self._select_assay(idx, card))
            self._assay_cards.append(c)
            lay.addWidget(c)
        if self._assay_cards:
            self._select_assay(0, self._assay_cards[0])
        lay.addStretch(1)
        w.setWidget(inner)
        w.setMinimumWidth(260)
        return w

    def _select_assay(self, idx: int, card: ZCard) -> None:
        for c in self._assay_cards:
            c.set_selected(c is card)

    def _center_column(self) -> QWidget:
        sc = QScrollArea()
        sc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        v = QVBoxLayout(inner)
        v.setSpacing(12)

        strip = QFrame()
        strip.setObjectName("ZPanel")
        sh = QHBoxLayout(strip)
        sh.setContentsMargins(14, 10, 14, 10)
        self._chip_idle = QLabel("● Idle")
        self._chip_idle.setStyleSheet("color:#94a8c6; font-weight:800;")
        self._lbl_proto = QLabel("Protocol: —")
        self._lbl_proto.setStyleSheet("color:#94a8c6;")
        self._lbl_run = QLabel("Run ID: —")
        self._lbl_run.setStyleSheet("color:#94a8c6;")
        sh.addWidget(self._chip_idle)
        sh.addSpacing(20)
        sh.addWidget(self._lbl_proto)
        sh.addSpacing(16)
        sh.addWidget(self._lbl_run)
        sh.addStretch(1)
        self._sys_ready = QLabel("SYSTEM NOT READY")
        self._sys_ready.setStyleSheet(
            "color:#ff4d5a; font-weight:900; font-size:12px; letter-spacing:0.5px;"
        )
        sh.addWidget(self._sys_ready)
        v.addWidget(strip)

        arduino_ok = self._hw.get("light") and self._hw.get("light").status not in (
            DeviceStatus.DISCONNECTED,
            DeviceStatus.ERROR,
        )
        warn_txt = (
            "Arduino not connected — use Settings to connect serial port."
            if not arduino_ok
            else "System linked — ready for configuration."
        )
        v.addWidget(self._banner(warn_txt))

        proto = QFrame()
        proto.setObjectName("ZPanel")
        pl = QVBoxLayout(proto)
        pl.setContentsMargins(14, 12, 14, 12)
        pl.addWidget(self._panel_title("PROTOCOL"))
        row = QHBoxLayout()
        self._btn_load = QPushButton("Load protocol file")
        self._btn_load.setObjectName("ZBtnGhost")
        self._btn_load.setIcon(icon(ICONS["folder_open"], "#eaf4ff", 16))
        self._combo_saved = QComboBox()
        self._combo_saved.addItems(["Startle Response", "Light/Dark", "Custom…"])
        self._btn_refresh = QPushButton()
        self._btn_refresh.setObjectName("ZBtnOutline")
        self._btn_refresh.setIcon(icon(ICONS["refresh"], "#eaf4ff", 16))
        self._btn_refresh.setFixedWidth(44)
        self._link_pb = QPushButton("Open Protocol Builder")
        self._link_pb.setObjectName("ZBtnOutline")
        self._link_pb.setIcon(icon(ICONS["link"], "#1ea7ff", 14))
        row.addWidget(self._btn_load)
        row.addWidget(self._combo_saved, 1)
        row.addWidget(self._btn_refresh)
        pl.addLayout(row)
        pl.addWidget(self._link_pb)
        v.addWidget(proto)

        cam = QFrame()
        cam.setObjectName("ZPanel")
        cl = QVBoxLayout(cam)
        cl.setContentsMargins(14, 12, 14, 12)
        cl.addWidget(self._panel_title("CAMERA"))
        cr = QHBoxLayout()
        self._cam_top = QComboBox()
        self._cam_top.addItems(["TOP — USB / Basler", "Machine vision"])
        self._cam_side = QComboBox()
        self._cam_side.addItems(["SIDE — USB", "Disabled"])
        self._btn_cam_ref = QPushButton("Refresh")
        self._btn_cam_ref.setObjectName("ZBtnOutline")
        self._btn_cam_ref.setIcon(icon(ICONS["refresh"], "#eaf4ff", 14))
        cr.addWidget(QLabel("Top"))
        cr.addWidget(self._cam_top, 1)
        cr.addWidget(QLabel("Side"))
        cr.addWidget(self._cam_side, 1)
        cr.addWidget(self._btn_cam_ref)
        cl.addLayout(cr)
        v.addWidget(cam)

        hw = QFrame()
        hw.setObjectName("ZPanel")
        hl = QVBoxLayout(hw)
        hl.setContentsMargins(14, 12, 14, 12)
        hl.addWidget(self._panel_title("HARDWARE"))
        self._hw_dots: dict[str, QLabel] = {}
        for key, name in (
            ("camera", "Camera"),
            ("light", "Light"),
            ("buzzer", "Buzzer"),
            ("vibration", "Vibration"),
            ("water", "Water"),
        ):
            row = QHBoxLayout()
            d = QLabel("●")
            d.setFixedWidth(20)
            row.addWidget(d)
            row.addWidget(QLabel(name), 1)
            self._hw_dots[key] = d
            hl.addLayout(row)
        v.addWidget(hw)

        feed = QFrame()
        feed.setObjectName("ZFeedFrame")
        fl = QVBoxLayout(feed)
        fl.setContentsMargins(10, 10, 10, 10)
        top = QHBoxLayout()
        top.addStretch(1)
        self._feed_state = QLabel("Standby")
        self._feed_state.setObjectName("ZFeedBadge")
        top.addWidget(self._feed_state)
        fl.addLayout(top)
        self._cam = CameraView()
        self._cam.setMinimumHeight(320)
        self._cam.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        fl.addWidget(self._cam, 1)
        ctl = QHBoxLayout()
        self._prev_toggle = QCheckBox("Camera preview")
        self._prev_toggle.setChecked(True)
        self._timer_lbl = QLabel("00:00:00")
        self._timer_lbl.setStyleSheet("font-weight:800; color:#1ea7ff;")
        self._btn_play_feed = QPushButton()
        self._btn_play_feed.setObjectName("ZBtnGhost")
        self._btn_play_feed.setIcon(icon(ICONS["play"], "#00d084", 18))
        self._btn_add = QPushButton("+300s")
        self._btn_add.setObjectName("ZBtnOutline")
        self._btn_close_feed = QPushButton()
        self._btn_close_feed.setObjectName("ZIconButton")
        self._btn_close_feed.setIcon(icon(ICONS["close"], "#94a8c6", 14))
        self._btn_close_feed.setFixedSize(36, 36)
        ctl.addWidget(self._prev_toggle)
        ctl.addStretch(1)
        ctl.addWidget(self._timer_lbl)
        ctl.addWidget(self._btn_play_feed)
        ctl.addWidget(self._btn_add)
        ctl.addWidget(self._btn_close_feed)
        fl.addLayout(ctl)
        v.addWidget(feed, 1)

        run = QFrame()
        run.setObjectName("ZPanel")
        rl = QVBoxLayout(run)
        rl.setContentsMargins(14, 12, 14, 12)
        rl.addWidget(self._panel_title("RUN CONTROL"))
        rr = QHBoxLayout()
        self._btn_start = QPushButton("  Start Experiment  ")
        self._btn_start.setObjectName("ZBtnPrimary")
        self._btn_start.setIcon(icon(ICONS["play"], "#041018", 18))
        self._btn_stop = QPushButton("  Stop  ")
        self._btn_stop.setObjectName("ZBtnDanger")
        self._btn_stop.setIcon(icon(ICONS["stop"], "#ff8a93", 16))
        self._btn_pause = QPushButton("  Pause  ")
        self._btn_pause.setObjectName("ZBtnMuted")
        self._btn_pause.setIcon(icon(ICONS["pause"], "#647a9a", 16))
        self._btn_pause.setEnabled(False)
        rr.addWidget(self._btn_start, 2)
        rr.addWidget(self._btn_stop, 1)
        rr.addWidget(self._btn_pause, 1)
        rl.addLayout(rr)
        v.addWidget(run)

        man = QGroupBox("Manual test")
        man.setStyleSheet("QGroupBox { font-weight:800; color:#94a8c6; }")
        ml = QGridLayout(man)
        self._t_light = QPushButton("Light")
        self._t_light.setCheckable(True)
        self._t_light.setObjectName("ZBtnGhost")
        self._t_light.setIcon(icon(ICONS["light"], "#ffb020", 18))
        self._t_buzz = QPushButton("Buzzer")
        self._t_buzz.setCheckable(True)
        self._t_buzz.setObjectName("ZBtnGhost")
        self._t_buzz.setIcon(icon(ICONS["volume"], "#1ea7ff", 18))
        self._t_vib = QPushButton("Vibration")
        self._t_vib.setCheckable(True)
        self._t_vib.setObjectName("ZBtnGhost")
        self._t_vib.setIcon(icon(ICONS["zap"], "#00d4ff", 18))
        self._t_water = QPushButton("Water")
        self._t_water.setCheckable(True)
        self._t_water.setObjectName("ZBtnGhost")
        self._t_water.setIcon(icon(ICONS["droplet"], "#7c4dff", 18))
        ml.addWidget(self._t_light, 0, 0)
        ml.addWidget(self._t_buzz, 0, 1)
        ml.addWidget(self._t_vib, 1, 0)
        ml.addWidget(self._t_water, 1, 1)
        v.addWidget(man)

        tl = QFrame()
        tl.setObjectName("ZPanel")
        tlay = QVBoxLayout(tl)
        tlay.setContentsMargins(14, 12, 14, 12)
        tlay.addWidget(self._panel_title("TIMELINE"))
        self._timeline = TimelineBar()
        tlay.addWidget(self._timeline)
        v.addWidget(tl)

        foot = QHBoxLayout()
        self._foot_dur = QLabel("Duration: 00:00")
        self._foot_clock = QLabel("")
        self._foot_phase = QLabel("Phase: —")
        self._foot_stim = QLabel("Stimuli: —")
        for x in (self._foot_dur, self._foot_clock, self._foot_phase, self._foot_stim):
            x.setStyleSheet("color:#94a8c6; font-weight:700;")
        foot.addWidget(self._foot_dur)
        foot.addStretch(1)
        foot.addWidget(self._foot_clock)
        foot.addStretch(1)
        foot.addWidget(self._foot_phase)
        foot.addStretch(1)
        foot.addWidget(self._foot_stim)
        v.addLayout(foot)

        sc.setWidget(inner)
        return sc

    def _right_sidebar(self) -> QWidget:
        w = QScrollArea()
        w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        w.setWidgetResizable(True)
        w.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setSpacing(12)
        lay.addWidget(self._panel_title("SELECT WELL PLATE"))
        g = QGridLayout()
        g.setSpacing(8)
        wgrp = QButtonGroup(self)
        wgrp.setExclusive(True)
        for i, label in enumerate(("12", "24", "48", "96")):
            b = QPushButton(label)
            b.setObjectName("ZWellPick")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            r, c = divmod(i, 2)
            g.addWidget(b, r, c)
            self._well_btns.append(b)
            wgrp.addButton(b)
        if self._well_btns:
            self._well_btns[-1].setChecked(True)
        lay.addLayout(g)

        lay.addWidget(self._panel_title("RECIPES"))
        recipes = [
            ("Custom Assay", "User-defined parameters", ICONS["grid"]),
            ("Larval Locomotion", "Swim kinematics", ICONS["route"]),
            ("Anxiety Test", "Novel tank diving", ICONS["split"]),
            ("Predator Exposure", "Cue from overhead", ICONS["square_dashed"]),
            ("Protocol Builder", "Design JSON timeline", ICONS["protocol"]),
        ]
        for title, sub, fa in recipes:
            c = ZCard(title, sub)
            ico = QLabel()
            ico.setPixmap(icon(fa, "#00d4ff", 20).pixmap(20, 20))
            hh = QHBoxLayout()
            hh.addWidget(ico)
            hh.addStretch(1)
            c.body_layout().addLayout(hh)
            lay.addWidget(c)
            self._recipe_cards.append(c)

        lay.addStretch(1)
        w.setWidget(inner)
        w.setMinimumWidth(260)
        return w

    def _wire(self) -> None:
        self._btn_start.clicked.connect(self._start)
        self._btn_stop.clicked.connect(self._stop)
        self._hw.devices_changed.connect(self._refresh_hw)
        self._proto.model_changed.connect(self._sync_proto_labels)
        self._rec.state_changed.connect(self._on_rec_state)
        self._btn_load.clicked.connect(
            lambda: self._proto.set_meta(self._proto.model().name, self._proto.model().description)
        )
        self._link_pb.clicked.connect(self._open_protocol_builder)
        self._t_light.clicked.connect(lambda: self._hw.test_device("light"))
        self._t_buzz.clicked.connect(lambda: self._hw.test_device("buzzer"))
        self._t_vib.clicked.connect(lambda: self._hw.test_device("vibration"))
        self._t_water.clicked.connect(lambda: self._hw.test_device("water"))

    def _start(self) -> None:
        self._rec.start()
        self._cam.set_recording(True)
        self._feed_state.setText("Live")
        self._feed_state.setStyleSheet(
            "background-color: rgba(0,208,132,0.2); border: 1px solid rgba(0,208,132,0.55);"
            "border-radius:10px; padding:4px 12px; font-weight:900; color:#00d084;"
        )

    def _stop(self) -> None:
        self._rec.stop()
        self._cam.set_recording(False)
        self._feed_state.setText("Standby")
        self._feed_state.setObjectName("ZFeedBadge")
        self._feed_state.style().unpolish(self._feed_state)
        self._feed_state.style().polish(self._feed_state)

    def _on_rec_state(self, s: str) -> None:
        self._chip_idle.setText(f"● {s.title()}")

    def _sync_proto_labels(self) -> None:
        m = self._proto.model()
        self._lbl_proto.setText(f"Protocol: {m.name}")
        phases = " / ".join(p.name for p in m.phases[:3])
        self._foot_phase.setText(f"Phase: {m.phases[0].name}" if m.phases else "Phase: —")
        self._foot_stim.setText(f"Timeline: {phases}")

    def _tick(self) -> None:
        self._lbl_run.setText(f"Run ID: {self._rec.experiment_id}")
        sec = int(self._rec.elapsed_s())
        h, r = divmod(sec, 3600)
        m, s = divmod(r, 60)
        self._foot_dur.setText(f"Duration: {h:02d}:{m:02d}:{s:02d}")
        self._timer_lbl.setText(f"{h:02d}:{m:02d}:{s:02d}")
        self._foot_clock.setText(datetime.now().strftime("%H:%M:%S"))
        ready = self._hw.system_ready()
        self._sys_ready.setText("SYSTEM READY" if ready else "SYSTEM NOT READY")
        self._sys_ready.setStyleSheet(
            "color:#00d084; font-weight:900; font-size:12px;"
            if ready
            else "color:#ff4d5a; font-weight:900; font-size:12px;"
        )
        self._sync_proto_labels()

    def _open_protocol_builder(self) -> None:
        mw = self.window()
        if mw is not None and hasattr(mw, "_go_protocol"):
            mw._go_protocol()

    def _refresh_hw(self) -> None:
        mp = {d.key: d.status for d in self._hw.devices()}
        for k, dot in self._hw_dots.items():
            st = mp.get(k, DeviceStatus.DISCONNECTED)
            col = "#00d084"
            if st in (DeviceStatus.ERROR, DeviceStatus.DISCONNECTED):
                col = "#ff4d5a"
            elif st == DeviceStatus.WARNING:
                col = "#ffb020"
            dot.setStyleSheet(f"color:{col}; font-size:16px;")
