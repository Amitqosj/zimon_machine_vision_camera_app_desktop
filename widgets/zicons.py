"""Font Awesome style icons via QtAwesome (optional); safe fallbacks."""

from __future__ import annotations

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QSize


def _empty() -> QIcon:
    return QIcon()


def icon(fa_name: str, color: str = "#eaf4ff", size: int = 18) -> QIcon:
    """Return QIcon from QtAwesome (fa5s.*) or a minimal text fallback."""
    try:
        import qtawesome as qta

        return qta.icon(fa_name, color=color)
    except Exception:
        return _text_fallback_icon(fa_name, color, size)


def _text_fallback_icon(hint: str, color: str, size: int) -> QIcon:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QColor(color))
    f = QFont("Segoe UI", max(8, size // 3))
    f.setBold(True)
    p.setFont(f)
    sym = "●"
    if "bell" in hint:
        sym = "◆"
    elif "play" in hint or "desktop" in hint or "tv" in hint:
        sym = "▶"
    elif "microscope" in hint:
        sym = "μ"
    elif "microchip" in hint or "server" in hint:
        sym = "▣"
    elif "layer" in hint:
        sym = "☰"
    elif "flask" in hint or "folder" in hint:
        sym = "◈"
    elif "shield" in hint:
        sym = "◇"
    elif "sun" in hint:
        sym = "☀"
    elif "moon" in hint:
        sym = "☾"
    elif "cog" in hint:
        sym = "⚙"
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, sym)
    p.end()
    return QIcon(pm)


# Semantic aliases → Font Awesome 5 solid names
ICONS = {
    "check_env": "fa5s.shield-alt",
    "adult": "fa5s.desktop",
    "larval": "fa5s.microscope",
    "environment": "fa5s.microchip",
    "protocol": "fa5s.layer-group",
    "experiments": "fa5s.flask",
    "bell": "fa5s.bell",
    "sun": "fa5s.sun",
    "moon": "fa5s.moon",
    "settings": "fa5s.cog",
    "help": "fa5s.question-circle",
    "play": "fa5s.play",
    "stop": "fa5s.stop",
    "pause": "fa5s.pause",
    "square": "fa5s.square",
    "light": "fa5s.lightbulb",
    "volume": "fa5s.volume-up",
    "zap": "fa5s.bolt",
    "droplet": "fa5s.tint",
    "grid": "fa5s.th",
    "route": "fa5s.route",
    "split": "fa5s.columns",
    "square_dashed": "fa5s.vector-square",
    "circle_half": "fa5s.adjust",
    "refresh": "fa5s.sync-alt",
    "link": "fa5s.external-link-alt",
    "activity": "fa5s.chart-line",
    "camera": "fa5s.video",
    "sliders": "fa5s.sliders-h",
    "chevron_down": "fa5s.chevron-down",
    "plus": "fa5s.plus",
    "trash": "fa5s.trash-alt",
    "folder_open": "fa5s.folder-open",
    "search": "fa5s.search",
    "replay": "fa5s.redo",
    "back": "fa5s.undo",
    "close": "fa5s.times",
    "eye": "fa5s.eye",
    "clock": "fa5s.clock",
}
