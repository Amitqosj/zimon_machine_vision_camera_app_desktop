"""Premium user account management screen for ZIMON."""

from __future__ import annotations

import re

from PyQt6.QtCore import QDateTime, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from database.auth import (
    ROLE_ADMIN,
    ROLE_STUDENT,
    clear_active_session,
    create_user,
    list_users,
    set_user_lock_state,
    set_user_password,
    update_user,
)


PALETTE = {
    "main": "#06111F",
    "surface": "#081523",
    "card": "#0D1420",
    "soft": "#102033",
    "border": "#15324D",
    "cyan": "#00C8FF",
    "blue": "#007BFF",
    "purple": "#5B5CFF",
    "text": "#FFFFFF",
    "text_soft": "#CFE8FF",
    "muted": "#8AA6C1",
    "success": "#22C55E",
    "danger": "#FF3355",
    "warning": "#F59E0B",
}

ROLE_COLORS = {
    "ADMIN": PALETTE["purple"],
    "STUDENT": PALETTE["blue"],
    "RESEARCHER": PALETTE["cyan"],
}


def _normalized_role(role: str) -> str:
    return (role or "STUDENT").strip().upper()


def _initials(name: str) -> str:
    parts = [p for p in (name or "").strip().split() if p]
    if not parts:
        return "U"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def _valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value.strip()))


class UserTabsHeader(QFrame):
    tab_changed = pyqtSignal(int)

    def __init__(self, tabs: list[str], parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("UserTabsHeader")
        self._buttons: list[QPushButton] = []
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 0)
        lay.setSpacing(8)
        for idx, tab in enumerate(tabs):
            btn = QPushButton(tab)
            btn.setObjectName("UserTabBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _=False, i=idx: self.tab_changed.emit(i))
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setFixedHeight(40)
            lay.addWidget(btn)
            self._buttons.append(btn)
        self.set_active(0)

    def set_active(self, index: int) -> None:
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == index)


class ProfileTab(QWidget):
    def __init__(self, user_data: dict, parent=None) -> None:
        super().__init__(parent)
        self._user = user_data
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        top = QFrame()
        top.setObjectName("UserCard")
        top_lay = QHBoxLayout(top)
        top_lay.setContentsMargins(18, 18, 18, 18)
        top_lay.setSpacing(16)

        avatar = QLabel(_initials(str(self._user.get("full_name", "User"))))
        avatar.setObjectName("UserLargeAvatar")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(94, 94)
        top_lay.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(8)
        full_name = str(self._user.get("full_name", "Unknown User")).strip() or "Unknown User"
        username = str(self._user.get("username", "unknown")).strip() or "unknown"
        role_text = _normalized_role(str(self._user.get("role", ROLE_STUDENT)))
        role_color = ROLE_COLORS.get(role_text, PALETTE["blue"])

        title = QLabel(full_name)
        title.setObjectName("ProfileName")
        sub = QLabel(f"@{username}")
        sub.setObjectName("ProfileUsername")
        badge = QLabel(role_text)
        badge.setObjectName("RoleBadge")
        badge.setProperty("roleColor", role_color)
        badge.style().unpolish(badge)
        badge.style().polish(badge)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedHeight(26)
        badge.setMinimumWidth(84)

        info.addWidget(title)
        info.addWidget(sub)
        info.addWidget(badge, 0, Qt.AlignmentFlag.AlignLeft)
        info.addStretch(1)
        top_lay.addLayout(info, 1)
        root.addWidget(top)

        details = QFrame()
        details.setObjectName("UserCard")
        dlay = QVBoxLayout(details)
        dlay.setContentsMargins(18, 18, 18, 18)
        dlay.setSpacing(10)

        cap = QLabel("ACCOUNT DETAILS")
        cap.setObjectName("CardCaption")
        dlay.addWidget(cap)

        for label, value in (
            ("Email", str(self._user.get("email", "—"))),
            ("Username", str(self._user.get("username", "—"))),
            ("Member since", str(self._user.get("created_at", "—"))),
        ):
            row = QHBoxLayout()
            left = QLabel(label)
            left.setObjectName("DetailKey")
            right = QLabel(value)
            right.setObjectName("DetailValue")
            row.addWidget(left, 0, Qt.AlignmentFlag.AlignLeft)
            row.addStretch(1)
            row.addWidget(right, 0, Qt.AlignmentFlag.AlignRight)
            dlay.addLayout(row)
            line = QFrame()
            line.setObjectName("DetailDivider")
            line.setFixedHeight(1)
            dlay.addWidget(line)

        root.addWidget(details)
        root.addStretch(1)


