"""Refined premium Experiments page with robust responsive layout."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtCore import QDateTime, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QResizeEvent
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QTabBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
    from PyQt6.QtMultimediaWidgets import QVideoWidget
    _HAS_MEDIA = True
except Exception:
    _HAS_MEDIA = False


PALETTE = {
    "main": "#06111F",
    "surface": "#081523",
    "card": "#0D1420",
    "soft": "#102033",
    "border": "#15324D",
    "cyan": "#00C8FF",
    "blue": "#007BFF",
    "primary_blue": "#1DA1FF",
    "purple": "#7C4DFF",
    "text": "#FFFFFF",
    "text_soft": "#CFE8FF",
    "muted": "#8AA6C1",
    "success": "#22C55E",
    "danger": "#FF5D73",
    "warning": "#FACC15",
}


@dataclass
class Recording:
    idx: int
    date: str
    experiment: str
    protocol: str
    status: str = "Ready"


class WarningBanner(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WarningBanner")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        msg = QLabel(
            "Arduino disconnected — connect serial in Settings. No cameras detected — check USB / API camera stack. "
            "Playback uses authenticated media URLs; exports use paths from the API host."
        )
        msg.setObjectName("WarningText")
        msg.setWordWrap(True)
        lay.addWidget(msg)


class RecordingList(QTableWidget):
    recording_selected = pyqtSignal(dict)

    def __init__(self, parent=None) -> None:
        super().__init__(0, 3, parent)
        self._rows: list[Recording] = []
        self.setObjectName("RecordingTable")
        self.setHorizontalHeaderLabels(["#", "DATE", "EXPERIMENT"])
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.setColumnWidth(0, 42)
        self.setColumnWidth(1, 112)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(False)
        self.setWordWrap(False)
        self.verticalHeader().setDefaultSectionSize(38)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.itemSelectionChanged.connect(self._emit_selected)

    def set_rows(self, rows: list[Recording]) -> None:
        self._rows = rows
        self.setRowCount(len(rows))
        for r, rec in enumerate(rows):
            self.setItem(r, 0, QTableWidgetItem(str(rec.idx)))
            self.setItem(r, 1, QTableWidgetItem(rec.date))
            self.setItem(r, 2, QTableWidgetItem(rec.experiment))
        if rows:
            self.selectRow(0)
            self._emit_selected()

    def _emit_selected(self) -> None:
        idx = self.currentRow()
        if 0 <= idx < len(self._rows):
            rec = self._rows[idx]
            self.recording_selected.emit(
                {
                    "id": rec.experiment,
                    "date": rec.date,
                    "protocol": rec.protocol,
                    "status": rec.status,
                    "camera": "USB Camera Top",
                    "fps": "60",
                    "duration": "120s",
                    "path": f"/recordings/{rec.experiment}",
                    "time": "10:14:22",
                }
            )


class RecordingsSidebar(QFrame):
    recording_selected = pyqtSignal(dict)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self._all_rows: list[Recording] = []
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        self.date_filter = QComboBox()
        self.date_filter.addItems(["All dates", "Today", "Last 7 days"])
        self.protocol_filter = QComboBox()
        self.protocol_filter.addItems(["All protocols", "Startle Response", "Custom Assay"])
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search name...")
        lay.addWidget(self.date_filter)
        lay.addWidget(self.protocol_filter)
        lay.addWidget(self.search)

        self.list = RecordingList()
        self.empty = QLabel("No recordings match filters.")
        self.empty.setObjectName("Muted")
        self.empty.hide()
        lay.addWidget(self.list, 1)
        lay.addWidget(self.empty)

        self.list.recording_selected.connect(self.recording_selected.emit)
        self.search.textChanged.connect(self._apply_filters)
        self.protocol_filter.currentTextChanged.connect(self._apply_filters)
        self.date_filter.currentTextChanged.connect(self._apply_filters)

    def set_recordings(self, rows: list[Recording]) -> None:
        self._all_rows = rows
        self._apply_filters()

    def _apply_filters(self) -> None:
        q = self.search.text().strip().lower()
        p = self.protocol_filter.currentText()
        filtered = [
            r
            for r in self._all_rows
            if (not q or q in r.experiment.lower())
            and (p == "All protocols" or r.protocol == p)
        ]
        self.list.set_rows(filtered)
        self.empty.setVisible(len(filtered) == 0)


class PlaybackControls(QWidget):
    replay_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    rewind_clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setRange(0, 120)
        self.seek.setValue(0)
        lay.addWidget(self.seek)
        row = QHBoxLayout()
        row.setSpacing(12)
        row.setContentsMargins(0, 0, 0, 4)
        row.addStretch(1)
        self.btn_replay = QPushButton("Replay")
        self.btn_pause = QPushButton("Pause")
        self.btn_stop = QPushButton("Stop")
        self.btn_rewind = QPushButton("-5s rewind")
        self.btn_next = QPushButton(">")
        for btn in (self.btn_replay, self.btn_pause, self.btn_stop, self.btn_rewind, self.btn_next):
            btn.setObjectName("SecondaryBtn")
            btn.setFixedHeight(36)
            btn.setMinimumWidth(92)
            row.addWidget(btn)
        row.addStretch(1)
        lay.addLayout(row)
        self.btn_replay.clicked.connect(self.replay_clicked.emit)
        self.btn_pause.clicked.connect(self.pause_clicked.emit)
        self.btn_stop.clicked.connect(self.stop_clicked.emit)
        self.btn_rewind.clicked.connect(self.rewind_clicked.emit)


class VideoPreviewWidget(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("VideoPreviewFrame")
        self.setMinimumHeight(360)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().Policy.Expanding)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.placeholder = QLabel("Select a recording")
        self.placeholder.setObjectName("PreviewPlaceholder")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._video_widget = None
        self._player = None
        self._audio = None
        if _HAS_MEDIA:
            self._video_widget = QVideoWidget(self)
            self._video_widget.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
            self._video_widget.hide()
            lay.addWidget(self._video_widget, 1)
            self._player = QMediaPlayer(self)
            self._audio = QAudioOutput(self)
            self._player.setAudioOutput(self._audio)
            self._player.setVideoOutput(self._video_widget)

        lay.addWidget(self.placeholder, 1)

    def set_recording(self, data: dict | None) -> None:
        if not data:
            self.placeholder.setText("Select a recording")
            self.placeholder.show()
            if self._video_widget:
                self._video_widget.hide()
            return
        self.placeholder.setText(f"Recording ready: {data.get('id', 'Selected recording')}")
        self.placeholder.show()
        if self._video_widget:
            self._video_widget.hide()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)


class PlayerCard(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(12)
        self.preview = VideoPreviewWidget()
        lay.addWidget(self.preview, 1)
        self.controls = PlaybackControls()
        lay.addWidget(self.controls)

    def set_recording(self, data: dict | None) -> None:
        self.preview.set_recording(data)


class TimelineCard(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(8)

        self.tabs = QTabBar()
        self.tabs.addTab("TIMELINE")
        self.tabs.addTab("SUMMARY")
        lay.addWidget(self.tabs)

        self.stack = QStackedWidget()
        self.timeline_view = self._build_timeline_view()
        self.summary_view = self._build_summary_view()
        self.stack.addWidget(self.timeline_view)
        self.stack.addWidget(self.summary_view)
        lay.addWidget(self.stack, 1)
        self.tabs.currentChanged.connect(self.stack.setCurrentIndex)

    def _build_timeline_view(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 2)
        lay.setSpacing(10)
        phases_label = QLabel("PHASES")
        phases_label.setObjectName("CardSubtitle")
        lay.addWidget(phases_label)

        phase_row = QHBoxLayout()
        for text, obj in (("BASELINE", "SegBaseline"), ("STIMULUS", "SegStim"), ("RECOVERY", "SegRecovery")):
            seg = QLabel(text)
            seg.setObjectName(obj)
            seg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            seg.setFixedHeight(34)
            phase_row.addWidget(seg)
        lay.addLayout(phase_row)

        rows = QWidget()
        grid = QGridLayout(rows)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        for r, track in enumerate(("Light", "Buzzer", "Vibration", "Water")):
            name = QLabel(track)
            name.setMinimumWidth(78)
            name.setMaximumWidth(78)
            lane = QFrame()
            lane.setObjectName("TrackLane")
            lane.setMinimumHeight(24)
            lane.setMaximumHeight(24)
            grid.addWidget(name, r, 0)
            grid.addWidget(lane, r, 1)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        lay.addWidget(rows)

        axis = QLabel("0s      |      30s      |      60s      |      90s      |      120s")
        axis.setObjectName("Muted")
        note = QLabel(
            "Tracks reflect the active protocol in workspace. Load a protocol on Adult or Protocol Builder to align markers."
        )
        note.setWordWrap(True)
        note.setObjectName("Muted")
        lay.addWidget(axis)
        lay.addWidget(note)
        lay.addStretch(1)
        return w

    def _build_summary_view(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        info = QLabel("Timeline summary view.")
        info.setObjectName("Muted")
        lay.addWidget(info)
        lay.addStretch(1)
        return w


class DetailsPanel(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        self.tabs = QTabBar()
        for t in ("SUMMARY", "METADATA", "PROTOCOL", "EXPORT"):
            self.tabs.addTab(t)
        lay.addWidget(self.tabs)

        self.stack = QStackedWidget()
        self.summary = self._build_summary_tab()
        self.metadata = self._build_metadata_tab()
        self.protocol = self._build_protocol_tab()
        self.export = ExportPanel()
        self.stack.addWidget(self.summary)
        self.stack.addWidget(self.metadata)
        self.stack.addWidget(self.protocol)
        self.stack.addWidget(self.export)
        lay.addWidget(self.stack, 1)
        self.tabs.currentChanged.connect(self.stack.setCurrentIndex)

    def _build_summary_tab(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        for k, v in (
            ("Pulse count", "— (needs run log)"),
            ("Duration", "Use player controls for timing."),
            ("Triggers", "— (needs run log)"),
        ):
            row = QHBoxLayout()
            row.addWidget(QLabel(k))
            row.addStretch(1)
            val = QLabel(v)
            val.setObjectName("Muted")
            row.addWidget(val)
            l.addLayout(row)
        div = QFrame()
        div.setObjectName("Divider")
        div.setFixedHeight(1)
        l.addWidget(div)
        note = QLabel("Files are served from the API recordings root.")
        note.setObjectName("Muted")
        note.setWordWrap(True)
        l.addWidget(note)
        l.addStretch(1)
        return w

    def _build_metadata_tab(self) -> QWidget:
        w = QWidget()
        g = QGridLayout(w)
        g.setContentsMargins(0, 0, 0, 0)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        self._meta_labels: dict[str, QLabel] = {}
        fields = ["Experiment ID", "Date", "Time", "Protocol", "Camera", "FPS", "Duration", "Storage path"]
        for i, f in enumerate(fields):
            g.addWidget(QLabel(f), i, 0)
            val = QLabel("—")
            val.setObjectName("Muted")
            val.setWordWrap(True)
            g.addWidget(val, i, 1)
            self._meta_labels[f] = val
        return w

    def _build_protocol_tab(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        for txt in ("Baseline", "Stimulus", "Recovery", "Total runtime: 120s"):
            label = QLabel(txt)
            label.setObjectName("Muted")
            l.addWidget(label)
        l.addStretch(1)
        return w

    def set_recording(self, data: dict | None) -> None:
        if not data:
            return
        map_data = {
            "Experiment ID": data.get("id", "—"),
            "Date": data.get("date", "—"),
            "Time": data.get("time", "—"),
            "Protocol": data.get("protocol", "—"),
            "Camera": data.get("camera", "—"),
            "FPS": data.get("fps", "—"),
            "Duration": data.get("duration", "—"),
            "Storage path": data.get("path", "—"),
        }
        for key, value in map_data.items():
            if key in self._meta_labels:
                self._meta_labels[key].setText(str(value))


class FooterStatusBar(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("FooterStatusBar")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        self.left = QLabel("System: Disconnected   |   Camera: Idle   |   Chamber: Idle   |   Temperature: —   |   Water flow: —")
        self.left.setObjectName("Muted")
        self.time = QLabel("")
        self.time.setObjectName("Muted")
        lay.addWidget(self.left, 1)
        lay.addWidget(self.time, 0, Qt.AlignmentFlag.AlignRight)


class ExportPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sc.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        root.addWidget(sc)
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        for text in ("Export MP4", "Export CSV", "Export JSON", "Open Folder", "Export All (ZIP)"):
            b = QPushButton(text)
            b.setObjectName("SecondaryBtn")
            b.setFixedHeight(36)
            lay.addWidget(b)
        lay.addStretch(1)
        sc.setWidget(content)


class ExperimentsPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build()
        self._load_sample_data()

    def _build(self) -> None:
        self.setObjectName("ExperimentsPage")
        self.setStyleSheet(self._qss())
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(0)

        self._main_scroll = QScrollArea()
        self._main_scroll.setWidgetResizable(True)
        self._main_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        root.addWidget(self._main_scroll, 1)

        page = QWidget()
        page_lay = QVBoxLayout(page)
        page_lay.setContentsMargins(0, 0, 0, 0)
        page_lay.setSpacing(16)
        self._main_scroll.setWidget(page)

        page_lay.addWidget(WarningBanner())

        header = QFrame()
        header.setObjectName("HeaderCard")
        hh = QHBoxLayout(header)
        hh.setContentsMargins(14, 10, 14, 10)
        left = QVBoxLayout()
        title = QLabel("Experiments")
        title.setObjectName("HeaderTitle")
        sub = QLabel("Review recordings, replay capture, and align stimulus tracks with the protocol in your workspace.")
        sub.setObjectName("HeaderSub")
        sub.setWordWrap(True)
        left.addWidget(title)
        left.addWidget(sub)
        hh.addLayout(left, 1)
        self.refresh_btn = QPushButton("Refresh list")
        self.refresh_btn.setObjectName("PrimaryBtn")
        self.refresh_btn.setFixedHeight(36)
        hh.addWidget(self.refresh_btn, 0, Qt.AlignmentFlag.AlignTop)
        page_lay.addWidget(header)

        workspace = QFrame()
        workspace.setObjectName("WorkspaceSurface")
        ws = QHBoxLayout(workspace)
        ws.setContentsMargins(14, 14, 14, 14)
        ws.setSpacing(16)

        self.left = RecordingsSidebar()
        self.left.setMinimumWidth(300)
        self.left.setMaximumWidth(340)

        center_wrap = QWidget()
        center = QVBoxLayout(center_wrap)
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(16)
        self.player = PlayerCard()
        self.timeline = TimelineCard()
        self.timeline.setMinimumHeight(300)
        center.addWidget(self.player, 1)
        center.addWidget(self.timeline, 1)

        self.right = DetailsPanel()
        self.right.setMinimumWidth(300)
        self.right.setMaximumWidth(340)

        ws.addWidget(self.left, 0)
        ws.addWidget(center_wrap, 1)
        ws.addWidget(self.right, 0)
        ws.setStretch(0, 0)
        ws.setStretch(1, 1)
        ws.setStretch(2, 0)

        page_lay.addWidget(workspace, 1)
        self.footer = FooterStatusBar()
        page_lay.addWidget(self.footer)

        self.left.recording_selected.connect(self.player.set_recording)
        self.left.recording_selected.connect(self.right.set_recording)
        self.refresh_btn.clicked.connect(self._load_sample_data)
        self._clock = QTimer(self)
        self._clock.timeout.connect(self._tick_clock)
        self._clock.start(1000)
        self._tick_clock()

    def _load_sample_data(self) -> None:
        now = datetime.now()
        rows = [
            Recording(1, now.strftime("%Y-%m-%d"), "EXP_2026_0413_01", "Startle Response"),
            Recording(2, now.strftime("%Y-%m-%d"), "EXP_2026_0413_02", "Custom Assay"),
            Recording(3, now.strftime("%Y-%m-%d"), "EXP_2026_0413_03", "Startle Response"),
        ]
        self.left.set_recordings(rows)

    def _tick_clock(self) -> None:
        self.footer.time.setText(QDateTime.currentDateTime().toString("h:mm AP MMM d, yyyy"))

    @staticmethod
    def _qss() -> str:
        return f"""
            QWidget#ExperimentsPage {{
                background: {PALETTE["main"]};
                color: {PALETTE["text"]};
            }}
            QFrame#HeaderCard, QFrame#WorkspaceSurface {{
                background: {PALETTE["surface"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 12px;
            }}
            QLabel#HeaderTitle {{ color: {PALETTE["text"]}; font-size: 28px; font-weight: 800; }}
            QLabel#HeaderSub {{ color: {PALETTE["muted"]}; font-size: 12px; }}
            QFrame#WarningBanner {{
                background: rgba(250, 204, 21, 0.1);
                border: 1px solid rgba(250, 204, 21, 0.45);
                border-radius: 12px;
            }}
            QLabel#WarningText {{ color: #F2DE8A; font-size: 12px; font-weight: 600; }}
            QFrame#Card {{
                background: {PALETTE["card"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 14px;
            }}
            QFrame#Card:hover {{ border-color: rgba(0, 200, 255, 0.75); }}
            QLineEdit, QComboBox {{
                min-height: 34px;
                background: {PALETTE["soft"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 8px;
                color: {PALETTE["text"]};
                padding: 0 10px;
            }}
            QLineEdit:focus, QComboBox:focus {{ border: 1px solid {PALETTE["blue"]}; }}
            QPushButton {{
                border-radius: 10px;
                min-height: 36px;
                padding: 0 12px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton#PrimaryBtn {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {PALETTE["primary_blue"]}, stop:1 {PALETTE["purple"]});
                color: {PALETTE["text"]};
                border: 1px solid rgba(94, 165, 255, 0.8);
            }}
            QPushButton#SecondaryBtn {{
                background: {PALETTE["soft"]};
                color: {PALETTE["text_soft"]};
                border: 1px solid {PALETTE["border"]};
            }}
            QLabel#PreviewPlaceholder {{
                background: {PALETTE["soft"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 10px;
                color: {PALETTE["muted"]};
                font-size: 18px;
                font-weight: 700;
            }}
            QTableWidget#RecordingTable {{
                background: {PALETTE["soft"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 10px;
                gridline-color: transparent;
                color: {PALETTE["text"]};
                selection-background-color: rgba(0, 200, 255, 0.14);
                selection-color: {PALETTE["text"]};
            }}
            QTableWidget#RecordingTable::item {{
                padding: 0 6px;
                border-bottom: 1px solid rgba(21, 50, 77, 0.65);
            }}
            QHeaderView::section {{
                background: transparent;
                color: {PALETTE["muted"]};
                border: none;
                border-bottom: 1px solid {PALETTE["border"]};
                font-weight: 700;
                font-size: 11px;
                padding: 6px;
            }}
            QLabel#CardSubtitle, QLabel#Muted {{
                color: {PALETTE["muted"]};
                font-size: 12px;
                font-weight: 600;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {PALETTE["muted"]};
                padding: 8px 12px;
                margin-right: 8px;
                border-bottom: 2px solid transparent;
                font-weight: 700;
            }}
            QTabBar::tab:selected {{
                color: {PALETTE["text_soft"]};
                border-bottom: 2px solid {PALETTE["cyan"]};
            }}
            QLabel#SegBaseline {{
                background: #1A2D49;
                color: {PALETTE["text_soft"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 8px;
            }}
            QLabel#SegStim {{
                background: rgba(0, 200, 255, 0.18);
                color: {PALETTE["cyan"]};
                border: 1px solid rgba(0, 200, 255, 0.45);
                border-radius: 8px;
            }}
            QLabel#SegRecovery {{
                background: rgba(124, 77, 255, 0.2);
                color: {PALETTE["text_soft"]};
                border: 1px solid rgba(124, 77, 255, 0.5);
                border-radius: 8px;
            }}
            QFrame#TrackLane {{
                background: {PALETTE["soft"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 6px;
            }}
            QSlider::groove:horizontal {{
                background: {PALETTE["border"]};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {PALETTE["primary_blue"]};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {PALETTE["cyan"]};
                border: 1px solid {PALETTE["cyan"]};
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
            QFrame#Divider {{
                background: {PALETTE["border"]};
                border: none;
            }}
            QFrame#FooterStatusBar {{
                background: #071426;
                border-top: 1px solid {PALETTE["border"]};
                border-radius: 0;
            }}
        """
