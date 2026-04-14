"""ZIMON PyQt login — split branding / form layout using assets from gui/images."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QRect, QSettings, pyqtSignal
from PyQt6.QtGui import QFont, QPainterPath, QPixmap, QRegion
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database.auth import verify_login_credentials, set_active_session

_IMAGES_DIR = Path(__file__).resolve().parent / "images"

# Large-screen layout (login + forgot password)
WINDOW_W = 1200
WINDOW_H = 760
CARD_W = int(WINDOW_W * 0.90)
CARD_H = int(WINDOW_H * 0.88)
MARGIN_X = (WINDOW_W - CARD_W) // 2
MARGIN_Y = (WINDOW_H - CARD_H) // 2

# Slightly smaller layout for forgot-password screen
FORGOT_WINDOW_W = 1040
FORGOT_WINDOW_H = 680
FORGOT_CARD_W = int(FORGOT_WINDOW_W * 0.90)
FORGOT_CARD_H = int(FORGOT_WINDOW_H * 0.88)
FORGOT_MARGIN_X = (FORGOT_WINDOW_W - FORGOT_CARD_W) // 2
FORGOT_MARGIN_Y = (FORGOT_WINDOW_H - FORGOT_CARD_H) // 2


def _pixmap(path: Path, max_w: int, max_h: int) -> QPixmap | None:
    if not path.is_file():
        return None
    pm = QPixmap(str(path))
    if pm.isNull():
        return None
    return pm.scaled(
        max_w,
        max_h,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def _zimon11_paths() -> list[Path]:
    base = _IMAGES_DIR / "zimon11"
    return [base.with_suffix(".jpeg"), base.with_suffix(".jpg"), base.with_suffix(".png")]


def _hero_pixmap_cover(target_w: int, target_h: int) -> QPixmap | None:
    """Load zimon11 (jpeg/jpg/png) and scale+crop to exactly fill the left panel."""
    pm0: QPixmap | None = None
    for p in _zimon11_paths():
        if p.is_file():
            pm0 = QPixmap(str(p))
            if not pm0.isNull():
                break
    if pm0 is None or pm0.isNull():
        return None
    scaled = pm0.scaled(
        target_w,
        target_h,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    x = max(0, (scaled.width() - target_w) // 2)
    y = max(0, (scaled.height() - target_h) // 2)
    return scaled.copy(QRect(x, y, target_w, target_h))


class ImagePanel(QFrame):
    """Left split panel with cover image and rounded left corners."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("loginBrandPanel")
        self._hero_pm: QPixmap | None = None
        for p in _zimon11_paths():
            if p.is_file():
                pm = QPixmap(str(p))
                if not pm.isNull():
                    self._hero_pm = pm
                    break

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._image = QLabel()
        self._image.setObjectName("loginHeroImage")
        self._image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image.setScaledContents(False)
        lay.addWidget(self._image, 1)

        if self._hero_pm is None:
            fallback = QWidget()
            fl = QVBoxLayout(fallback)
            fl.setContentsMargins(28, 36, 28, 28)
            fl.setSpacing(16)
            fl.addStretch(1)
            logo_lbl = QLabel()
            logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_pm = _pixmap(_IMAGES_DIR / "zimon-logo.png", 220, 220)
            if logo_pm:
                logo_lbl.setPixmap(logo_pm)
            else:
                logo_lbl.setText("ZIMON")
                logo_lbl.setStyleSheet("color: #ffffff; font-size: 42px; font-weight: 800;")
            fl.addWidget(logo_lbl)
            zimon_title = QLabel("ZIMON")
            zimon_title.setObjectName("loginBrandTitle")
            zimon_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            f = QFont()
            f.setPointSize(26)
            f.setWeight(QFont.Weight.Bold)
            zimon_title.setFont(f)
            fl.addWidget(zimon_title)
            chamber_line = QLabel(
                "ZEBRAFISH INTEGRATED MOTION &\nOPTICAL NEUROANALYSIS CHAMBER"
            )
            chamber_line.setObjectName("loginBrandSubtitle")
            chamber_line.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chamber_line.setWordWrap(True)
            fl.addWidget(chamber_line)
            fl.addStretch(2)
            lay.addWidget(fallback, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_left_corner_mask()
        if self._hero_pm is None:
            return
        target_w = max(1, self.width())
        target_h = max(1, self.height())
        scaled = self._hero_pm.scaled(
            target_w,
            target_h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = max(0, (scaled.width() - target_w) // 2)
        y = max(0, (scaled.height() - target_h) // 2)
        self._image.setPixmap(scaled.copy(QRect(x, y, target_w, target_h)))

    def _apply_left_corner_mask(self) -> None:
        w = max(1, self.width())
        h = max(1, self.height())
        r = 24.0
        path = QPainterPath()
        path.moveTo(r, 0)
        path.lineTo(w, 0)
        path.lineTo(w, h)
        path.lineTo(r, h)
        path.quadTo(0, h, 0, h - r)
        path.lineTo(0, r)
        path.quadTo(0, 0, r, 0)
        path.closeSubpath()
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))


class LoginSplitContainer(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("loginShellCard")


class LoginFormPanel(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("loginFormPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_right_corner_mask()

    def _apply_right_corner_mask(self) -> None:
        w = max(1, self.width())
        h = max(1, self.height())
        r = 24.0
        path = QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(w - r, 0)
        path.quadTo(w, 0, w, r)
        path.lineTo(w, h - r)
        path.quadTo(w, h, w - r, h)
        path.lineTo(0, h)
        path.closeSubpath()
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))


def styled_input_row(glyph: str, placeholder: str) -> tuple[QFrame, QLineEdit]:
    wrap = QFrame()
    wrap.setObjectName("loginInputShell")
    hl = QHBoxLayout(wrap)
    hl.setContentsMargins(0, 0, 0, 0)
    hl.setSpacing(0)
    g = QLabel(glyph)
    g.setObjectName("loginInputGlyph")
    hl.addWidget(g)
    edit = QLineEdit()
    edit.setObjectName("loginLineInner")
    edit.setPlaceholderText(placeholder)
    hl.addWidget(edit, 1)
    return wrap, edit


def brand_hero_left_panel() -> QFrame:
    """Left split panel: cover image with rounded left corners."""
    return ImagePanel()


def _hardware_vsep() -> QFrame:
    line = QFrame()
    line.setObjectName("loginHardwareVSep")
    line.setFixedWidth(1)
    return line


def login_hardware_status_strip() -> QFrame:
    """Bottom strip on the login column (reference: ZIMON HARDWARE STATUS)."""
    strip = QFrame()
    strip.setObjectName("loginHardwareStrip")
    strip.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    root = QVBoxLayout(strip)
    root.setContentsMargins(20, 14, 20, 16)
    root.setSpacing(12)

    head = QHBoxLayout()
    head.setSpacing(12)
    title = QLabel("ZIMON HARDWARE STATUS")
    title.setObjectName("loginHardwareTitle")
    cats = QLabel("Camera • Chamber • Environment")
    cats.setObjectName("loginHardwareCats")
    cats.setAlignment(
        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
    )
    head.addWidget(title, 0)
    head.addStretch(1)
    head.addWidget(cats, 0)
    root.addLayout(head)

    hline = QFrame()
    hline.setObjectName("loginHardwareHSep")
    hline.setFrameShape(QFrame.Shape.NoFrame)
    hline.setFixedHeight(1)
    root.addWidget(hline)

    row = QHBoxLayout()
    row.setSpacing(0)
    row.setContentsMargins(0, 4, 0, 0)

    def cell(icon: str, body: QWidget) -> QWidget:
        w = QWidget()
        w.setObjectName("loginHardwareCell")
        hl = QHBoxLayout(w)
        hl.setContentsMargins(14, 10, 14, 10)
        hl.setSpacing(10)
        ic = QLabel(icon)
        ic.setObjectName("loginHardwareIcon")
        hl.addWidget(ic, 0, Qt.AlignmentFlag.AlignTop)
        hl.addWidget(body, 1, Qt.AlignmentFlag.AlignVCenter)
        return w

    cam_inner = QHBoxLayout()
    cam_inner.setContentsMargins(0, 0, 0, 0)
    cam_inner.setSpacing(6)
    cam_l = QLabel("Camera")
    cam_l.setObjectName("loginHardwareLabel")
    cam_dots = QLabel("…")
    cam_dots.setObjectName("loginHardwareMuted")
    cam_inner.addWidget(cam_l)
    cam_inner.addWidget(cam_dots)
    cam_inner.addStretch(1)
    cam_wrap = QWidget()
    cam_wrap.setObjectName("loginHardwareRowInner")
    cam_wrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    cam_wrap.setLayout(cam_inner)

    ch_inner = QHBoxLayout()
    ch_inner.setContentsMargins(0, 0, 0, 0)
    ch_inner.setSpacing(6)
    ch_l = QLabel("Chamber")
    ch_l.setObjectName("loginHardwareLabel")
    ch_st = QLabel("Idle")
    ch_st.setObjectName("loginHardwareStatusIdle")
    ch_inner.addWidget(ch_l)
    ch_inner.addWidget(ch_st)
    ch_inner.addStretch(1)
    ch_wrap = QWidget()
    ch_wrap.setObjectName("loginHardwareRowInner")
    ch_wrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    ch_wrap.setLayout(ch_inner)

    tp_inner = QHBoxLayout()
    tp_inner.setContentsMargins(0, 0, 0, 0)
    tp_inner.setSpacing(6)
    tp_l = QLabel("Temperature")
    tp_l.setObjectName("loginHardwareLabel")
    tp_st = QLabel("OK")
    tp_st.setObjectName("loginHardwareStatusOk")
    tp_inner.addWidget(tp_l)
    tp_inner.addWidget(tp_st)
    tp_inner.addStretch(1)
    tp_wrap = QWidget()
    tp_wrap.setObjectName("loginHardwareRowInner")
    tp_wrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    tp_wrap.setLayout(tp_inner)

    row.addWidget(cell("📷", cam_wrap), 1)
    row.addWidget(_hardware_vsep(), 0)
    row.addWidget(cell("⚙", ch_wrap), 1)
    row.addWidget(_hardware_vsep(), 0)
    row.addWidget(cell("🌡", tp_wrap), 1)
    root.addLayout(row)

    strip.setMinimumHeight(108)
    return strip


AUTH_SHELL_QSS = """
            QWidget#loginRootOuter {
                background-color: #0c1222;
            }
            QFrame#loginShellCard {
                background-color: #ffffff;
                border-radius: 24px;
                border: 1px solid #1e293b;
            }
            QFrame#loginBrandPanel {
                background-color: #0a1630;
                border-top-left-radius: 24px;
                border-bottom-left-radius: 24px;
                border-right: 1px solid rgba(255,255,255,0.08);
            }
            QLabel#loginHeroImage {
                background-color: #0a1630;
                border-top-left-radius: 24px;
                border-bottom-left-radius: 24px;
            }
            QLabel#loginBrandSubtitle {
                color: rgba(255,255,255,0.88);
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.12em;
                line-height: 1.45;
            }
            QLabel#loginBrandTitle {
                color: #ffffff;
                letter-spacing: 0.08em;
            }
            QFrame#loginFormPanel {
                background-color: #ffffff;
                border-top-right-radius: 24px;
                border-bottom-right-radius: 24px;
            }
            QWidget#loginFormBlock {
                background-color: #ffffff;
            }
            QFrame#loginHardwareStrip {
                background-color: #ffffff;
                border-top: 1px solid #e2e8f0;
                border-bottom-right-radius: 24px;
            }
            QLabel#loginHardwareTitle {
                color: #0f172a;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 0.12em;
            }
            QLabel#loginHardwareCats {
                color: #64748b;
                font-size: 10px;
                font-weight: 500;
            }
            QFrame#loginHardwareHSep {
                background-color: #e2e8f0;
                border: none;
            }
            QFrame#loginHardwareVSep {
                background-color: #e2e8f0;
                border: none;
            }
            QWidget#loginHardwareCell {
                background-color: #ffffff;
            }
            QWidget#loginHardwareRowInner {
                background-color: #ffffff;
            }
            QLabel#loginHardwareIcon {
                color: #0f172a;
                font-size: 15px;
            }
            QLabel#loginHardwareLabel {
                color: #0f172a;
                font-size: 13px;
                font-weight: 600;
            }
            QLabel#loginHardwareMuted {
                color: #64748b;
                font-size: 13px;
                font-weight: 500;
            }
            QLabel#loginHardwareStatusIdle {
                color: #2563eb;
                font-size: 13px;
                font-weight: 700;
            }
            QLabel#loginHardwareStatusOk {
                color: #15803d;
                font-size: 13px;
                font-weight: 700;
            }
            QLabel#loginWelcomeTitle {
                color: #0f172a;
                font-size: 28px;
                font-weight: 700;
            }
            QLabel#loginWelcomeSub {
                color: #64748b;
                font-size: 14px;
                font-weight: 500;
            }
            QLabel#loginFieldCaption {
                color: #334155;
                font-size: 13px;
                font-weight: 600;
            }
            QFrame#loginInputShell {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                min-height: 45px;
            }
            QLineEdit#loginLineInner {
                border: none;
                background: transparent;
                padding: 12px 10px;
                font-size: 15px;
                color: #0f172a;
            }
            QLineEdit#loginLineInner:focus {
                background: transparent;
            }
            QLabel#loginInputGlyph {
                color: #64748b;
                font-size: 18px;
                padding-left: 14px;
                min-width: 32px;
            }
            QCheckBox#loginRemember {
                color: #475569;
                font-size: 14px;
                font-weight: 500;
            }
            QCheckBox#loginRemember::indicator {
                width: 16px;
                height: 16px;
            }
            QPushButton#loginForgotLink {
                color: #1d4ed8;
                font-size: 14px;
                font-weight: 600;
                border: none;
                padding: 4px 0;
                background: transparent;
            }
            QPushButton#loginForgotLink:hover {
                color: #2563eb;
                text-decoration: underline;
            }
            QPushButton#loginPrimaryBtn {
                background-color: #0f172a;
                color: #ffffff;
                font-size: 14px;
                font-weight: 700;
                border-radius: 10px;
                border: none;
                padding: 9px 18px;
                min-height: 42px;
                max-height: 44px;
            }
            QPushButton#loginPrimaryBtn:hover {
                background-color: #1e293b;
            }
            QPushButton#loginPrimaryBtn:pressed {
                background-color: #020617;
            }
            QPushButton#loginPwToggle {
                border: none;
                background: transparent;
                color: #64748b;
                font-size: 15px;
                padding: 4px 12px;
            }
            QPushButton#loginPwToggle:hover {
                color: #0f172a;
            }
            """


class LoginWindow(QWidget):
    login_success = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.forgot_password_window = None
        self._pw_visible = False
        self._settings = QSettings("ZIMON", "DesktopLogin")

        self.setWindowTitle("ZIMON — Sign in")
        self.setFixedSize(WINDOW_W, WINDOW_H)
        self._build_ui()
        self._apply_saved_username()

    def _apply_saved_username(self):
        if self._settings.value("remember_username", False, type=bool):
            u = self._settings.value("saved_username", "", type=str)
            if u:
                self.username_or_email_input.setText(u)
                self.remember_checkbox.setChecked(True)

    def _build_ui(self):
        self.setObjectName("loginRootOuter")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(MARGIN_X, MARGIN_Y, MARGIN_X, MARGIN_Y)
        outer.setSpacing(0)

        card = LoginSplitContainer()
        card.setFixedSize(CARD_W, CARD_H)
        card_row = QHBoxLayout()
        card_row.addStretch(1)
        card_row.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)
        card_row.addStretch(1)
        outer.addLayout(card_row)

        shell = QHBoxLayout(card)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        left_panel = brand_hero_left_panel()
        shell.addWidget(left_panel, 1)

        # —— Right: white form column + hardware status strip (reference layout) ——
        right = LoginFormPanel()
        outer_rv = QVBoxLayout(right)
        outer_rv.setContentsMargins(0, 0, 0, 0)
        outer_rv.setSpacing(0)

        form_block = QWidget()
        form_block.setObjectName("loginFormBlock")
        form_block.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        rv = QVBoxLayout(form_block)
        rv.setContentsMargins(52, 52, 52, 38)
        rv.setSpacing(19)

        welcome = QLabel("Welcome to ZIMON")
        welcome.setObjectName("loginWelcomeTitle")
        rv.addWidget(welcome)

        sub = QLabel(
            "Zebrafish Integrated Motion & Optical Neuroanalysis Chamber"
        )
        sub.setObjectName("loginWelcomeSub")
        sub.setWordWrap(True)
        rv.addWidget(sub)

        rv.addSpacing(5)

        em_label = QLabel("Email or Username")
        em_label.setObjectName("loginFieldCaption")
        rv.addWidget(em_label)
        self._user_shell, self.username_or_email_input = styled_input_row(
            "👤", "Enter your email or username"
        )
        rv.addWidget(self._user_shell)

        pw_label = QLabel("Password")
        pw_label.setObjectName("loginFieldCaption")
        rv.addWidget(pw_label)
        self._password_row_widget = self._password_row()
        rv.addWidget(self._password_row_widget)

        row = QHBoxLayout()
        row.setSpacing(9)
        self.remember_checkbox = QCheckBox("Remember me")
        self.remember_checkbox.setObjectName("loginRemember")
        row.addWidget(self.remember_checkbox)
        row.addStretch(1)
        self.forgot_password_btn = QPushButton("Forgot Password?")
        self.forgot_password_btn.setObjectName("loginForgotLink")
        self.forgot_password_btn.setFlat(True)
        self.forgot_password_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        row.addWidget(self.forgot_password_btn)
        rv.addLayout(row)

        self.login_btn = QPushButton("Login   →")
        self.login_btn.setObjectName("loginPrimaryBtn")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setMinimumHeight(42)
        self.login_btn.setMaximumHeight(44)
        rv.addWidget(self.login_btn)
        rv.addStretch(1)

        outer_rv.addWidget(form_block, 1)
        outer_rv.addWidget(login_hardware_status_strip(), 0)

        shell.addWidget(right, 1)
        shell.setStretch(0, 1)
        shell.setStretch(1, 1)

        self.setStyleSheet(AUTH_SHELL_QSS)

        self.login_btn.clicked.connect(self._on_login)
        self.forgot_password_btn.clicked.connect(self._open_forgot_password)

    def _password_row(self) -> QFrame:
        wrap = QFrame()
        wrap.setObjectName("loginInputShell")
        hl = QHBoxLayout(wrap)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)
        g = QLabel("🔒")
        g.setObjectName("loginInputGlyph")
        hl.addWidget(g)
        self.password_input = QLineEdit()
        self.password_input.setObjectName("loginLineInner")
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        hl.addWidget(self.password_input, 1)
        self._pw_toggle = QPushButton("👁")
        self._pw_toggle.setObjectName("loginPwToggle")
        self._pw_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pw_toggle.setFixedWidth(44)
        self._pw_toggle.clicked.connect(self._toggle_password_visibility)
        hl.addWidget(self._pw_toggle)
        return wrap

    def _toggle_password_visibility(self):
        self._pw_visible = not self._pw_visible
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Normal
            if self._pw_visible
            else QLineEdit.EchoMode.Password
        )

    def _on_login(self):
        username_or_email = self.username_or_email_input.text().strip()
        password = self.password_input.text()
        if not username_or_email or not password:
            QMessageBox.warning(
                self,
                "Missing fields",
                "Please enter your email or username and password.",
            )
            return

        ok, payload = verify_login_credentials(username_or_email, password)
        if ok:
            set_active_session(int(payload["id"]))
            if self.remember_checkbox.isChecked():
                self._settings.setValue("remember_username", True)
                self._settings.setValue("saved_username", username_or_email)
            else:
                self._settings.setValue("remember_username", False)
                self._settings.remove("saved_username")

            QMessageBox.information(
                self, "Welcome", f"Signed in as {payload['full_name']}."
            )
            self.login_success.emit(payload)
            self.close()
        else:
            QMessageBox.warning(self, "Sign in failed", str(payload))

    def _open_forgot_password(self):
        if self.forgot_password_window is None:
            self.forgot_password_window = ForgotPasswordWindow()
            self.forgot_password_window.back_to_login.connect(self._back_from_forgot_password)
        self.forgot_password_window.showNormal()
        self.forgot_password_window.raise_()
        self.forgot_password_window.activateWindow()
        self.hide()

    def _back_from_forgot_password(self):
        if self.forgot_password_window is not None:
            self.forgot_password_window.hide()
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.show()


