"""Shared top navbar for all ZIMON pages."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from widgets.icon_button import ZIconButton
from widgets.zicons import ICONS, icon


class NavBar(QFrame):
    """Fixed header: branding, Check Environment, pill nav, actions, profile."""

    page_changed = pyqtSignal(int)
    check_environment_clicked = pyqtSignal()
    theme_toggle_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    help_clicked = pyqtSignal()

    def __init__(self, user_data: dict | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ZimonTopNav")
        self._user = user_data or {}
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(88)

        root = QHBoxLayout(self)
        root.setContentsMargins(18, 10, 18, 10)
        root.setSpacing(16)

        left = QHBoxLayout()
        left.setSpacing(12)
        self._logo = QLabel("Z")
        self._logo.setObjectName("ZimonNavLogo")
        self._logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand = QVBoxLayout()
        brand.setSpacing(2)
        row = QHBoxLayout()
        self._title = QLabel("ZIMON")
        self._title.setObjectName("ZimonNavTitle")
        row.addWidget(self._title)
        row.addStretch(1)
        brand.addLayout(row)
        self._sub = QLabel("Zebrafish Integrated Motion & Optical Neuro System")
        self._sub.setObjectName("ZimonNavSubtitle")
        self._sub.setWordWrap(True)
        brand.addWidget(self._sub)
        left.addWidget(self._logo, 0, Qt.AlignmentFlag.AlignTop)
        left.addLayout(brand, 1)

        self._btn_check = QPushButton("  Check Environment  ")
        self._btn_check.setObjectName("ZimonCheckEnvBtn")
        self._btn_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_check.setIcon(icon(ICONS["check_env"], "#ffb020", 16))
        self._btn_check.clicked.connect(self.check_environment_clicked.emit)
        left.addWidget(self._btn_check, 0, Qt.AlignmentFlag.AlignVCenter)

        root.addLayout(left, 0)
        root.addStretch(1)

        mid = QWidget()
        ml = QHBoxLayout(mid)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(8)

        def pill(idx: int, label: str, fa: str) -> QPushButton:
            b = QPushButton(label)
            b.setObjectName("ZimonNavPill")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setIcon(icon(fa, "#94a8c6", 16))
            b.clicked.connect(lambda _=False, i=idx, btn=b: self._on_pill(i, btn))
            ml.addWidget(b)
            return b

        self._pills = [
            pill(0, "  Adult", ICONS["adult"]),
            pill(1, "  Larval", ICONS["larval"]),
            pill(2, "  Environment", ICONS["environment"]),
            pill(3, "  Protocol Builder", ICONS["protocol"]),
            pill(4, "  Experiments", ICONS["experiments"]),
        ]
        self._pill_group = QButtonGroup(self)
        self._pill_group.setExclusive(True)
        for b in self._pills:
            self._pill_group.addButton(b)

        root.addWidget(mid, 0)
        root.addStretch(1)

        right = QHBoxLayout()
        right.setSpacing(10)

        self._bell = ZIconButton(icon(ICONS["bell"], "#eaf4ff", 20), tooltip="Notifications")
        self._badge = QLabel(self._bell)
        self._badge.setFixedSize(10, 10)
        self._badge.setStyleSheet(
            "background:#ff4d5a; border-radius:5px; border:1px solid #050b18;"
        )
        self._badge.raise_()
        self._bell.clicked.connect(
            lambda: QMessageBox.information(
                self.window(), "Notifications", "No new notifications."
            )
        )
        right.addWidget(self._bell)

        self._btn_theme = ZIconButton(icon(ICONS["sun"], "#eaf4ff", 18), tooltip="Toggle accent contrast")
        self._btn_theme.clicked.connect(self.theme_toggle_clicked.emit)
        right.addWidget(self._btn_theme)

        self._btn_settings = ZIconButton(icon(ICONS["settings"], "#eaf4ff", 18), tooltip="Settings")
        self._btn_settings.clicked.connect(self.settings_clicked.emit)
        right.addWidget(self._btn_settings)

        self._btn_help = ZIconButton(icon(ICONS["help"], "#eaf4ff", 18), tooltip="Help")
        self._btn_help.clicked.connect(self.help_clicked.emit)
        right.addWidget(self._btn_help)

        prof = QFrame()
        prof.setObjectName("ZProfileCard")
        ph = QHBoxLayout(prof)
        ph.setContentsMargins(10, 6, 12, 6)
        ph.setSpacing(10)
        fn = str(self._user.get("full_name", "Researcher")).strip() or "Researcher"
        letter = (fn[:1] or "A").upper()
        av = QLabel(letter)
        av.setObjectName("ZAvatar")
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph.addWidget(av)
        self._profile_btn = QToolButton()
        self._profile_btn.setText(fn)
        self._profile_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._profile_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self._profile_btn.setStyleSheet(
            "QToolButton { color:#eaf4ff; font-weight:800; border:none; padding:4px; }"
        )
        self._profile_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._profile_btn.setIcon(icon(ICONS["chevron_down"], "#94a8c6", 12))
        ph.addWidget(self._profile_btn, 1)
        right.addWidget(prof)

        root.addLayout(right, 0)

        self._pill_group.setExclusive(False)
        self._pills[0].setChecked(True)
        self._pill_group.setExclusive(True)
        self._refresh_pill_icons()

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        if hasattr(self, "_badge") and self._badge.parent() == self._bell:
            self._badge.move(self._bell.width() - 14, 6)

    def set_profile_menu(self, menu: QMenu) -> None:
        self._profile_btn.setMenu(menu)

    def set_active_index(self, index: int) -> None:
        if 0 <= index < len(self._pills):
            self._pill_group.setExclusive(False)
            for i, b in enumerate(self._pills):
                b.setChecked(i == index)
            self._pill_group.setExclusive(True)
            self._refresh_pill_icons()

    def _refresh_pill_icons(self) -> None:
        mapping = [
            ICONS["adult"],
            ICONS["larval"],
            ICONS["environment"],
            ICONS["protocol"],
            ICONS["experiments"],
        ]
        for i, b in enumerate(self._pills):
            col = "#041018" if b.isChecked() else "#94a8c6"
            b.setIcon(icon(mapping[i], col, 16))

    def _on_pill(self, index: int, btn: QPushButton) -> None:
        if not btn.isChecked():
            return
        self._refresh_pill_icons()
        self.page_changed.emit(index)

    def set_theme_icon_sun(self, sun: bool) -> None:
        self._btn_theme.setIcon(icon(ICONS["sun"] if sun else ICONS["moon"], "#eaf4ff", 18))
