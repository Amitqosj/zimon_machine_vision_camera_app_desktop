"""Environment — camera + stimulus readiness (reference layout)."""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from services.hardware_service import DeviceStatus, HardwareService
from widgets.status_chip import ChipTone, StatusChip
from widgets.zicons import ICONS, icon


class EnvironmentPage(QWidget):
    def __init__(self, hardware: HardwareService, parent=None) -> None:
        super().__init__(parent)
        self._hw = hardware
        self._cam_chips: list[StatusChip] = []
        self._cam_subs: list[QLabel] = []
        self._stim_chips: dict[str, StatusChip] = {}
        self._build()
        self._hw.devices_changed.connect(self._sync)
        self._hw.log_message.connect(self._append_log)
        self._sync()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        head = QFrame()
        head.setObjectName("ZPanel")
        head.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        hh = QHBoxLayout(head)
        hh.setContentsMargins(12, 10, 12, 10)
        hh.setSpacing(12)
        col = QVBoxLayout()
        col.setSpacing(2)
        t1 = QLabel("ENVIRONMENT")
        t1.setStyleSheet(
            "font-size:10px; font-weight:800; letter-spacing:1px; color:#94a8c6;"
        )
        t2 = QLabel("Environment / System readiness")
        t2.setStyleSheet("font-size:17px; font-weight:900; color:#eaf4ff;")
        t3 = QLabel(
            "Live status from the API — test actions hit real serial / camera endpoints."
        )
        t3.setWordWrap(True)
        t3.setStyleSheet("color:#94a8c6; font-size:11px;")
        col.addWidget(t1)
        col.addWidget(t2)
        col.addWidget(t3)
        hh.addLayout(col, 1)
        self._badge_top = QLabel("ACTION REQUIRED")
        self._badge_top.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge_top.setWordWrap(True)
        self._badge_top.setMinimumHeight(36)
        self._badge_top.setMinimumWidth(140)
        self._badge_top.setStyleSheet(
            "background: rgba(255,176,32,0.12); color:#ffb020; font-weight:900;"
            "padding:8px 12px; border-radius:10px; border:1px solid rgba(255,176,32,0.45);"
            "font-size:11px;"
        )
        hh.addWidget(
            self._badge_top, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )
        root.addWidget(head)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)
        split.setOpaqueResize(True)
        split.setHandleWidth(10)
        split.setMinimumHeight(200)
        split.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        left = QFrame()
        left.setObjectName("ZPanel")
        left.setMinimumWidth(300)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(12, 12, 12, 12)
        ll.setSpacing(10)
        ll.addWidget(self._sec_title("Camera devices"))
        inner_cam = QWidget()
        il = QVBoxLayout(inner_cam)
        il.setContentsMargins(0, 0, 0, 0)
        il.setSpacing(12)
        cam_names = [
            "Machine vision (Larval)",
            "USB camera (Adult top)",
            "USB camera (Adult side)",
        ]
        for name in cam_names:
            il.addWidget(self._device_row(name, "camera"))
        self._pb_cam = QProgressBar()
        self._pb_cam.setRange(0, 100)
        self._pb_cam.setValue(0)
        self._pb_cam.setMinimumHeight(22)
        self._pb_cam.setTextVisible(True)
        il.addWidget(self._progress_group("System ready (cameras)", self._pb_cam))
        il.addStretch(1)
        scroll_cam = self._card_scroll(inner_cam)
        ll.addWidget(scroll_cam, 1)

        right = QFrame()
        right.setObjectName("ZPanel")
        right.setMinimumWidth(300)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(12, 12, 12, 12)
        rl.setSpacing(10)
        rl.addWidget(self._sec_title("Stimulus devices"))
        inner_stim = QWidget()
        ir = QVBoxLayout(inner_stim)
        ir.setContentsMargins(0, 0, 0, 0)
        ir.setSpacing(12)
        stim_specs = (
            ("Light", "light", "Test light"),
            ("Buzzer", "buzzer", "Test sound"),
            ("Vibration", "vibration", "Test vibration"),
            ("Water flow", "water", "Test pump"),
        )
        for label, key, test_label in stim_specs:
            ir.addWidget(self._stimulus_cell(label, key, test_label))
        self._pb_stim = QProgressBar()
        self._pb_stim.setValue(0)
        self._pb_stim.setMinimumHeight(22)
        self._pb_stim.setTextVisible(True)
        ir.addWidget(self._progress_group("System ready (stimuli)", self._pb_stim))
        ir.addStretch(1)
        scroll_stim = self._card_scroll(inner_stim)
        rl.addWidget(scroll_stim, 1)

        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 1)
        split.setSizes([520, 520])
        root.addWidget(split, 1)

        foot = QHBoxLayout()
        foot.setSpacing(12)
        foot.setContentsMargins(0, 2, 0, 0)
        log_wrap = QFrame()
        log_wrap.setObjectName("ZPanel")
        log_wrap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        log_col = QVBoxLayout(log_wrap)
        log_col.setContentsMargins(10, 8, 10, 8)
        log_col.setSpacing(4)
        log_title = QLabel("HARDWARE EVENT LOG")
        log_title.setStyleSheet(
            "color:#94a8c6; font-weight:900; font-size:10px; letter-spacing:0.8px;"
        )
        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setPlaceholderText("No tests yet — use Test buttons above.")
        self._log.setMinimumHeight(56)
        self._log.setMaximumHeight(88)
        self._log.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._log.setMaximumBlockCount(500)
        log_col.addWidget(log_title)
        log_col.addWidget(self._log)
        foot.addWidget(log_wrap, 1)

        cal_col = QVBoxLayout()
        cal_col.setContentsMargins(8, 0, 0, 0)
        cal_col.addStretch(1)
        self._btn_cal = QPushButton("Calibration")
        self._btn_cal.setObjectName("ZBtnAzure")
        self._btn_cal.setIcon(icon(ICONS["sliders"], "#041018", 18))
        self._btn_cal.setMinimumHeight(40)
        self._btn_cal.setMinimumWidth(180)
        self._btn_cal.setCursor(Qt.CursorShape.PointingHandCursor)
        cal_col.addWidget(self._btn_cal, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        foot.addLayout(cal_col, 0)
        root.addLayout(foot)

    def _card_scroll(self, inner: QWidget) -> QScrollArea:
        """Scroll inside each card: vertical for long lists; horizontal if the pane is too narrow."""
        inner.setMinimumWidth(292)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        sc.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        sc.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        sc.setWidget(inner)
        sc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sc.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        sc.viewport().setStyleSheet("background: transparent;")
        return sc

    def _stimulus_cell(self, label: str, key: str, test_caption: str) -> QFrame:
        """One full-width row (like camera rows): scroll the list to see all four devices."""
        rw = QFrame()
        rw.setMinimumHeight(68)
        rw.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        rw.setStyleSheet(
            "QFrame { background:#101a2f; border:1px solid rgba(0,170,255,0.15); border-radius:12px; }"
        )
        h = QHBoxLayout(rw)
        h.setContentsMargins(12, 10, 12, 10)
        h.setSpacing(10)
        cb = QCheckBox()
        cb.setChecked(True)
        h.addWidget(cb, 0, Qt.AlignmentFlag.AlignVCenter)
        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        name = QLabel(label)
        name.setStyleSheet("color:#eaf4ff; font-weight:800; font-size:14px;")
        name.setWordWrap(True)
        hint = QLabel(test_caption)
        hint.setStyleSheet("color:#647a9a; font-weight:600; font-size:11px;")
        hint.setWordWrap(True)
        name_col.addWidget(name)
        name_col.addWidget(hint)
        h.addLayout(name_col, 1)
        st = StatusChip("Offline", tone=ChipTone.DANGER)
        st.setMinimumHeight(36)
        st.setMinimumWidth(88)
        st.setMaximumWidth(138)
        st.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._stim_chips[key] = st
        h.addWidget(st, 0, Qt.AlignmentFlag.AlignVCenter)
        bt = QPushButton("Test  ›")
        bt.setObjectName("ZBtnGhost")
        bt.setToolTip(test_caption)
        bt.setMinimumHeight(38)
        bt.setMinimumWidth(84)
        bt.setMaximumWidth(108)
        bt.setIcon(icon(ICONS["activity"], "#1ea7ff", 14))
        bt.clicked.connect(lambda _=False, k=key: self._hw.test_device(k))
        h.addWidget(bt, 0, Qt.AlignmentFlag.AlignVCenter)
        return rw

    def _progress_group(self, title: str, bar: QProgressBar) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 8, 0, 0)
        v.setSpacing(8)
        lab = QLabel(title)
        lab.setStyleSheet("color:#94a8c6; font-weight:800; font-size:13px;")
        v.addWidget(lab)
        v.addWidget(bar)
        return w

    def _sec_title(self, text: str) -> QLabel:
        t = QLabel(text)
        t.setMinimumHeight(40)
        t.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        t.setStyleSheet(
            "font-size:15px; font-weight:900; letter-spacing:0.3px; color:#eaf4ff;"
            "background-color: rgba(30, 167, 255, 0.1);"
            "border: 1px solid rgba(0, 170, 255, 0.28);"
            "border-radius: 10px; padding: 8px 12px;"
        )
        return t

    def _device_row(self, title: str, bind_key: str) -> QFrame:
        fr = QFrame()
        fr.setMinimumHeight(72)
        fr.setStyleSheet(
            "QFrame { background:#101a2f; border:1px solid rgba(0,170,255,0.15); border-radius:12px; }"
        )
        h = QHBoxLayout(fr)
        h.setContentsMargins(14, 12, 14, 12)
        h.setSpacing(12)
        dot = QLabel("●")
        dot.setFixedWidth(14)
        dot.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        dot.setStyleSheet("color:#ff4d5a; font-size:14px; font-weight:900; padding-top:2px;")
        h.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop)
        name_col = QVBoxLayout()
        name_col.setSpacing(4)
        name = QLabel(title)
        name.setStyleSheet("color:#eaf4ff; font-weight:800; font-size:15px;")
        name.setWordWrap(True)
        sub = QLabel("Not detected")
        sub.setStyleSheet("color:#647a9a; font-weight:600; font-size:12px;")
        name_col.addWidget(name)
        name_col.addWidget(sub)
        h.addLayout(name_col, 1)
        self._cam_subs.append(sub)
        chip = StatusChip("DISCONNECTED", tone=ChipTone.DANGER)
        chip.setMinimumHeight(36)
        chip.setMinimumWidth(88)
        chip.setMaximumWidth(138)
        chip.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        h.addWidget(chip, 0, Qt.AlignmentFlag.AlignVCenter)
        bt = QPushButton("Test  ›")
        bt.setObjectName("ZBtnGhost")
        bt.setMinimumHeight(38)
        bt.setMinimumWidth(84)
        bt.setMaximumWidth(108)
        bt.clicked.connect(lambda _=False, k=bind_key: self._hw.test_device(k))
        h.addWidget(bt, 0, Qt.AlignmentFlag.AlignVCenter)
        self._cam_chips.append(chip)
        return fr

    def _append_log(self, msg: str) -> None:
        self._log.appendPlainText(f"[{datetime.now():%H:%M:%S}] {msg}")

    @staticmethod
    def _device_ok(st: DeviceStatus | None) -> bool:
        if st is None:
            return False
        return st not in (DeviceStatus.DISCONNECTED, DeviceStatus.ERROR)

    def _stim_line(self, key: str) -> tuple[str, ChipTone]:
        d = self._hw.get(key)
        st = d.status if d else DeviceStatus.DISCONNECTED
        if st in (DeviceStatus.DISCONNECTED, DeviceStatus.ERROR):
            return "Offline", ChipTone.DANGER
        if st == DeviceStatus.WARNING:
            return "Idle", ChipTone.WARNING
        return "Online", ChipTone.SUCCESS

    def _sync(self) -> None:
        ready = self._hw.system_ready()
        self._badge_top.setText("READY" if ready else "ACTION REQUIRED")
        self._badge_top.setStyleSheet(
            "background: rgba(0,208,132,0.12); color:#00d084; font-weight:900;"
            "padding:8px 12px; border-radius:10px; border:1px solid rgba(0,208,132,0.45);"
            "font-size:11px;"
            if ready
            else (
                "background: rgba(255,176,32,0.12); color:#ffb020; font-weight:900;"
                "padding:8px 12px; border-radius:10px; border:1px solid rgba(255,176,32,0.45);"
                "font-size:11px;"
            )
        )

        cam = self._hw.get("camera")
        cam_ok = self._device_ok(cam.status if cam else None)
        self._pb_cam.setValue(100 if cam_ok else 0)

        stim_keys = ("light", "buzzer", "vibration", "water")
        stim_ok = sum(
            1 for k in stim_keys if self._device_ok(self._hw.get(k).status if self._hw.get(k) else None)
        )
        self._pb_stim.setValue(int(round(100 * stim_ok / len(stim_keys))))

        for sub in self._cam_subs:
            sub.setText("Detected" if cam_ok else "Not detected")
        for chip in self._cam_chips:
            if cam_ok:
                chip.set_text("CONNECTED")
                chip.set_tone(ChipTone.SUCCESS)
            else:
                chip.set_text("DISCONNECTED")
                chip.set_tone(ChipTone.DANGER)

        for key, chip in self._stim_chips.items():
            text, tone = self._stim_line(key)
            chip.set_text(text)
            chip.set_tone(tone)

