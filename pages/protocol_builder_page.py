"""Premium dark-neon Protocol Builder page."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
import uuid

from PyQt6.QtCore import QDateTime, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services.protocol_service import PhaseBlock, ProtocolService, StimulusConfig


PALETTE = {
    "main": "#06111F",
    "surface": "#081523",
    "card": "#0D1420",
    "soft": "#102033",
    "border": "#15324D",
    "cyan": "#00C8FF",
    "blue": "#007BFF",
    "purple": "#7C4DFF",
    "primary_blue": "#1DA1FF",
    "text": "#FFFFFF",
    "text_soft": "#CFE8FF",
    "muted": "#8AA6C1",
    "success": "#22C55E",
    "danger": "#FF5D73",
    "warning": "#FACC15",
}

STIM_KEYS = {"Light": "light", "Buzzer": "buzzer", "Vibration": "vibration", "Water Flow": "water"}


class WarningBanner(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WarningBanner")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(5)
        title = QLabel("Hardware incomplete — connect Arduino + camera for full operation.")
        title.setObjectName("WarningTitle")
        detail = QLabel(
            "Arduino disconnected — connect serial in Settings. No cameras detected — check USB / API camera stack."
        )
        detail.setObjectName("WarningSub")
        detail.setWordWrap(True)
        lay.addWidget(title)
        lay.addWidget(detail)


class ProtocolDetailsCard(QFrame):
    save_protocol = pyqtSignal()
    save_draft = pyqtSignal()
    duplicate_protocol = pyqtSignal()
    delete_protocol = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ProtocolCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        cap = QLabel("PROTOCOL DETAILS")
        cap.setObjectName("CardTitle")
        lay.addWidget(cap)

        self.name_edit = QLineEdit("Untitled protocol")
        self.desc_edit = QTextEdit()
        self.desc_edit.setMinimumHeight(88)
        self.desc_edit.setPlaceholderText("Description...")
        self.library_combo = QComboBox()
        self.library_combo.addItem("Select...")
        self.refresh_link = QPushButton("Refresh library list")
        self.refresh_link.setObjectName("LinkBtn")

        lay.addWidget(QLabel("Name"))
        lay.addWidget(self.name_edit)
        lay.addWidget(QLabel("Description"))
        lay.addWidget(self.desc_edit)

        self.btn_save = QPushButton("Save protocol")
        self.btn_save.setObjectName("PrimaryBtn")
        self.btn_draft = QPushButton("Save as draft")
        self.btn_draft.setObjectName("SecondaryBtn")
        self.btn_duplicate = QPushButton("Duplicate protocol")
        self.btn_duplicate.setObjectName("SecondaryBtn")
        self.btn_delete = QPushButton("Delete from library")
        self.btn_delete.setObjectName("DangerOutlineBtn")
        for btn in (self.btn_save, self.btn_draft, self.btn_duplicate, self.btn_delete):
            btn.setFixedHeight(38)
            lay.addWidget(btn)

        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFixedHeight(1)
        lay.addWidget(divider)

        load_title = QLabel("LOAD SAVED")
        load_title.setObjectName("CardSubtitle")
        lay.addWidget(load_title)
        lay.addWidget(self.library_combo)
        lay.addWidget(self.refresh_link, 0, Qt.AlignmentFlag.AlignLeft)
        lay.addStretch(1)

        self.btn_save.clicked.connect(self.save_protocol.emit)
        self.btn_draft.clicked.connect(self.save_draft.emit)
        self.btn_duplicate.clicked.connect(self.duplicate_protocol.emit)
        self.btn_delete.clicked.connect(self.delete_protocol.emit)


class PhaseCard(QFrame):
    changed = pyqtSignal(int, str, int)
    remove_requested = pyqtSignal(int)
    selected = pyqtSignal(int)

    def __init__(self, index: int, name: str, duration: int, color: str, parent=None) -> None:
        super().__init__(parent)
        self.index = index
        self.setObjectName("PhaseCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        top = QHBoxLayout()
        title = QLabel(f"{index + 1}. {name}")
        title.setObjectName("PhaseTitle")
        badge = QLabel(f"{duration}s")
        badge.setObjectName("DurationBadge")
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(badge)
        lay.addLayout(top)

        self.progress = QFrame()
        self.progress.setObjectName("PhaseProgress")
        self.progress.setProperty("barColor", color)
        self.progress.setFixedHeight(8)
        lay.addWidget(self.progress)

        row = QGridLayout()
        row.setHorizontalSpacing(8)
        row.setVerticalSpacing(8)
        self.duration_edit = QLineEdit(str(duration))
        self.label_edit = QLineEdit(name)
        remove_btn = QPushButton("Remove")
        remove_btn.setObjectName("LinkBtn")
        row.addWidget(QLabel("Duration(s)"), 0, 0)
        row.addWidget(self.duration_edit, 0, 1)
        row.addWidget(QLabel("Label"), 1, 0)
        row.addWidget(self.label_edit, 1, 1)
        row.addWidget(remove_btn, 2, 1, 1, 1, Qt.AlignmentFlag.AlignRight)
        lay.addLayout(row)

        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.index))
        self.duration_edit.editingFinished.connect(self._emit_change)
        self.label_edit.editingFinished.connect(self._emit_change)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self.selected.emit(self.index)
        return super().mousePressEvent(event)

    def _emit_change(self) -> None:
        try:
            duration = max(1, int(self.duration_edit.text().strip()))
        except ValueError:
            duration = 1
            self.duration_edit.setText("1")
        label = self.label_edit.text().strip() or f"Phase {self.index + 1}"
        self.changed.emit(self.index, label, duration)


class TimelineCard(QFrame):
    add_phase = pyqtSignal(str, int)
    phase_changed = pyqtSignal(int, str, int)
    phase_removed = pyqtSignal(int)
    phase_selected = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ProtocolCard")
        self._phase_layout = QVBoxLayout()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        cap = QLabel("TIMELINE")
        cap.setObjectName("CardTitle")
        lay.addWidget(cap)

        add_label = QLabel("ADD HARDWARE STEP")
        add_label.setObjectName("CardSubtitle")
        lay.addWidget(add_label)

        chips = QHBoxLayout()
        for label in ("Light", "Buzzer", "Vibration", "Water flow"):
            btn = QPushButton(label)
            btn.setObjectName("ChipBtn")
            btn.setFixedHeight(32)
            chips.addWidget(btn)
        lay.addLayout(chips)

        phase_btns = QHBoxLayout()
        for label, default_dur in (("+ Baseline", 120), ("+ Stimulus", 60), ("+ Recovery", 120)):
            btn = QPushButton(label)
            btn.setObjectName("SecondaryBtn")
            btn.setFixedHeight(34)
            btn.clicked.connect(lambda _=False, l=label, d=default_dur: self._add_from_label(l, d))
            phase_btns.addWidget(btn)
        lay.addLayout(phase_btns)

        self.phase_wrap = QWidget()
        self.phase_wrap.setLayout(self._phase_layout)
        self._phase_layout.setContentsMargins(0, 0, 0, 0)
        self._phase_layout.setSpacing(10)
        lay.addWidget(self.phase_wrap)
        lay.addStretch(1)

    def _add_from_label(self, label: str, duration: int) -> None:
        self.add_phase.emit(label.replace("+ ", ""), duration)

    def set_phases(self, phases: list[PhaseBlock]) -> None:
        while self._phase_layout.count():
            item = self._phase_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        colors = ("#8AA6C1", PALETTE["primary_blue"], PALETTE["purple"])
        for idx, phase in enumerate(phases):
            card = PhaseCard(idx, phase.name, int(phase.duration_s), colors[idx % len(colors)])
            card.changed.connect(self.phase_changed.emit)
            card.remove_requested.connect(self.phase_removed.emit)
            card.selected.connect(self.phase_selected.emit)
            self._phase_layout.addWidget(card)
        self._phase_layout.addStretch(1)


class StimulusEditorCard(QFrame):
    stimulus_changed = pyqtSignal(dict)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._stim_key = "light"
        self.setObjectName("ProtocolCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        cap = QLabel("STIMULUS (SELECTED PHASE)")
        cap.setObjectName("CardTitle")
        lay.addWidget(cap)

        chips = QHBoxLayout()
        self._chip_buttons: dict[str, QPushButton] = {}
        for name in ("Light", "Buzzer", "Vibration", "Water Flow"):
            btn = QPushButton(name)
            btn.setObjectName("ChipBtn")
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda _=False, n=name: self._set_chip(n))
            chips.addWidget(btn)
            self._chip_buttons[name] = btn
        lay.addLayout(chips)
        self._set_chip("Light")

        self.on_check = QCheckBox("ON for this phase")
        lay.addWidget(self.on_check)

        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(0, 100)
        self.freq_edit = QLineEdit()
        self.pulse_edit = QLineEdit()
        self.duration_edit = QLineEdit()
        self.delay_edit = QLineEdit()
        self.reps_edit = QLineEdit()
        for edit in (self.freq_edit, self.pulse_edit, self.duration_edit, self.delay_edit, self.reps_edit):
            edit.setPlaceholderText("0")

        form = QGridLayout()
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(8)
        form.addWidget(QLabel("Intensity (0-100)"), 0, 0)
        form.addWidget(self.intensity_slider, 0, 1)
        form.addWidget(QLabel("Frequency (Hz)"), 1, 0)
        form.addWidget(self.freq_edit, 1, 1)
        form.addWidget(QLabel("Pulse width (ms)"), 2, 0)
        form.addWidget(self.pulse_edit, 2, 1)
        form.addWidget(QLabel("Duration (ms)"), 3, 0)
        form.addWidget(self.duration_edit, 3, 1)
        form.addWidget(QLabel("Delay (ms)"), 4, 0)
        form.addWidget(self.delay_edit, 4, 1)
        form.addWidget(QLabel("Repetitions"), 5, 0)
        form.addWidget(self.reps_edit, 5, 1)
        lay.addLayout(form)

        apply_btn = QPushButton("Apply stimulus settings")
        apply_btn.setObjectName("PrimaryBtn")
        apply_btn.setFixedHeight(38)
        apply_btn.clicked.connect(self._emit_update)
        lay.addWidget(apply_btn)
        lay.addStretch(1)

    def _set_chip(self, chip_name: str) -> None:
        for name, btn in self._chip_buttons.items():
            btn.setChecked(name == chip_name)
        self._stim_key = STIM_KEYS[chip_name]

    def _emit_update(self) -> None:
        payload = {
            "stim_key": self._stim_key,
            "on": self.on_check.isChecked(),
            "intensity": self.intensity_slider.value(),
            "frequency_hz": self._as_float(self.freq_edit.text()),
            "pulse_ms": self._as_int(self.pulse_edit.text()),
            "duration_s": self._as_float(self.duration_edit.text()) / 1000.0,
            "delay_s": self._as_float(self.delay_edit.text()) / 1000.0,
            "repeat": max(1, self._as_int(self.reps_edit.text(), default=1)),
        }
        self.stimulus_changed.emit(payload)

    def load_stimulus(self, config: StimulusConfig) -> None:
        self.on_check.setChecked(config.on)
        self.intensity_slider.setValue(int(config.intensity))
        self.freq_edit.setText(str(config.frequency_hz))
        self.pulse_edit.setText(str(config.pulse_ms))
        self.duration_edit.setText(str(int(config.duration_s * 1000)))
        self.delay_edit.setText(str(int(config.delay_s * 1000)))
        self.reps_edit.setText(str(config.repeat))

    @staticmethod
    def _as_int(text: str, default: int = 0) -> int:
        try:
            return int(float(text.strip()))
        except ValueError:
            return default

    @staticmethod
    def _as_float(text: str) -> float:
        try:
            return float(text.strip())
        except ValueError:
            return 0.0


class SummaryCard(QFrame):
    test_run_requested = pyqtSignal()
    save_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ProtocolCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(8)
        title = QLabel("PROTOCOL SUMMARY")
        title.setObjectName("CardTitle")
        lay.addWidget(title)
        self.runtime = QLabel("0s")
        self.runtime.setObjectName("RuntimeTotal")
        self.runtime_caption = QLabel("Total runtime")
        self.runtime_caption.setObjectName("Muted")
        self.phase_lines = QLabel("—")
        self.phase_lines.setObjectName("Muted")
        self.phase_lines.setWordWrap(True)
        lay.addWidget(self.runtime)
        lay.addWidget(self.runtime_caption)
        lay.addWidget(self.phase_lines)
        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFixedHeight(1)
        lay.addWidget(divider)
        self.test_btn = QPushButton("Test run")
        self.test_btn.setObjectName("SecondaryBtn")
        self.test_btn.setFixedHeight(38)
        self.save_btn = QPushButton("Save protocol")
        self.save_btn.setObjectName("PrimaryBtn")
        self.save_btn.setFixedHeight(38)
        lay.addWidget(self.test_btn)
        lay.addWidget(self.save_btn)
        lay.addStretch(1)
        self.test_btn.clicked.connect(self.test_run_requested.emit)
        self.save_btn.clicked.connect(self.save_requested.emit)


class ValidationOutputCard(QFrame):
    generate_json_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ProtocolCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)
        title = QLabel("VALIDATION & OUTPUT")
        title.setObjectName("CardTitle")
        self.status = QLabel("No blocking issues detected.")
        self.status.setObjectName("SuccessText")
        self.json_preview = QTextEdit()
        self.json_preview.setReadOnly(True)
        self.json_preview.setMinimumHeight(220)
        self.json_preview.setObjectName("JsonPreview")
        generate_btn = QPushButton("Generate protocol JSON (download)")
        generate_btn.setObjectName("PrimaryBtn")
        generate_btn.setFixedHeight(38)
        generate_btn.clicked.connect(self.generate_json_requested.emit)
        lay.addWidget(title)
        lay.addWidget(self.status)
        lay.addWidget(self.json_preview)
        lay.addWidget(generate_btn, 0, Qt.AlignmentFlag.AlignLeft)


class FooterStatusBar(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("FooterStatusBar")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(5)
        hint = QLabel(
            'For "Custom Assay": set RGB to ~80% intensity, 60 FPS, and ~20 min duration when chamber allows it.'
        )
        hint.setObjectName("Muted")
        warn = QLabel(
            "Arduino disconnected — connect serial in Settings. No cameras detected — check USB / API camera stack."
        )
        warn.setObjectName("WarningText")
        row = QHBoxLayout()
        self.left = QLabel("System: Disconnected   |   Camera: Idle   |   Chamber: Idle   |   Temperature: —   |   Water flow: —")
        self.left.setObjectName("Muted")
        self.time = QLabel("")
        self.time.setObjectName("Muted")
        row.addWidget(self.left, 1)
        row.addWidget(self.time, 0, Qt.AlignmentFlag.AlignRight)
        lay.addWidget(hint)
        lay.addWidget(warn)
        lay.addLayout(row)


class ProtocolBuilderPage(QWidget):
    def __init__(self, protocols: ProtocolService, parent=None) -> None:
        super().__init__(parent)
        self._proto = protocols
        self._selected_phase_idx = 0
        self._hardware_ready = False

        self._details = ProtocolDetailsCard()
        self._timeline = TimelineCard()
        self._stimulus = StimulusEditorCard()
        self._summary = SummaryCard()
        self._validation = ValidationOutputCard()
        self._footer = FooterStatusBar()

        self._build_ui()
        self._wire()
        self._refresh_from_model()
        self._proto.validation_changed.connect(self._on_validation)
        self._proto.model_changed.connect(self._refresh_from_model)

    def _build_ui(self) -> None:
        self.setObjectName("ProtocolBuilderPage")
        self.setStyleSheet(self._qss())
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 8)
        root.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        root.addWidget(scroll, 1)

        content = QWidget()
        body = QVBoxLayout(content)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(10)

        header = QFrame()
        header.setObjectName("HeaderCard")
        hh = QHBoxLayout(header)
        hh.setContentsMargins(14, 10, 14, 10)
        left = QVBoxLayout()
        title = QLabel("Protocol Builder")
        title.setObjectName("HeaderTitle")
        sub = QLabel("Design phases, attach stimuli, validate, and export JSON.")
        sub.setObjectName("HeaderSub")
        left.addWidget(title)
        left.addWidget(sub)
        hh.addLayout(left, 1)
        adult_btn = QPushButton("← Adult module")
        adult_btn.setObjectName("LinkBtn")
        adult_btn.setFixedHeight(32)
        hh.addWidget(adult_btn, 0, Qt.AlignmentFlag.AlignTop)
        body.addWidget(header)

        body.addWidget(WarningBanner())

        grid_wrap = QFrame()
        grid_wrap.setObjectName("PageSurface")
        grid = QGridLayout(grid_wrap)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(0)
        grid.addWidget(self._details, 0, 0)
        grid.addWidget(self._timeline, 0, 1)
        grid.addWidget(self._stimulus, 0, 2)
        grid.addWidget(self._summary, 0, 3)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(2, 2)
        grid.setColumnStretch(3, 2)
        body.addWidget(grid_wrap)
        body.addWidget(self._validation)
        scroll.setWidget(content)

        root.addWidget(self._footer)
        self._clock = QTimer(self)
        self._clock.timeout.connect(self._tick_clock)
        self._clock.start(1000)
        self._tick_clock()

    def _wire(self) -> None:
        self._details.save_protocol.connect(self._save_meta)
        self._details.save_draft.connect(lambda: self._save_meta(draft=True))
        self._details.duplicate_protocol.connect(self._proto.duplicate)
        self._details.delete_protocol.connect(lambda: self._proto.set_phases([]))
        self._details.refresh_link.clicked.connect(self._refresh_library_list)
        self._timeline.add_phase.connect(self._add_phase)
        self._timeline.phase_changed.connect(self._update_phase)
        self._timeline.phase_removed.connect(self._remove_phase)
        self._timeline.phase_selected.connect(self._select_phase)
        self._stimulus.stimulus_changed.connect(self._apply_stimulus)
        self._summary.save_requested.connect(self._save_meta)
        self._summary.test_run_requested.connect(self._test_run)
        self._validation.generate_json_requested.connect(self._download_json)

    def _save_meta(self, draft: bool = False) -> None:
        self._proto.set_meta(self._details.name_edit.text().strip(), self._details.desc_edit.toPlainText().strip())
        if draft:
            self._validation.status.setObjectName("WarningText")
            self._validation.status.setText("Draft saved locally.")
            self._validation.status.style().unpolish(self._validation.status)
            self._validation.status.style().polish(self._validation.status)

    def _refresh_library_list(self) -> None:
        self._details.library_combo.clear()
        self._details.library_combo.addItems(["Select...", "Startle Response", "Light/Dark", "Custom Assay"])

    def _add_phase(self, name: str, duration: int) -> None:
        phases = deepcopy(self._proto.model().phases)
        phases.append(PhaseBlock(name, float(duration)))
        self._proto.set_phases(phases)
        self._selected_phase_idx = len(phases) - 1

    def _update_phase(self, idx: int, label: str, duration: int) -> None:
        phases = deepcopy(self._proto.model().phases)
        if 0 <= idx < len(phases):
            phases[idx].name = label
            phases[idx].duration_s = float(duration)
            self._proto.set_phases(phases)

    def _remove_phase(self, idx: int) -> None:
        phases = deepcopy(self._proto.model().phases)
        if 0 <= idx < len(phases):
            phases.pop(idx)
            self._selected_phase_idx = max(0, min(self._selected_phase_idx, len(phases) - 1))
            self._proto.set_phases(phases)

    def _select_phase(self, idx: int) -> None:
        self._selected_phase_idx = idx
        self._load_selected_phase_stimulus()

    def _apply_stimulus(self, payload: dict) -> None:
        phases = deepcopy(self._proto.model().phases)
        if not phases:
            return
        idx = max(0, min(self._selected_phase_idx, len(phases) - 1))
        phase = phases[idx]
        config = StimulusConfig(
            on=payload["on"],
            intensity=payload["intensity"],
            frequency_hz=payload["frequency_hz"],
            pulse_ms=payload["pulse_ms"],
            duration_s=payload["duration_s"],
            delay_s=payload["delay_s"],
            repeat=payload["repeat"],
        )
        setattr(phase, payload["stim_key"], config)
        self._proto.set_phases(phases)

    def _test_run(self) -> None:
        if not self._hardware_ready:
            QMessageBox.information(self, "Test run", "Test run is disabled until hardware is connected.")
            return
        QMessageBox.information(self, "Test run", "Protocol test run started.")

    def _on_validation(self, items: list[str]) -> None:
        if items:
            self._validation.status.setObjectName("WarningText")
            self._validation.status.setText(" ; ".join(items))
        else:
            self._validation.status.setObjectName("SuccessText")
            self._validation.status.setText("No blocking issues detected.")
        self._validation.status.style().unpolish(self._validation.status)
        self._validation.status.style().polish(self._validation.status)

    def _build_preview_json(self) -> str:
        model = self._proto.model()
        payload = {
            "id": str(uuid.uuid4()),
            "name": model.name,
            "description": model.description,
            "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "phases": json.loads(self._proto.to_json()).get("phases", []),
        }
        return json.dumps(payload, indent=2)

    def _download_json(self) -> None:
        self._save_meta()
        text = self._build_preview_json()
        self._validation.json_preview.setPlainText(text)
        default_name = f"{self._proto.model().name.strip().replace(' ', '_') or 'protocol'}.json"
        out_path, _ = QFileDialog.getSaveFileName(self, "Save protocol JSON", default_name, "JSON Files (*.json)")
        if not out_path:
            return
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        QMessageBox.information(self, "Export complete", f"Protocol JSON saved to:\n{out_path}")

    def _refresh_from_model(self) -> None:
        model = self._proto.model()
        self._details.name_edit.setText(model.name or "Untitled protocol")
        self._details.desc_edit.setPlainText(model.description or "")
        self._timeline.set_phases(model.phases)
        self._summary.runtime.setText(f"{int(sum(p.duration_s for p in model.phases))}s")
        self._summary.phase_lines.setText(
            "\n".join(f"{i + 1}. {p.name} ........ {int(p.duration_s)}s" for i, p in enumerate(model.phases)) or "—"
        )
        self._summary.test_btn.setEnabled(self._hardware_ready)
        self._validation.json_preview.setPlainText(self._build_preview_json())
        self._load_selected_phase_stimulus()

    def _load_selected_phase_stimulus(self) -> None:
        phases = self._proto.model().phases
        if not phases:
            return
        idx = max(0, min(self._selected_phase_idx, len(phases) - 1))
        self._selected_phase_idx = idx
        self._stimulus.load_stimulus(phases[idx].light)

    def _tick_clock(self) -> None:
        self._footer.time.setText(QDateTime.currentDateTime().toString("h:mm AP MMM d, yyyy"))

    @staticmethod
    def _qss() -> str:
        return f"""
            QWidget#ProtocolBuilderPage {{
                background: {PALETTE["main"]};
                color: {PALETTE["text"]};
            }}
            QFrame#HeaderCard, QFrame#PageSurface {{
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
            QLabel#WarningTitle {{ color: {PALETTE["warning"]}; font-size: 13px; font-weight: 700; }}
            QLabel#WarningSub {{ color: #EFDFA2; font-size: 12px; }}
            QFrame#ProtocolCard {{
                background: {PALETTE["card"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 14px;
            }}
            QFrame#ProtocolCard:hover {{ border-color: rgba(0, 200, 255, 0.7); }}
            QLabel#CardTitle {{ color: {PALETTE["text_soft"]}; font-size: 12px; font-weight: 800; letter-spacing: 1px; }}
            QLabel#CardSubtitle {{ color: {PALETTE["muted"]}; font-size: 11px; font-weight: 700; }}
            QLabel#Muted, QLabel {{ color: {PALETTE["muted"]}; font-size: 12px; }}
            QLabel#RuntimeTotal {{ color: {PALETTE["primary_blue"]}; font-size: 32px; font-weight: 900; }}
            QLabel#SuccessText {{ color: {PALETTE["success"]}; font-size: 12px; font-weight: 700; }}
            QLabel#WarningText {{ color: {PALETTE["warning"]}; font-size: 12px; font-weight: 700; }}
            QLineEdit, QComboBox {{
                min-height: 32px;
                background: {PALETTE["soft"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 8px;
                color: {PALETTE["text"]};
                padding: 0 10px;
            }}
            QTextEdit {{
                background: {PALETTE["soft"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 8px;
                color: {PALETTE["text"]};
                padding: 8px;
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{ border: 1px solid {PALETTE["blue"]}; }}
            QPushButton {{
                min-height: 32px;
                border-radius: 10px;
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
            QPushButton#DangerOutlineBtn {{
                background: rgba(255, 93, 115, 0.08);
                color: {PALETTE["danger"]};
                border: 1px solid rgba(255, 93, 115, 0.7);
            }}
            QPushButton#LinkBtn {{
                background: transparent;
                color: {PALETTE["primary_blue"]};
                border: none;
                padding: 0;
            }}
            QPushButton#ChipBtn {{
                background: {PALETTE["soft"]};
                color: {PALETTE["text_soft"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 16px;
                padding: 0 10px;
            }}
            QPushButton#ChipBtn:checked {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {PALETTE["cyan"]}, stop:1 {PALETTE["blue"]});
                color: #041018;
                border: 1px solid rgba(0, 200, 255, 0.8);
            }}
            QFrame#PhaseCard {{
                background: {PALETTE["soft"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 12px;
            }}
            QLabel#PhaseTitle {{ color: {PALETTE["text"]}; font-size: 13px; font-weight: 700; }}
            QLabel#DurationBadge {{
                background: rgba(29, 161, 255, 0.12);
                color: {PALETTE["primary_blue"]};
                border: 1px solid rgba(29, 161, 255, 0.55);
                border-radius: 8px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 700;
            }}
            QFrame#PhaseProgress {{
                border: none;
                border-radius: 4px;
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {PALETTE["primary_blue"]}, stop:1 {PALETTE["purple"]});
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
            QCheckBox {{
                color: {PALETTE["text_soft"]};
                spacing: 8px;
                font-size: 12px;
                font-weight: 600;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid {PALETTE["border"]};
                background: {PALETTE["soft"]};
            }}
            QCheckBox::indicator:checked {{
                background: {PALETTE["cyan"]};
                border: 1px solid {PALETTE["cyan"]};
            }}
            QTextEdit#JsonPreview {{
                font-family: Consolas, "Cascadia Mono", monospace;
                font-size: 11px;
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