class ForgotPasswordWindow(QWidget):
    back_to_login = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZIMON — Reset password")
        self.setFixedSize(FORGOT_WINDOW_W, FORGOT_WINDOW_H)
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("loginRootOuter")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(FORGOT_MARGIN_X, FORGOT_MARGIN_Y, FORGOT_MARGIN_X, FORGOT_MARGIN_Y)
        outer.setSpacing(0)

        card = LoginSplitContainer()
        card.setFixedSize(FORGOT_CARD_W, FORGOT_CARD_H)
        card_row = QHBoxLayout()
        card_row.addStretch(1)
        card_row.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)
        card_row.addStretch(1)
        outer.addLayout(card_row)

        shell = QHBoxLayout(card)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        left_panel = brand_hero_left_panel()
        left_panel.setMinimumWidth(FORGOT_CARD_W // 2)
        left_panel.setMaximumWidth(FORGOT_CARD_W // 2)
        shell.addWidget(left_panel, 1)

        right = LoginFormPanel()
        right.setMinimumWidth(FORGOT_CARD_W // 2)
        right.setMaximumWidth(FORGOT_CARD_W // 2)
        outer_rv = QVBoxLayout(right)
        outer_rv.setContentsMargins(0, 0, 0, 0)
        outer_rv.setSpacing(0)

        form_block = QWidget()
        form_block.setObjectName("loginFormBlock")
        form_block.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        rv = QVBoxLayout(form_block)
        rv.setContentsMargins(52, 52, 52, 38)
        rv.setSpacing(19)

        title = QLabel("Reset your password")
        title.setObjectName("loginWelcomeTitle")
        rv.addWidget(title)

        sub = QLabel(
            "Enter the email associated with your account. If it is registered, "
            "you will receive password reset instructions."
        )
        sub.setObjectName("loginWelcomeSub")
        sub.setWordWrap(True)
        rv.addWidget(sub)

        rv.addSpacing(5)

        em_label = QLabel("Email")
        em_label.setObjectName("loginFieldCaption")
        rv.addWidget(em_label)
        self._email_shell, self.email_input = styled_input_row(
            "✉", "Enter your email address"
        )
        rv.addWidget(self._email_shell)

        rv.addStretch(1)

        self.send_btn = QPushButton("Send reset link   →")
        self.send_btn.setObjectName("loginPrimaryBtn")
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setMinimumHeight(42)
        self.send_btn.setMaximumHeight(44)
        rv.addWidget(self.send_btn)

        self.back_btn = QPushButton("← Back to sign in")
        self.back_btn.setObjectName("loginForgotLink")
        self.back_btn.setFlat(True)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rv.addWidget(self.back_btn, 0, Qt.AlignmentFlag.AlignCenter)

        outer_rv.addWidget(form_block, 1)

        shell.addWidget(right, 1)
        shell.setStretch(0, 1)
        shell.setStretch(1, 1)

        self.setStyleSheet(AUTH_SHELL_QSS)

        self.send_btn.clicked.connect(self._send_reset_link)
        self.back_btn.clicked.connect(self.back_to_login.emit)

    def _send_reset_link(self):
        email = self.email_input.text().strip()
        if not email:
            QMessageBox.warning(self, "Missing email", "Please enter your email address.")
            return

        QMessageBox.information(
            self,
            "Success",
            "Email send Successfully",
        )
        self.back_to_login.emit()
