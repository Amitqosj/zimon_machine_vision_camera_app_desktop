"""Larval module — same dashboard pattern as Adult, compact (top camera only)."""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
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


class LarvalAssayCard(ZCard):
    clicked = pyqtSignal()

    def mousePressEvent(self, e) -> None:
        self.clicked.emit()
        super().mousePressEvent(e)


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
        self._assays: list[LarvalAssayCard] = []
        self._build()
        self._wire()
        QTimer(self, timeout=self._tick).start(500)
        self._tick()

    def _pt(self, t: str) -> QLabel:
        x = QLabel(t)
        x.setObjectName("ZPanelTitle")
        return x

    def _build(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)
        sp = QSplitter(Qt.Orientation.Horizontal)
        sp.setChildrenCollapsible(False)
        sp.setOpaqueResize(True)
        sp.setHandleWidth(8)
        sp.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        left = QScrollArea()
        left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left.setWidgetResizable(True)
        left.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        iw = QWidget()
        il = QVBoxLayout(iw)
        il.setSpacing(10)
        il.addWidget(self._pt("LARVAL ASSAYS"))
        for title, sub, fa in (
            ("Multi-Well Plate", "High-density larvae", ICONS["grid"]),
            ("Reservoir Maze", "Depth preference", ICONS["route"]),
            ("Open Field", "Locomotion burst", ICONS["square_dashed"]),
        ):
            c = LarvalAssayCard(title, sub)
            ic = QLabel()
            ic.setPixmap(icon(fa, "#00d4ff", 20).pixmap(20, 20))
            r = QHBoxLayout()
            r.addWidget(ic)
            r.addStretch(1)
            c.body_layout().addLayout(r)
            c.clicked.connect(lambda _=False, card=c: self._pick(card))
            self._assays.append(c)
            il.addWidget(c)
        if self._assays:
            self._pick(self._assays[0])
        il.addStretch(1)
        left.setWidget(iw)
        left.setMinimumWidth(220)

        center = QWidget()
        center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cl = QVBoxLayout(center)
        cl.setSpacing(10)
        strip = QFrame()
        strip.setObjectName("ZPanel")
        strip.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        sh = QHBoxLayout(strip)
        sh.setContentsMargins(12, 8, 12, 8)
        self._status = QLabel("● Idle")
        self._status.setStyleSheet("color:#94a8c6; font-weight:800;")
        self._proto_lbl = QLabel("Protocol: —")
        self._proto_lbl.setStyleSheet("color:#94a8c6;")
        sh.addWidget(self._status)
        sh.addSpacing(16)
        sh.addWidget(self._proto_lbl, 1)
        cl.addWidget(strip)

        cam = QFrame()
        cam.setObjectName("ZPanel")
        cam.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        cv = QVBoxLayout(cam)
        cv.setContentsMargins(12, 10, 12, 10)
        cv.addWidget(self._pt("TOP CAMERA"))
        self._cam_combo = QLabel("Machine vision — TOP")
        self._cam_combo.setStyleSheet("font-weight:700; color:#eaf4ff;")
        cv.addWidget(self._cam_combo)
        cl.addWidget(cam)

        hw = QFrame()
        hw.setObjectName("ZPanel")
        hw.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        hv = QVBoxLayout(hw)
        hv.setContentsMargins(12, 10, 12, 10)
        hv.addWidget(self._pt("HARDWARE"))
        self._dots: dict[str, QLabel] = {}
        for k, n in (("camera", "Camera"), ("light", "Light"), ("buzzer", "Buzzer")):
            row = QHBoxLayout()
            d = QLabel("●")
            self._dots[k] = d
            row.addWidget(d)
            row.addWidget(QLabel(n), 1)
            hv.addLayout(row)
        cl.addWidget(hw)

        feed = QFrame()
        feed.setObjectName("ZFeedFrame")
        fv = QVBoxLayout(feed)
        fv.setContentsMargins(8, 8, 8, 8)
        self._view = CameraView()
        self._view.setMinimumHeight(260)
        self._view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        fv.addWidget(self._view, 1)
        cl.addWidget(feed, 1)

        tl = QFrame()
        tl.setObjectName("ZPanel")
        tl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        tv = QVBoxLayout(tl)
        tv.setContentsMargins(12, 10, 12, 10)
        tv.addWidget(self._pt("TIMELINE"))
        tv.addWidget(TimelineBar())
        cl.addWidget(tl)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(100)
        self._log.setPlaceholderText("Event log…")
        cl.addWidget(self._log)

        right = QFrame()
        right.setObjectName("ZPanel")
        right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        rv = QVBoxLayout(right)
        rv.setContentsMargins(12, 12, 12, 12)
        self._go = QPushButton("Start")
        self._go.setObjectName("ZBtnPrimary")
        self._go.setIcon(icon(ICONS["play"], "#041018", 18))
        self._btn_stop = QPushButton("Stop")
        self._btn_stop.setObjectName("ZBtnDanger")
        self._btn_stop.setIcon(icon(ICONS["stop"], "#ff8a93", 16))
        rv.addWidget(self._go)
        rv.addWidget(self._btn_stop)
        rv.addStretch(1)
        right.setMinimumWidth(200)

        sp.addWidget(left)
        sp.addWidget(center)
        sp.addWidget(right)
        sp.setStretchFactor(0, 0)
        sp.setStretchFactor(1, 1)
        sp.setStretchFactor(2, 0)
        sp.setSizes([220, 1000, 210])
        lay.addWidget(sp, 1)

    def _pick(self, card: LarvalAssayCard) -> None:
        for c in self._assays:
            c.set_selected(c is card)

    def _wire(self) -> None:
        self._go.clicked.connect(self._start)
        self._btn_stop.clicked.connect(self._stop_experiment)
        self._hw.devices_changed.connect(self._dots_refresh)
        self._proto.model_changed.connect(self._proto_refresh)

    def _start(self) -> None:
        self._rec.start()
        self._view.set_recording(True)
        self._log.appendPlainText(f"[{datetime.now():%H:%M:%S}] Started.")

    def _stop_experiment(self) -> None:
        self._rec.stop()
        self._view.set_recording(False)
        self._log.appendPlainText(f"[{datetime.now():%H:%M:%S}] Stopped.")

    def _proto_refresh(self) -> None:
        self._proto_lbl.setText(f"Protocol: {self._proto.model().name}")

    def _dots_refresh(self) -> None:
        mp = {d.key: d.status for d in self._hw.devices()}
        for k, d in self._dots.items():
            st = mp.get(k, DeviceStatus.DISCONNECTED)
            col = "#00d084" if st not in (DeviceStatus.ERROR, DeviceStatus.DISCONNECTED) else "#ff4d5a"
            d.setStyleSheet(f"color:{col}; font-size:15px;")

    def _tick(self) -> None:
        self._proto_refresh()
        self._dots_refresh()
        if self._rec.is_running():
            self._status.setText("● Running")
        else:
            self._status.setText("● Idle")
