"""Protocol Builder — timeline, stimulus tabs, JSON, summary (reference layout)."""

from __future__ import annotations

from copy import deepcopy

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services.protocol_service import PhaseBlock, ProtocolService, StimulusConfig
from widgets.timeline_widget import TimelineMarker, TimelineModel, TimelineWidget
from widgets.zicons import ICONS, icon


class ProtocolBuilderPage(QWidget):
    def __init__(self, protocols: ProtocolService, parent=None) -> None:
        super().__init__(parent)
        self._proto = protocols
        self._name = QLineEdit()
        self._desc = QTextEdit()
        self._desc.setMaximumHeight(72)
        self._desc.setMinimumHeight(52)
        self._saved = QComboBox()
        self._saved.addItems(["Startle Response", "Light/Dark", "Custom…"])
        self._timeline = TimelineWidget()
        self._timeline.setMinimumHeight(96)
        self._timeline.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._warnings = QLabel("—")
        self._warnings.setWordWrap(True)
        self._warnings.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._json = QTextEdit()
        self._summary_runtime = QLabel("—")

        self._light_on = QCheckBox("ON for this phase")
        self._light_i = QSlider(Qt.Orientation.Horizontal)
        self._light_i.setRange(0, 100)
        self._light_f = QSpinBox()
        self._light_pw = QSpinBox()
        self._light_dur = QSpinBox()
        self._light_del = QSpinBox()
        self._light_rep = QSpinBox()
        for s in (self._light_f, self._light_pw, self._light_dur, self._light_del, self._light_rep):
            s.setMinimumHeight(36)
            s.setMaximumWidth(160)
        self._light_f.setRange(0, 200)
        self._light_pw.setRange(0, 5000)
        self._light_dur.setRange(0, 3600)
        self._light_del.setRange(0, 3600)
        self._light_rep.setRange(1, 999)

        self._build()
        self._wire()
        self._load_from_model()
        self._proto.validation_changed.connect(self._show_warnings)
        self._proto.model_changed.connect(self._on_model_changed)

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        head = QFrame()
        head.setObjectName("ZPanel")
        head.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        hh = QVBoxLayout(head)
        hh.setContentsMargins(14, 12, 14, 12)
        hh.setSpacing(4)
        t = QLabel("Protocol Builder")
        t.setStyleSheet("font-size:18px; font-weight:900; color:#eaf4ff;")
        s = QLabel("Design phases, attach stimuli, validate, and export JSON.")
        s.setStyleSheet("color:#94a8c6; font-size:12px;")
        s.setWordWrap(True)
        hh.addWidget(t)
        hh.addWidget(s)
        root.addWidget(head)

        warn = QFrame()
        warn.setObjectName("ZBannerWarn")
        warn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        wl = QHBoxLayout(warn)
        wl.setContentsMargins(12, 10, 12, 10)
        wx = QLabel("Hardware incomplete — connect Arduino + camera.")
        wx.setWordWrap(True)
        wx.setStyleSheet("color:#ffd79a; font-weight:600; font-size:12px;")
        wl.addWidget(wx)
        root.addWidget(warn)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)
        split.setOpaqueResize(True)
        split.setHandleWidth(8)
        split.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # --- Left: protocol details (scroll) ---
        left = QFrame()
        left.setObjectName("ZPanel")
        left.setMinimumWidth(272)
        inner_left = QWidget()
        ll = QVBoxLayout(inner_left)
        ll.setContentsMargins(12, 12, 12, 12)
        ll.setSpacing(10)
        ll.addWidget(self._pt("Protocol details"))
        lbl_n = QLabel("Name")
        lbl_n.setStyleSheet("color:#94a8c6; font-weight:700; font-size:12px;")
        ll.addWidget(lbl_n)
        self._name.setMinimumHeight(34)
        ll.addWidget(self._name)
        lbl_d = QLabel("Description")
        lbl_d.setStyleSheet("color:#94a8c6; font-weight:700; font-size:12px;")
        ll.addWidget(lbl_d)
        ll.addWidget(self._desc)
        self._btn_save = QPushButton("Save protocol")
        self._btn_save.setObjectName("ZBtnPrimary")
        self._btn_save.setIcon(icon(ICONS["folder_open"], "#041018", 16))
        self._btn_draft = QPushButton("Save as draft")
        self._btn_draft.setObjectName("ZBtnGhost")
        self._btn_dup = QPushButton("Duplicate protocol")
        self._btn_dup.setObjectName("ZBtnOutline")
        self._btn_del = QPushButton("Delete from library")
        self._btn_del.setObjectName("ZBtnDanger")
        self._btn_del.setIcon(icon(ICONS["trash"], "#ff8a93", 14))
        btn_col = QVBoxLayout()
        btn_col.setSpacing(8)
        for b in (self._btn_save, self._btn_draft, self._btn_dup, self._btn_del):
            b.setMinimumHeight(40)
            b.setMinimumWidth(180)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn_col.addWidget(b)
        ll.addLayout(btn_col)
        ll.addSpacing(4)
        ll.addWidget(self._pt("Load saved"))
        self._saved.setMinimumHeight(34)
        ll.addWidget(self._saved)
        ll.addStretch(1)
        left_outer = QVBoxLayout(left)
        left_outer.setContentsMargins(0, 0, 0, 0)
        left_outer.addWidget(self._card_scroll(inner_left, min_w=256))

        # --- Center: timeline + phases (scroll) ---
        inner_c = QWidget()
        cl = QVBoxLayout(inner_c)
        cl.setContentsMargins(12, 12, 12, 12)
        cl.setSpacing(10)
        cl.addWidget(self._pt("Timeline"))
        chips = QHBoxLayout()
        chips.setSpacing(8)
        for lab, fa in (
            ("Light", ICONS["light"]),
            ("Buzzer", ICONS["volume"]),
            ("Vibration", ICONS["zap"]),
            ("Water Flow", ICONS["droplet"]),
        ):
            b = QPushButton(lab)
            b.setObjectName("ZBtnOutline")
            b.setMinimumHeight(36)
            b.setIcon(icon(fa, "#1ea7ff", 14))
            chips.addWidget(b)
        chips.addStretch(1)
        cl.addLayout(chips)
        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        self._b_base = QPushButton("+ Baseline")
        self._b_stim = QPushButton("+ Stimulus")
        self._b_rec = QPushButton("+ Recovery")
        for b in (self._b_base, self._b_stim, self._b_rec):
            b.setObjectName("ZBtnGhost")
            b.setMinimumHeight(36)
            b.setIcon(icon(ICONS["plus"], "#00d4ff", 14))
            add_row.addWidget(b)
        add_row.addStretch(1)
        cl.addLayout(add_row)
        cl.addWidget(self._timeline, 0)
        self._phase_host = QWidget()
        self._phase_lay = QVBoxLayout(self._phase_host)
        self._phase_lay.setSpacing(12)
        self._phase_lay.setContentsMargins(2, 6, 2, 6)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._phase_host)
        scroll.setMinimumHeight(140)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.viewport().setStyleSheet("background: transparent;")
        cl.addWidget(scroll, 1)
        center = QFrame()
        center.setObjectName("ZPanel")
        center.setMinimumWidth(300)
        co = QVBoxLayout(center)
        co.setContentsMargins(0, 0, 0, 0)
        co.addWidget(self._card_scroll(inner_c, min_w=300))

        # --- Stimulus tabs (scroll per tab) ---
        tabs = QTabWidget()
        tabs.setMinimumWidth(260)
        tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        tw = QWidget()
        tvl = QVBoxLayout(tw)
        tvl.setContentsMargins(10, 10, 10, 10)
        tvl.setSpacing(10)
        self._light_on.setMinimumHeight(32)
        tvl.addWidget(self._light_on)
        tvl.addWidget(self._stacked_field("Intensity %", self._light_i))
        for lab, w in (
            ("Frequency (Hz)", self._light_f),
            ("Pulse width (ms)", self._light_pw),
            ("Duration (s)", self._light_dur),
            ("Delay (s)", self._light_del),
            ("Repetitions", self._light_rep),
        ):
            tvl.addWidget(self._stacked_field(lab, w))
        self._btn_apply = QPushButton("Apply to stimulus phase")
        self._btn_apply.setObjectName("ZBtnGhost")
        self._btn_apply.setMinimumHeight(40)
        tvl.addWidget(self._btn_apply)
        tvl.addStretch(1)
        tabs.addTab(self._card_scroll(tw, min_w=248), "Light")
        for title in ("Buzzer", "Vibration", "Water Flow"):
            pw = QWidget()
            pl = QVBoxLayout(pw)
            pl.setContentsMargins(10, 10, 10, 10)
            pl.setSpacing(8)
            ph = QLabel(f"Configure {title} (placeholder).")
            ph.setWordWrap(True)
            ph.setStyleSheet("color:#94a8c6; font-size:12px;")
            pl.addWidget(ph)
            pl.addStretch(1)
            tabs.addTab(self._card_scroll(pw, min_w=240), title)

        # --- Summary (scroll) ---
        sumf = QFrame()
        sumf.setObjectName("ZPanel")
        sumf.setMinimumWidth(236)
        inner_s = QWidget()
        sl = QVBoxLayout(inner_s)
        sl.setContentsMargins(12, 12, 12, 12)
        sl.setSpacing(10)
        sl.addWidget(self._pt("Summary"))
        self._sum_phases = QLabel("—")
        self._sum_phases.setWordWrap(True)
        self._sum_phases.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._sum_phases.setStyleSheet("color:#94a8c6; font-weight:600; font-size:12px;")
        rt_l = QLabel("Total runtime")
        rt_l.setStyleSheet("color:#94a8c6; font-weight:800; font-size:11px;")
        sl.addWidget(rt_l)
        self._summary_runtime.setStyleSheet(
            "font-size:22px; font-weight:900; color:#1ea7ff;"
        )
        sl.addWidget(self._summary_runtime)
        sl.addWidget(self._sum_phases)
        sl.addStretch(1)
        sl.addSpacing(6)
        self._btn_test = QPushButton("Test Run")
        self._btn_test.setObjectName("ZBtnPrimary")
        self._btn_test.setIcon(icon(ICONS["play"], "#041018", 16))
        self._btn_test.setMinimumHeight(40)
        self._btn_sum_save = QPushButton("Save protocol")
        self._btn_sum_save.setObjectName("ZBtnGhost")
        self._btn_sum_save.setMinimumHeight(40)
        sl.addWidget(self._btn_test)
        sl.addWidget(self._btn_sum_save)
        so = QVBoxLayout(sumf)
        so.setContentsMargins(0, 0, 0, 0)
        so.addWidget(self._card_scroll(inner_s, min_w=220))

        split.addWidget(left)
        split.addWidget(center)
        split.addWidget(tabs)
        split.addWidget(sumf)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 2)
        split.setStretchFactor(2, 1)
        split.setStretchFactor(3, 0)
        split.setSizes([250, 500, 280, 220])

        root.addWidget(split, 1)

        foot = QFrame()
        foot.setObjectName("ZPanel")
        foot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        fl = QVBoxLayout(foot)
        fl.setContentsMargins(12, 8, 12, 8)
        fl.setSpacing(5)
        fl.addWidget(self._pt("Validation"))
        self._warnings.setStyleSheet("color:#eaf4ff; font-size:8px;")
        warn_host = QWidget()
        wh = QVBoxLayout(warn_host)
        wh.setContentsMargins(4, 2, 4, 2)
        wh.setSpacing(0)
        wh.addWidget(self._warnings)
        val_scroll = QScrollArea()
        val_scroll.setWidgetResizable(True)
        val_scroll.setFrameShape(QFrame.Shape.NoFrame)
        val_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        val_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        val_scroll.setAlignment(Qt.AlignmentFlag.AlignTop)
        val_scroll.setWidget(warn_host)
        val_scroll.setMinimumHeight(18)
        val_scroll.setMaximumHeight(42)
        val_scroll.setStyleSheet(
            "QScrollArea { border: none; background: #050b18; border-radius: 8px; }"
        )
        fl.addWidget(val_scroll)
        fl.addWidget(self._pt("JSON preview"))
        self._json.setMinimumHeight(72)
        self._json.setMaximumHeight(140)
        self._json.setStyleSheet(
            "QTextEdit { font-size: 11px; font-family: Consolas, 'Cascadia Mono', monospace; }"
        )
        self._json.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        fl.addWidget(self._json)
        row = QHBoxLayout()
        row.setContentsMargins(0, 4, 0, 0)
        self._btn_json = QPushButton("Generate JSON")
        self._btn_json.setObjectName("ZBtnPrimary")
        self._btn_json.setMinimumHeight(32)
        self._btn_json.setMaximumHeight(36)
        self._btn_json.setMaximumWidth(140)
        bf = self._btn_json.font()
        bf.setPointSize(max(9, bf.pointSize() - 1))
        self._btn_json.setFont(bf)
        self._btn_json.setIcon(icon(ICONS["activity"], "#041018", 12))
        row.addStretch(1)
        row.addWidget(self._btn_json)
        fl.addLayout(row)
        root.addWidget(foot, 0)

    def _card_scroll(self, inner: QWidget, *, min_w: int = 260) -> QScrollArea:
        """Scrollable column: splitter resize + inner min width avoids clipped controls."""
        inner.setMinimumWidth(min_w)
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

    def _pt(self, t: str) -> QLabel:
        x = QLabel(t)
        x.setStyleSheet(
            "font-size:11px; font-weight:900; letter-spacing:0.75px; color:#94a8c6;"
        )
        return x

    def _stacked_field(self, label: str, widget: QWidget) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        lab = QLabel(label)
        lab.setStyleSheet("color:#94a8c6; font-weight:700; font-size:12px;")
        v.addWidget(lab)
        v.addWidget(widget)
        return w

    def _wire(self) -> None:
        self._btn_save.clicked.connect(self._save_meta)
        self._btn_draft.clicked.connect(lambda: self._save_meta(draft=True))
        self._btn_dup.clicked.connect(self._proto.duplicate)
        self._btn_del.clicked.connect(lambda: self._proto.set_phases([]))
        self._btn_json.clicked.connect(self._generate_json)
        self._btn_apply.clicked.connect(self._apply_stim)
        self._b_base.clicked.connect(lambda: self._add_phase("Baseline", 10.0))
        self._b_stim.clicked.connect(lambda: self._add_phase("Stimulus", 2.0))
        self._b_rec.clicked.connect(lambda: self._add_phase("Recovery", 30.0))
        self._btn_test.clicked.connect(lambda: None)
        self._btn_sum_save.clicked.connect(self._save_meta)

    def _on_model_changed(self) -> None:
        self._load_from_model()

    def _save_meta(self, draft: bool = False) -> None:
        self._proto.set_meta(self._name.text().strip(), self._desc.toPlainText().strip())
        if draft:
            self._warnings.setText("Draft saved (local placeholder).")

    def _add_phase(self, name: str, dur: float) -> None:
        phases = deepcopy(self._proto.model().phases)
        phases.append(PhaseBlock(name, dur))
        self._proto.set_phases(phases)

    def _apply_stim(self) -> None:
        phases = deepcopy(self._proto.model().phases)
        target = next((p for p in phases if p.name.lower().startswith("stim")), None)
        if target is None:
            target = PhaseBlock("Stimulus", 2.0)
            phases.append(target)
        target.light = StimulusConfig(
            self._light_on.isChecked(),
            int(self._light_i.value()),
            float(self._light_f.value()),
            int(self._light_pw.value()),
            float(self._light_dur.value()),
            float(self._light_del.value()),
            int(self._light_rep.value()),
        )
        self._proto.set_phases(phases)

    def _generate_json(self) -> None:
        self._save_meta()
        self._json.setPlainText(self._proto.to_json())

    def _show_warnings(self, items: list[str]) -> None:
        self._warnings.setText(
            "No validation issues." if not items else "• " + "\n• ".join(items)
        )

    def _load_from_model(self) -> None:
        m = self._proto.model()
        self._name.setText(m.name)
        self._desc.setPlainText(m.description)
        total = sum(p.duration_s for p in m.phases)
        self._summary_runtime.setText(f"{total:.0f}s")
        self._sum_phases.setText(
            " · ".join(f"{p.name} ({p.duration_s:.0f}s)" for p in m.phases) or "—"
        )
        self._rebuild_phase_cards()
        self._refresh_timeline()
        sp = next((p for p in m.phases if p.name.lower().startswith("stim")), None)
        if sp:
            self._light_on.setChecked(sp.light.on)
            self._light_i.setValue(int(sp.light.intensity))
            self._light_f.setValue(int(sp.light.frequency_hz))
            self._light_pw.setValue(int(sp.light.pulse_ms))
            self._light_dur.setValue(int(sp.light.duration_s))
            self._light_del.setValue(int(sp.light.delay_s))
            self._light_rep.setValue(int(sp.light.repeat))

    def _rebuild_phase_cards(self) -> None:
        while self._phase_lay.count():
            it = self._phase_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        m = self._proto.model()
        for i, p in enumerate(m.phases):
            fr = QFrame()
            fr.setObjectName("ZPanel")
            fl = QVBoxLayout(fr)
            fl.setContentsMargins(14, 12, 14, 12)
            fl.setSpacing(8)
            top = QHBoxLayout()
            top.setSpacing(8)
            nm = QLineEdit(p.name)
            nm.setObjectName(f"ph_name_{i}")
            nm.setMinimumHeight(36)
            nm.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            dur = QSpinBox()
            dur.setRange(1, 86400)
            dur.setValue(int(p.duration_s))
            dur.setSuffix(" s")
            dur.setMinimumHeight(36)
            rm = QPushButton("Remove")
            rm.setObjectName("ZBtnDanger")
            rm.setMinimumHeight(32)
            rm.setMaximumWidth(90)
            rm.setIcon(icon(ICONS["trash"], "#ff8a93", 12))
            rm.clicked.connect(lambda _=False, idx=i: self._remove_phase(idx))
            top.addWidget(nm, 1)
            top.addWidget(dur, 0)
            top.addWidget(rm, 0, Qt.AlignmentFlag.AlignRight)
            fl.addLayout(top)
            pb = QProgressBar()
            pb.setRange(0, 100)
            pb.setMinimumHeight(18)
            pb.setValue(min(100, int(p.duration_s * 3)))
            fl.addWidget(pb)
            self._phase_lay.addWidget(fr)

    def _remove_phase(self, idx: int) -> None:
        phases = deepcopy(self._proto.model().phases)
        if 0 <= idx < len(phases):
            phases.pop(idx)
            self._proto.set_phases(phases)

    def _refresh_timeline(self) -> None:
        m = self._proto.model()
        splits = [(p.name, p.duration_s) for p in m.phases]
        total = sum(d for _, d in splits) or 1.0
        stim_idx = next((i for i, p in enumerate(m.phases) if p.name.lower().startswith("stim")), None)
        tracks = {k: [] for k in ("Light", "Buzzer", "Vibration", "Water")}
        t0 = sum(m.phases[i].duration_s for i in range(0, stim_idx)) if stim_idx is not None else 0.0
        t1 = t0 + (m.phases[stim_idx].duration_s if stim_idx is not None else 0.0)
        if stim_idx is not None:
            ph = m.phases[stim_idx]
            if ph.light.on:
                tracks["Light"].append(TimelineMarker(t0, t1, "ON", QColor("#1ea7ff")))
            if ph.buzzer.on:
                tracks["Buzzer"].append(TimelineMarker(t0, t1, "PULSE", QColor("#00d084")))
            if ph.vibration.on:
                tracks["Vibration"].append(TimelineMarker(t0, t1, "DRV", QColor("#ffb020")))
            if ph.water.on:
                tracks["Water"].append(TimelineMarker(t0, t1, "FLOW", QColor("#94a8c6")))
        self._timeline.set_model(TimelineModel(total, splits, tracks))
