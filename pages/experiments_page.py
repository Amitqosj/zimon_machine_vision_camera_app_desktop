"""Experiments — history, playback placeholder, export (reference layout)."""

from __future__ import annotations

from datetime import datetime, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from widgets.camera_view import CameraView
from widgets.timeline_widget import TimelineMarker, TimelineModel, TimelineWidget
from widgets.zicons import ICONS, icon


class ExperimentsPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build()

    def _pt(self, t: str) -> QLabel:
        x = QLabel(t)
        x.setStyleSheet(
            "font-size:12px; font-weight:900; letter-spacing:0.85px; color:#94a8c6;"
        )
        return x

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        top = QHBoxLayout()
        ht = QLabel("Experiments")
        ht.setStyleSheet("font-size:24px; font-weight:900; color:#eaf4ff;")
        ht.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        top.addWidget(ht)
        top.addStretch(1)
        self._btn_refresh = QPushButton("  Refresh list  ")
        self._btn_refresh.setObjectName("ZBtnGhost")
        self._btn_refresh.setMinimumHeight(42)
        self._btn_refresh.setIcon(icon(ICONS["refresh"], "#1ea7ff", 16))
        top.addWidget(self._btn_refresh)
        root.addLayout(top)

        warn = QFrame()
        warn.setObjectName("ZBannerWarn")
        warn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        wl = QHBoxLayout(warn)
        wl.setContentsMargins(16, 14, 16, 14)
        wz = QLabel(
            "Arduino disconnected — playback uses authenticated media URLs."
        )
        wz.setWordWrap(True)
        wz.setStyleSheet("color:#ffd79a; font-weight:600;")
        wl.addWidget(wz)
        root.addWidget(warn)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)
        split.setOpaqueResize(True)
        split.setHandleWidth(8)
        split.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        left = QFrame()
        left.setObjectName("ZPanel")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(16, 16, 16, 16)
        ll.setSpacing(12)
        ll.addWidget(self._pt("Filters"))
        self._date_f = QComboBox()
        self._date_f.addItems(["Last 7 days", "Last 30 days", "All time"])
        self._date_f.setMinimumHeight(36)
        self._proto_f = QComboBox()
        self._proto_f.addItems(["(All protocols)", "Startle Response", "Light/Dark"])
        self._proto_f.setMinimumHeight(36)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search…")
        self._search.setMinimumHeight(36)
        ll.addWidget(self._date_f)
        ll.addWidget(self._proto_f)
        ll.addWidget(self._search)
        ll.addSpacing(4)
        ll.addWidget(self._pt("Recordings"))
        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Date", "Experiment"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setDefaultSectionSize(48)
        self._table.setShowGrid(False)
        ll.addWidget(self._table, 1)
        empty = QLabel("No recordings match filters.")
        empty.setStyleSheet("color:#647a9a; font-style:italic;")
        empty.hide()
        self._empty = empty
        ll.addWidget(empty)
        self._fill_table()
        left.setMinimumWidth(300)
        left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        center = QWidget()
        center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cl = QVBoxLayout(center)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(14)
        self._viewer = CameraView()
        self._viewer.set_status_text("Select a recording")
        self._viewer.setMinimumHeight(280)
        cl.addWidget(self._viewer, 1)
        ctl = QHBoxLayout()
        ctl.setSpacing(10)
        ctl.setContentsMargins(0, 8, 0, 0)
        for lab, fa in (
            ("Replay", ICONS["replay"]),
            ("Pause", ICONS["pause"]),
            ("Stop", ICONS["stop"]),
            ("-5s", ICONS["back"]),
        ):
            b = QPushButton(lab)
            b.setObjectName("ZBtnOutline" if lab != "Replay" else "ZBtnPrimary")
            b.setMinimumHeight(44)
            b.setMinimumWidth(88)
            b.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            b.setIcon(icon(fa, "#eaf4ff" if lab != "Replay" else "#041018", 14))
            ctl.addWidget(b)
        ctl.addStretch(1)
        cl.addLayout(ctl)
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tw = QWidget()
        tl = QVBoxLayout(tw)
        tl.setContentsMargins(8, 8, 8, 8)
        tl.setSpacing(8)
        self._ev_timeline = TimelineWidget()
        self._ev_timeline.setMinimumHeight(160)
        total = 120.0
        splits = [("Baseline", 40.0), ("Stimulus", 40.0), ("Recovery", 40.0)]
        tracks = {
            "Light": [TimelineMarker(40, 45, "ON", QColor("#1ea7ff"))],
            "Buzzer": [TimelineMarker(41, 42, "FLASH", QColor("#00d084"))],
            "Vibration": [TimelineMarker(40, 50, "5", QColor("#ffb020"))],
            "Water": [],
        }
        self._ev_timeline.set_model(TimelineModel(total, splits, tracks))
        tl.addWidget(self._ev_timeline)
        tabs.addTab(tw, "Timeline")
        sumw = QWidget()
        sl = QVBoxLayout(sumw)
        sl.setContentsMargins(8, 8, 8, 8)
        sm = QLabel("Summary metrics (placeholder).")
        sm.setWordWrap(True)
        sm.setStyleSheet("color:#94a8c6; font-size:14px;")
        sl.addWidget(sm)
        sl.addStretch(1)
        tabs.addTab(sumw, "Summary")
        cl.addWidget(tabs)
        center.setMinimumWidth(420)

        right = QFrame()
        right.setObjectName("ZPanel")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(16, 16, 16, 16)
        rl.setSpacing(10)
        rt = QTabWidget()
        rt.setDocumentMode(True)
        rt.addTab(self._kv_tab([("Pulse count", "128"), ("Duration", "02:00"), ("Triggers", "42"), ("Notes", "—")]), "Summary")
        rt.addTab(
            self._kv_tab(
                [
                    ("Experiment ID", "EXP_2026_0406_03"),
                    ("Camera", "USB TOP"),
                    ("Start", "2026-04-06 10:12"),
                    ("End", "2026-04-06 10:14"),
                    ("Folder", "D:/ZIMON/recordings/…"),
                ]
            ),
            "Metadata",
        )
        rt.addTab(self._kv_tab([("Protocol", "Startle Response"), ("Phases", "3")]), "Protocol")
        exp = QWidget()
        ev = QVBoxLayout(exp)
        ev.setContentsMargins(8, 8, 8, 8)
        ev.setSpacing(10)
        for t, tip in (
            ("Export CSV", "Metrics"),
            ("Export Logs", "Hardware logs"),
            ("Export Video", "Video file"),
            ("Export ZIP", "Full bundle"),
        ):
            b = QPushButton(t + "  ›")
            b.setObjectName("ZBtnGhost")
            b.setMinimumHeight(42)
            b.setToolTip(tip)
            ev.addWidget(b)
        ev.addStretch(1)
        rt.addTab(exp, "Export")
        rl.addWidget(rt, 1)
        right.setMinimumWidth(320)
        right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        split.addWidget(left)
        split.addWidget(center)
        split.addWidget(right)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setStretchFactor(2, 0)
        split.setSizes([320, 900, 340])
        root.addWidget(split, 1)

    def _kv_tab(self, rows: list[tuple[str, str]]) -> QWidget:
        w = QWidget()
        g = QGridLayout(w)
        g.setContentsMargins(12, 12, 12, 12)
        g.setHorizontalSpacing(14)
        g.setVerticalSpacing(12)
        for i, (k, v) in enumerate(rows):
            kl = QLabel(k)
            kl.setStyleSheet("color:#94a8c6; font-weight:700; font-size:13px;")
            g.addWidget(kl, i, 0, Qt.AlignmentFlag.AlignTop)
            vl = QLabel(v)
            vl.setWordWrap(True)
            vl.setStyleSheet("color:#eaf4ff; font-weight:700; font-size:13px;")
            g.addWidget(vl, i, 1, Qt.AlignmentFlag.AlignTop)
        return w

    def _fill_table(self) -> None:
        base = datetime(2026, 4, 6, 10, 12)
        rows = [
            (base, "EXP_2026_0406_03"),
            (base - timedelta(days=1), "EXP_2026_0405_11"),
        ]
        self._table.setRowCount(len(rows))
        for r, (dt, eid) in enumerate(rows):
            self._table.setItem(r, 0, QTableWidgetItem(dt.strftime("%Y-%m-%d %H:%M")))
            self._table.setItem(r, 1, QTableWidgetItem(eid))
        self._empty.setVisible(len(rows) == 0)
