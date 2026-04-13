"""Shared top navbar for all ZIMON pages."""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QRegion
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
    QWidget,
)

from widgets.zicons import ICONS, icon


class NavTabButton(QPushButton):
    """Capsule tab button used inside segmented top strip."""

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setObjectName("ZNavTabPill")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedHeight(38)
        self.setMinimumWidth(86)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)


class CircleIconButton(QPushButton):
    """Circular icon button (notification/settings)."""

    def __init__(self, icon_name: str, tooltip: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ZCircleIconPill")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(38, 38)
        self.setIcon(icon(icon_name, "#CFE8FF", 16))
        self.setIconSize(self.iconSize())
        if tooltip:
            self.setToolTip(tooltip)


class UserProfileButton(QToolButton):
    """Username + chevron pill in the right segmented strip."""

    def __init__(self, full_name: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ZUserProfilePill")
        self.setText(full_name)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setIcon(icon(ICONS["chevron_down"], "#9CC7E8", 12))
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedHeight(38)
        self.setMinimumWidth(138)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)


class TopNavbar(QFrame):
    """Premium futuristic segmented-capsule navbar."""

    page_changed = pyqtSignal(int)
    check_environment_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    profile_clicked = pyqtSignal()

    def __init__(self, user_data: dict | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ZimonTopNav")
        self._user = user_data or {}
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(68)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(10)

        left = QHBoxLayout()
        left.setSpacing(8)
        left.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._logo = QLabel()
        self._logo.setObjectName("ZimonNavLogo")
        self._logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo.setFixedSize(40, 40)
        logo_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "gui", "images", "cropped_circle_image.png")
        )
        logo_pix = QPixmap(logo_path)
        if not logo_pix.isNull():
            self._logo.setPixmap(
                logo_pix.scaled(
                    40,
                    40,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self._logo.setMask(QRegion(self._logo.rect(), QRegion.RegionType.Ellipse))
        self._title = QLabel("ZIMON")
        self._title.setObjectName("ZimonNavTitle")
        self._btn_check = QPushButton("Check Environment")
        self._btn_check.setObjectName("ZimonCheckEnvBtn")
        self._btn_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_check.setFixedHeight(34)
        self._btn_check.clicked.connect(self.check_environment_clicked.emit)
        left.addWidget(self._logo, 0, Qt.AlignmentFlag.AlignVCenter)
        left.addWidget(self._title, 0, Qt.AlignmentFlag.AlignVCenter)
        left.addSpacing(6)
        left.addWidget(self._btn_check, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(left, 0)
        root.addStretch(1)

        self._nav_strip = QFrame()
        self._nav_strip.setObjectName("ZNavStrip")
        self._nav_strip.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._nav_strip.setFixedHeight(52)
        strip = QHBoxLayout(self._nav_strip)
        strip.setContentsMargins(7, 7, 7, 7)
        strip.setSpacing(6)
        strip.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        labels = ("Adult", "Larval", "Environment", "Protocol Builder", "Experiments")
        self._pills: list[NavTabButton] = []
        self._pill_group = QButtonGroup(self)
        self._pill_group.setExclusive(True)
        for idx, text in enumerate(labels):
            b = NavTabButton(text)
            strip.addWidget(b)
            self._pill_group.addButton(b, idx)
            self._pills.append(b)
        self._pill_group.idClicked.connect(self.page_changed.emit)
        root.addWidget(self._nav_strip, 0, Qt.AlignmentFlag.AlignVCenter)

        root.addSpacing(16)

        actions = QWidget()
        actions.setObjectName("ZNavActions")
        actions.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        ar = QHBoxLayout(actions)
        ar.setContentsMargins(0, 0, 0, 0)
        ar.setSpacing(8)
        ar.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        ar.setDirection(QHBoxLayout.Direction.LeftToRight)
        self._bell = CircleIconButton(ICONS["bell"], "Notifications")
        self._bell.clicked.connect(
            lambda: QMessageBox.information(self.window(), "Notifications", "No new notifications.")
        )
        ar.addWidget(self._bell, 0, Qt.AlignmentFlag.AlignVCenter)

        self._btn_settings = CircleIconButton(ICONS["settings"], "Settings")
        self._btn_settings.clicked.connect(self.settings_clicked.emit)
        ar.addWidget(self._btn_settings, 0, Qt.AlignmentFlag.AlignVCenter)

        fn = str(self._user.get("full_name", "Researcher")).strip() or "Researcher"
        letter = (fn[:1] or "R").upper()
        self._avatar = QPushButton(letter)
        self._avatar.setObjectName("ZUserAvatarPill")
        self._avatar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._avatar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._avatar.setFixedSize(38, 38)
        self._avatar.clicked.connect(self.profile_clicked.emit)
        ar.addWidget(self._avatar, 0, Qt.AlignmentFlag.AlignVCenter)

        self._profile_btn = UserProfileButton(fn)
        self._profile_btn.clicked.connect(self.profile_clicked.emit)
        ar.addWidget(self._profile_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addWidget(actions, 0, Qt.AlignmentFlag.AlignVCenter)

        self._pill_group.setExclusive(False)
        self._pills[0].setChecked(True)
        self._pill_group.setExclusive(True)

        self.setStyleSheet(
            """
            QFrame#ZimonTopNav {
                background: #0b1324;
                border: 1px solid rgba(0, 212, 255, 0.12);
                border-radius: 18px;
            }
            QLabel#ZimonNavLogo {
                min-width: 40px;
                max-width: 40px;
                min-height: 40px;
                max-height: 40px;
                border-radius: 20px;
                background: #101a2f;
                border: 1px solid rgba(30, 167, 255, 0.55);
            }
            QLabel#ZimonNavTitle {
                color: #eaf4ff;
                font-size: 17px;
                font-weight: 800;
            }
            QPushButton#ZimonCheckEnvBtn {
                background-color: rgba(255, 176, 32, 0.08);
                color: #ffb020;
                border: 1px solid rgba(255, 176, 32, 0.65);
                border-radius: 17px;
                padding: 0 12px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton#ZimonCheckEnvBtn:hover {
                border: 1px solid #ffb020;
                background-color: rgba(255, 176, 32, 0.16);
            }
            QFrame#ZNavStrip {
                background: #0f1829;
                border: 1px solid rgba(0, 170, 255, 0.18);
                border-radius: 26px;
            }
            QPushButton#ZNavTabPill {
                background: transparent;
                color: #94a8c6;
                border: 1px solid transparent;
                border-radius: 19px;
                padding: 0 18px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton#ZNavTabPill:hover {
                border: 1px solid rgba(30, 167, 255, 0.35);
                background: rgba(30, 167, 255, 0.08);
                color: #eaf4ff;
            }
            QPushButton#ZNavTabPill:checked {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #1ea7ff, stop:1 #00d4ff);
                color: #041018;
                border: 1px solid rgba(0, 212, 255, 0.85);
                border-radius: 19px;
                font-weight: 700;
            }
            QPushButton#ZCircleIconPill {
                background: #101a2f;
                border: 1px solid rgba(0, 170, 255, 0.18);
                border-radius: 19px;
            }
            QPushButton#ZCircleIconPill:hover {
                border: 1px solid rgba(30, 167, 255, 0.55);
                background: #15243d;
            }
            QPushButton#ZUserAvatarPill {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #7c4dff, stop:1 #1ea7ff);
                color: #eaf4ff;
                border: 1px solid rgba(0, 212, 255, 0.45);
                border-radius: 19px;
                font-size: 12px;
                font-weight: 800;
            }
            QPushButton#ZUserAvatarPill:hover {
                border: 1px solid rgba(0, 212, 255, 0.8);
            }
            QToolButton#ZUserProfilePill {
                background: #101a2f;
                color: #eaf4ff;
                border: 1px solid rgba(0, 170, 255, 0.18);
                border-radius: 19px;
                padding: 0 34px 0 16px;
                font-size: 12px;
                font-weight: 700;
            }
            QToolButton#ZUserProfilePill:hover {
                border: 1px solid rgba(30, 167, 255, 0.55);
                background: #15243d;
            }
            QToolButton#ZUserProfilePill::menu-button {
                subcontrol-origin: padding;
                subcontrol-position: right center;
                width: 24px;
                border: none;
            }
            QToolButton#ZUserProfilePill::menu-arrow {
                image: none;
                width: 0;
                height: 0;
            }
            """
        )

    def set_profile_menu(self, menu: QMenu) -> None:
        self._profile_btn.setMenu(menu)

    def set_active_index(self, index: int) -> None:
        if 0 <= index < len(self._pills):
            self._pill_group.setExclusive(False)
            for i, b in enumerate(self._pills):
                b.setChecked(i == index)
            self._pill_group.setExclusive(True)


class NavBar(TopNavbar):
    """Backward-compatible name used by existing main window."""
