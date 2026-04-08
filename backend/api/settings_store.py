"""Persist web/API-only settings (ZebraZoom path, etc.) under config/api_settings.json."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_DIR = os.path.join(_ROOT, "config")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "api_settings.json")


def load_settings() -> Dict[str, Any]:
    if not os.path.isfile(SETTINGS_FILE):
        return {"zebrazoom_exe": ""}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"zebrazoom_exe": ""}
            return data
    except Exception:
        return {"zebrazoom_exe": ""}


def save_settings(updates: Dict[str, Any]) -> Dict[str, Any]:
    current = load_settings()
    current.update({k: v for k, v in updates.items() if v is not None})
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    return current
