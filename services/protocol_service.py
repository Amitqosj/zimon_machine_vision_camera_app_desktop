"""Protocol model, validation, and JSON export (placeholder logic)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal


@dataclass
class StimulusConfig:
    on: bool = False
    intensity: int = 0
    frequency_hz: float = 0.0
    pulse_ms: int = 0
    duration_s: float = 0.0
    delay_s: float = 0.0
    repeat: int = 1


@dataclass
class PhaseBlock:
    name: str
    duration_s: float
    light: StimulusConfig = field(default_factory=StimulusConfig)
    buzzer: StimulusConfig = field(default_factory=StimulusConfig)
    vibration: StimulusConfig = field(default_factory=StimulusConfig)
    water: StimulusConfig = field(default_factory=StimulusConfig)


@dataclass
class ProtocolModel:
    name: str
    description: str = ""
    phases: list[PhaseBlock] = field(default_factory=list)


class ProtocolService(QObject):
    """In-memory protocol editing; ready to swap for file/API persistence."""

    model_changed = pyqtSignal()
    validation_changed = pyqtSignal(list)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._model = ProtocolModel(
            name="Startle Response",
            description="Behavioral startle response protocol for zebrafish.",
            phases=[
                PhaseBlock("Baseline", 10.0),
                PhaseBlock(
                    "Stimulus",
                    2.0,
                    light=StimulusConfig(True, 80, 5.0, 50, 2.0, 0.0, 1),
                    buzzer=StimulusConfig(True, 70, 0.0, 0, 0.1, 0.0, 1),
                    vibration=StimulusConfig(True, 5, 0.0, 0, 2.0, 0.0, 1),
                ),
                PhaseBlock("Recovery", 30.0),
            ],
        )
        self._validate()

    def model(self) -> ProtocolModel:
        return self._model

    def set_meta(self, name: str, description: str) -> None:
        self._model.name = name
        self._model.description = description
        self.model_changed.emit()
        self._validate()

    def set_phases(self, phases: list[PhaseBlock]) -> None:
        self._model.phases = phases
        self.model_changed.emit()
        self._validate()

    def duplicate(self) -> None:
        self._model.name = f"{self._model.name} (copy)"
        self.model_changed.emit()
        self._validate()

    def _validate(self) -> None:
        warnings: list[str] = []
        if not self._model.name.strip():
            warnings.append("Missing protocol name.")
        total = sum(p.duration_s for p in self._model.phases)
        if total <= 0:
            warnings.append("Invalid duration: total runtime is zero.")
        for i, p in enumerate(self._model.phases):
            if p.duration_s < 0:
                warnings.append(f"Phase {i + 1} ({p.name}): negative duration.")
        # Placeholder overlap rule
        stim = [p for p in self._model.phases if p.name.lower() == "stimulus"]
        if len(stim) > 1:
            warnings.append("Overlapping conflict: multiple stimulus phases detected.")
        self.validation_changed.emit(warnings)

    def to_json(self) -> str:
        def serialize_phase(p: PhaseBlock) -> dict[str, Any]:
            return {
                "name": p.name,
                "duration_s": p.duration_s,
                "stimuli": {
                    "light": asdict(p.light),
                    "buzzer": asdict(p.buzzer),
                    "vibration": asdict(p.vibration),
                    "water": asdict(p.water),
                },
            }

        payload = {
            "name": self._model.name,
            "description": self._model.description,
            "phases": [serialize_phase(p) for p in self._model.phases],
        }
        return json.dumps(payload, indent=2)