class SessionTab(QWidget):
    logout_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        card = QFrame()
        card.setObjectName("UserCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)

        title = QLabel("Session")
        title.setObjectName("SectionTitle")
        desc = QLabel(
            "Sign out to return to the login screen.\nUnsaved work in this session may be lost."
        )
        desc.setObjectName("MutedText")
        desc.setWordWrap(True)
        btn = QPushButton("Log out")
        btn.setObjectName("DangerBtn")
        btn.setFixedHeight(38)
        btn.clicked.connect(self._on_logout_clicked)

        lay.addWidget(title)
        lay.addWidget(desc)
        lay.addSpacing(8)
        lay.addWidget(btn, 0, Qt.AlignmentFlag.AlignLeft)
        lay.addStretch(1)
        root.addWidget(card)
        root.addStretch(1)

    def _on_logout_clicked(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Log out",
            "Logout and return to the login screen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            clear_active_session()
            self.logout_requested.emit()


class AddStudentCard(QFrame):
    create_student = pyqtSignal(str, str, str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("UserCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)

        title = QLabel("ADD STUDENT")
        title.setObjectName("SectionTitle")
        lay.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        self.full_name = QLineEdit()
        self.username = QLineEdit()
        self.email = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.full_name.setPlaceholderText("Full name")
        self.username.setPlaceholderText("Username")
        self.email.setPlaceholderText("Email")
        self.password.setPlaceholderText("Password")

        grid.addWidget(QLabel("Full name"), 0, 0)
        grid.addWidget(self.full_name, 0, 1)
        grid.addWidget(QLabel("Username"), 1, 0)
        grid.addWidget(self.username, 1, 1)
        grid.addWidget(QLabel("Email"), 2, 0)
        grid.addWidget(self.email, 2, 1)
        grid.addWidget(QLabel("Password"), 3, 0)
        grid.addWidget(self.password, 3, 1)
        lay.addLayout(grid)

        note = QLabel("Role is always assigned as STUDENT.")
        note.setObjectName("MutedText")
        lay.addWidget(note)

        btn = QPushButton("Create student")
        btn.setObjectName("PrimaryBtn")
        btn.setFixedHeight(38)
        btn.clicked.connect(self._emit_create)
        lay.addWidget(btn, 0, Qt.AlignmentFlag.AlignLeft)

    def _emit_create(self) -> None:
        self.create_student.emit(
            self.full_name.text(),
            self.username.text(),
            self.email.text(),
            self.password.text(),
        )

    def clear_form(self) -> None:
        self.full_name.clear()
        self.username.clear()
        self.email.clear()
        self.password.clear()


class UserCard(QFrame):
    refresh_requested = pyqtSignal()

    def __init__(self, user_data: dict, parent=None) -> None:
        super().__init__(parent)
        self.user_data = user_data
        self.setObjectName("UserCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(10)

        title = QLabel(f"Name: {user_data.get('full_name', '')}")
        title.setObjectName("SectionTitle")
        meta = QLabel(f"@{user_data.get('username', '')}  •  {user_data.get('email', '')}")
        meta.setObjectName("MutedText")
        state = "Locked" if user_data.get("is_locked") else "Unlocked"
        active = "Active" if user_data.get("is_active") else "Inactive"
        status = QLabel(f"Status: {active} / {state}")
        status.setObjectName("MutedText")
        lay.addWidget(title)
        lay.addWidget(meta)
        lay.addWidget(status)

        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        self.edit_name = QLineEdit(str(user_data.get("full_name", "")))
        self.edit_email = QLineEdit(str(user_data.get("email", "")))
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password.setPlaceholderText("New password")
        self.active_chk = QCheckBox("Active account")
        self.active_chk.setChecked(bool(user_data.get("is_active")))
        form.addWidget(QLabel("Full name"), 0, 0)
        form.addWidget(self.edit_name, 0, 1)
        form.addWidget(QLabel("Email"), 1, 0)
        form.addWidget(self.edit_email, 1, 1)
        form.addWidget(QLabel("Password"), 2, 0)
        form.addWidget(self.new_password, 2, 1)
        form.addWidget(self.active_chk, 3, 1)
        lay.addLayout(form)

        row = QHBoxLayout()
        row.setSpacing(10)
        save_btn = QPushButton("Save")
        save_btn.setObjectName("SecondaryBtn")
        lock_btn = QPushButton("Unlock" if user_data.get("is_locked") else "Lock")
        lock_btn.setObjectName("WarningBtn")
        reset_btn = QPushButton("Reset Password")
        reset_btn.setObjectName("DangerBtn")
        for b in (save_btn, lock_btn, reset_btn):
            b.setFixedHeight(38)
            row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)

        save_btn.clicked.connect(self._on_save)
        lock_btn.clicked.connect(lambda: self._on_lock_toggle(bool(user_data.get("is_locked"))))
        reset_btn.clicked.connect(self._on_reset_password)

    def _on_save(self) -> None:
        name = self.edit_name.text().strip()
        email = self.edit_email.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Full name is required.")
            return
        if not _valid_email(email):
            QMessageBox.warning(self, "Validation", "Please enter a valid email.")
            return
        ok = update_user(self.user_data["id"], name, email, self.active_chk.isChecked())
        if ok:
            QMessageBox.information(self, "Saved", "User profile updated successfully.")
            self.refresh_requested.emit()
            return
        QMessageBox.warning(self, "Update failed", "Unable to save user changes.")

    def _on_lock_toggle(self, currently_locked: bool) -> None:
        ok = set_user_lock_state(self.user_data["id"], not currently_locked)
        if ok:
            QMessageBox.information(
                self,
                "User updated",
                "User unlocked." if currently_locked else "User locked.",
            )
            self.refresh_requested.emit()
            return
        QMessageBox.warning(self, "Update failed", "Unable to update lock state.")

    def _on_reset_password(self) -> None:
        new_pw = self.new_password.text().strip()
        if len(new_pw) < 6:
            QMessageBox.warning(self, "Validation", "Password must be at least 6 characters.")
            return
        ok = set_user_password(self.user_data["id"], new_pw, unlock=True)
        if ok:
            QMessageBox.information(self, "Updated", "Password reset successfully.")
            self.new_password.clear()
            self.refresh_requested.emit()
            return
        QMessageBox.warning(self, "Update failed", "Unable to reset password.")


class UserManagementTab(QWidget):
    def __init__(self, user_data: dict, parent=None) -> None:
        super().__init__(parent)
        self._user = user_data
        self._is_admin = _normalized_role(str(user_data.get("role", ""))) == "ADMIN"

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        if not self._is_admin:
            card = QFrame()
            card.setObjectName("UserCard")
            c = QVBoxLayout(card)
            c.setContentsMargins(18, 18, 18, 18)
            msg = QLabel("You do not have permission.")
            msg.setObjectName("SectionTitle")
            c.addWidget(msg)
            c.addStretch(1)
            root.addWidget(card)
            root.addStretch(1)
            return

        self.add_card = AddStudentCard()
        self.add_card.create_student.connect(self._create_student)
        root.addWidget(self.add_card)

        list_title = QLabel("USER LIST / MANAGE USERS")
        list_title.setObjectName("SectionTitle")
        root.addWidget(list_title)

        self.user_list_wrap = QWidget()
        self.user_list_layout = QVBoxLayout(self.user_list_wrap)
        self.user_list_layout.setContentsMargins(0, 0, 0, 0)
        self.user_list_layout.setSpacing(12)
        root.addWidget(self.user_list_wrap)
        root.addStretch(1)
        self._reload_users()

    def _create_student(self, full_name: str, username: str, email: str, password: str) -> None:
        full_name = full_name.strip()
        username = username.strip()
        email = email.strip()
        password = password.strip()
        if not full_name or not username or not email or not password:
            QMessageBox.warning(self, "Validation", "All fields are required.")
            return
        if not _valid_email(email):
            QMessageBox.warning(self, "Validation", "Please enter a valid email.")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "Validation", "Password must be at least 6 characters.")
            return
        ok, payload = create_user(full_name, username, email, password, role=ROLE_STUDENT)
        if ok:
            QMessageBox.information(self, "Success", "Student created successfully.")
            self.add_card.clear_form()
            self._reload_users()
            return
        QMessageBox.warning(self, "Create failed", str(payload))

    def _reload_users(self) -> None:
        while self.user_list_layout.count():
            item = self.user_list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        for user in list_users():
            card = UserCard(user)
            card.refresh_requested.connect(self._reload_users)
            self.user_list_layout.addWidget(card)
        self.user_list_layout.addStretch(1)


class StatusFooter(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("UserFooter")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(16)
        self.left = QLabel(
            "System: Disconnected   |   Camera: Idle   |   Chamber: Idle   |   Temperature: —   |   Water flow: —"
        )
        self.left.setObjectName("FooterLeft")
        self.right = QLabel("")
        self.right.setObjectName("FooterRight")
        lay.addWidget(self.left, 1)
        lay.addWidget(self.right, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)


class UserScreen(QWidget):
    logout_requested = pyqtSignal()

    def __init__(self, user_data: dict, parent=None) -> None:
        super().__init__(parent)
        self._user_data = user_data or {}

        self.setObjectName("UserScreen")
        self.setStyleSheet(self._qss())

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 8)
        root.setSpacing(10)

        body_scroll = QScrollArea()
        body_scroll.setWidgetResizable(True)
        body_scroll.setFrameShape(QFrame.Shape.NoFrame)
        body_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        root.addWidget(body_scroll, 1)

        wrap = QWidget()
        sc_lay = QVBoxLayout(wrap)
        sc_lay.setContentsMargins(0, 0, 0, 0)
        sc_lay.setSpacing(0)

        center = QHBoxLayout()
        center.setContentsMargins(0, 0, 0, 0)
        center.addStretch(1)

        card = QFrame()
        card.setObjectName("UserPageCard")
        card.setMinimumWidth(900)
        card.setMaximumWidth(1050)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(14, 14, 14, 14)
        card_lay.setSpacing(10)

        tabs = ["Profile", "Session"]
        self._is_admin = _normalized_role(str(self._user_data.get("role", ""))) == "ADMIN"
        if self._is_admin:
            tabs.append("User Management")
        self._header = UserTabsHeader(tabs)
        self._header.tab_changed.connect(self._switch_tab)
        card_lay.addWidget(self._header)

        self._stack = QStackedWidget()
        self._stack.addWidget(ProfileTab(self._user_data))
        self._session_tab = SessionTab()
        self._session_tab.logout_requested.connect(self.logout_requested.emit)
        self._stack.addWidget(self._session_tab)
        if self._is_admin:
            self._stack.addWidget(UserManagementTab(self._user_data))
        card_lay.addWidget(self._stack, 1)
        center.addWidget(card, 0)
        center.addStretch(1)
        sc_lay.addLayout(center)
        body_scroll.setWidget(wrap)

        self._footer = StatusFooter()
        root.addWidget(self._footer, 0)

        self._clock = QTimer(self)
        self._clock.timeout.connect(self._tick_clock)
        self._clock.start(1000)
        self._tick_clock()

    def _tick_clock(self) -> None:
        self._footer.right.setText(QDateTime.currentDateTime().toString("h:mm AP MMM d, yyyy"))

    def _switch_tab(self, index: int) -> None:
        self._header.set_active(index)
        self._stack.setCurrentIndex(index)

    @staticmethod
    def _qss() -> str:
        return f"""
            QWidget#UserScreen {{
                background: {PALETTE["main"]};
                color: {PALETTE["text"]};
            }}
            QFrame#UserPageCard {{
                background: {PALETTE["surface"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 16px;
            }}
            QFrame#UserTabsHeader {{
                background: {PALETTE["soft"]};
                border: 1px solid {PALETTE["border"]};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
            QPushButton#UserTabBtn {{
                background: {PALETTE["card"]};
                color: {PALETTE["muted"]};
                border: 1px solid {PALETTE["border"]};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton#UserTabBtn:hover {{
                color: {PALETTE["text_soft"]};
                border-color: {PALETTE["cyan"]};
            }}
            QPushButton#UserTabBtn:checked {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {PALETTE["cyan"]}, stop:0.55 {PALETTE["blue"]}, stop:1 {PALETTE["purple"]});
                color: {PALETTE["text"]};
                border-color: rgba(0, 200, 255, 0.75);
            }}
            QFrame#UserCard {{
                background: {PALETTE["card"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 14px;
            }}
            QLabel#UserLargeAvatar {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {PALETTE["purple"]}, stop:1 {PALETTE["cyan"]});
                border: 1px solid rgba(0, 200, 255, 0.75);
                border-radius: 47px;
                font-size: 28px;
                font-weight: 800;
                color: {PALETTE["text"]};
            }}
            QLabel#ProfileName {{
                color: {PALETTE["text"]};
                font-size: 24px;
                font-weight: 800;
            }}
            QLabel#ProfileUsername {{
                color: {PALETTE["text_soft"]};
                font-size: 13px;
                font-weight: 600;
            }}
            QLabel#RoleBadge {{
                background: #1A2A3D;
                border: 1px solid {PALETTE["border"]};
                border-radius: 8px;
                color: {PALETTE["text"]};
                font-size: 12px;
                font-weight: 800;
                padding: 0 8px;
            }}
            QLabel#RoleBadge[roleColor="{PALETTE["purple"]}"] {{ border-color: {PALETTE["purple"]}; color: {PALETTE["purple"]}; }}
            QLabel#RoleBadge[roleColor="{PALETTE["blue"]}"] {{ border-color: {PALETTE["blue"]}; color: {PALETTE["blue"]}; }}
            QLabel#RoleBadge[roleColor="{PALETTE["cyan"]}"] {{ border-color: {PALETTE["cyan"]}; color: {PALETTE["cyan"]}; }}
            QLabel#CardCaption {{
                color: {PALETTE["text_soft"]};
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 1px;
            }}
            QLabel#DetailKey {{
                color: {PALETTE["muted"]};
                font-size: 13px;
            }}
            QLabel#DetailValue {{
                color: {PALETTE["text"]};
                font-size: 13px;
                font-weight: 600;
            }}
            QFrame#DetailDivider {{
                background: {PALETTE["border"]};
                border: none;
            }}
            QLabel#SectionTitle {{
                color: {PALETTE["text"]};
                font-size: 16px;
                font-weight: 800;
            }}
            QLabel#MutedText {{
                color: {PALETTE["muted"]};
                font-size: 12px;
            }}
            QLabel {{
                color: {PALETTE["text_soft"]};
                font-size: 12px;
                font-weight: 500;
            }}
            QLineEdit {{
                min-height: 38px;
                background: {PALETTE["soft"]};
                border: 1px solid {PALETTE["border"]};
                border-radius: 8px;
                color: {PALETTE["text"]};
                padding: 0 10px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {PALETTE["blue"]};
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
            QPushButton {{
                min-height: 38px;
                border-radius: 10px;
                padding: 0 16px;
                font-size: 12px;
                font-weight: 700;
                color: {PALETTE["text"]};
            }}
            QPushButton#PrimaryBtn {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {PALETTE["blue"]}, stop:1 {PALETTE["purple"]});
                border: 1px solid rgba(110, 165, 255, 0.8);
            }}
            QPushButton#SecondaryBtn {{
                background: {PALETTE["soft"]};
                border: 1px solid {PALETTE["border"]};
            }}
            QPushButton#SuccessBtn {{
                background: {PALETTE["success"]};
                border: 1px solid {PALETTE["success"]};
            }}
            QPushButton#DangerBtn {{
                background: {PALETTE["danger"]};
                border: 1px solid {PALETTE["danger"]};
            }}
            QPushButton#WarningBtn {{
                background: {PALETTE["warning"]};
                border: 1px solid {PALETTE["warning"]};
                color: #101010;
            }}
            QFrame#UserFooter {{
                background: #071426;
                border-top: 1px solid {PALETTE["border"]};
                border-radius: 0;
            }}
            QLabel#FooterLeft, QLabel#FooterRight {{
                color: {PALETTE["muted"]};
                font-size: 11px;
            }}
        """
