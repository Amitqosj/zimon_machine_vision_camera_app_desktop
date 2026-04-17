"""ZIMON PyQt login — split branding / form layout using assets from gui/images."""

from __future__ import annotations

from pathlib import Path
import re
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import parse_qs, urlparse

import requests
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

# ---------------- Forgot-password integration placeholders ----------------
# Replace these values in your environment before production use.
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "thakuramitsingh165@gmail.com"
SMTP_PASSWORD = "abbg ktau iifa rjxk"
FROM_EMAIL = "thakuramitsingh165@gmail.com"

# Reset link and password update endpoint placeholders.
# You can keep custom scheme for desktop deep links or use your HTTPS domain.
RESET_LINK_BASE = "myapp://reset-password"
RESET_PASSWORD_API_ENDPOINT = "https://yourdomain.com/api/users/reset-password"

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


def _is_valid_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()))


def _extract_token_from_link(link: str) -> str:
    try:
        parsed = urlparse(link.strip())
        values = parse_qs(parsed.query)
        token = values.get("token", [""])[0].strip()
        return token
    except Exception:
        return ""


def _build_reset_link(token: str) -> str:
    base = RESET_LINK_BASE.rstrip("/")
    if base.startswith("myapp://"):
        return f"{base}?token={token}"
    return f"{base}/reset-password?token={token}"


def _send_password_reset_email(target_email: str, reset_link: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "ZIMON Password Reset"
    msg["From"] = FROM_EMAIL
    msg["To"] = target_email

    plain = (
        "You requested a password reset for your ZIMON account.\n\n"
        f"Open this link to continue:\n{reset_link}\n\n"
        "If you did not request this, you can ignore this email."
    )
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #dbeafe; background: #0b1324;">
        <p>You requested a password reset for your ZIMON account.</p>
        <p>
          <a href="{reset_link}" style="color: #38bdf8;">Reset your password</a>
        </p>
        <p>If you did not request this, you can ignore this email.</p>
      </body>
    </html>
    """

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, [target_email], msg.as_string())


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
        self.reset_password_window = None
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
            self.forgot_password_window.open_reset_link.connect(
                self._open_reset_password_from_link
            )
        self.forgot_password_window.showNormal()
        self.forgot_password_window.raise_()
        self.forgot_password_window.activateWindow()
        self.hide()

    def _open_reset_password_from_link(self, link: str):
        token = _extract_token_from_link(link)
        if not token:
            QMessageBox.warning(
                self,
                "Invalid reset link",
                "Could not read a token from the reset link.",
            )
            return
        if self.reset_password_window is None:
            self.reset_password_window = ResetPasswordWindow()
            self.reset_password_window.back_to_login.connect(
                self._back_from_reset_password
            )
        self.reset_password_window.set_token(token)
        self.reset_password_window.showNormal()
        self.reset_password_window.raise_()
        self.reset_password_window.activateWindow()
        if self.forgot_password_window is not None:
            self.forgot_password_window.hide()
        self.hide()

    def _back_from_forgot_password(self):
        if self.forgot_password_window is not None:
            self.forgot_password_window.hide()
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.show()

    def _back_from_reset_password(self):
        if self.reset_password_window is not None:
            self.reset_password_window.hide()
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.show()


FORGOT_RESET_QSS = """
QWidget#forgotRoot {
    background-color: #040a16;
}
QFrame#forgotCard {
    background-color: #081523;
    border: 1px solid rgba(0, 170, 255, 0.28);
    border-radius: 18px;
}
QLabel#forgotTitle {
    color: #eaf4ff;
    font-size: 26px;
    font-weight: 800;
}
QLabel#forgotSub {
    color: #9fb5d3;
    font-size: 13px;
}
QLabel#forgotLabel {
    color: #cfe8ff;
    font-size: 12px;
    font-weight: 700;
}
QLineEdit#forgotInput {
    background-color: #050b18;
    color: #eaf4ff;
    border: 1px solid rgba(0, 170, 255, 0.22);
    border-radius: 10px;
    min-height: 40px;
    padding: 0 12px;
}
QLineEdit#forgotInput:focus {
    border: 1px solid rgba(30, 167, 255, 0.75);
}
QPushButton#forgotPrimary {
    background-color: rgba(30, 167, 255, 0.18);
    color: #eaf4ff;
    border: 1px solid rgba(30, 167, 255, 0.58);
    border-radius: 11px;
    min-height: 40px;
    font-weight: 700;
}
QPushButton#forgotPrimary:hover {
    background-color: rgba(30, 167, 255, 0.26);
}
QPushButton#forgotSecondary {
    background-color: transparent;
    color: #7dd3fc;
    border: 1px solid rgba(30, 167, 255, 0.32);
    border-radius: 11px;
    min-height: 40px;
    font-weight: 700;
}
QPushButton#forgotSecondary:hover {
    background-color: rgba(30, 167, 255, 0.12);
}
"""


class ForgotPasswordWindow(QWidget):
    back_to_login = pyqtSignal()
    open_reset_link = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZIMON — Forgot Password")
        self.setFixedSize(640, 420)
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("forgotRoot")
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 24, 26, 24)
        root.setSpacing(0)

        card = QFrame()
        card.setObjectName("forgotCard")
        root.addWidget(card, 1)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        title = QLabel("Forgot Password")
        title.setObjectName("forgotTitle")
        sub = QLabel(
            "Enter your registered email to receive a password reset link."
        )
        sub.setObjectName("forgotSub")
        sub.setWordWrap(True)
        lay.addWidget(title)
        lay.addWidget(sub)

        lbl_email = QLabel("Registered Email")
        lbl_email.setObjectName("forgotLabel")
        lay.addWidget(lbl_email)

        self.email_input = QLineEdit()
        self.email_input.setObjectName("forgotInput")
        self.email_input.setPlaceholderText("name@example.com")
        lay.addWidget(self.email_input)

        lbl_link = QLabel("Reset Link (paste from email)")
        lbl_link.setObjectName("forgotLabel")
        lay.addWidget(lbl_link)

        self.link_input = QLineEdit()
        self.link_input.setObjectName("forgotInput")
        self.link_input.setPlaceholderText("myapp://reset-password?token=...")
        lay.addWidget(self.link_input)
        lay.addStretch(1)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.send_btn = QPushButton("Send Reset Link")
        self.send_btn.setObjectName("forgotPrimary")
        self.open_btn = QPushButton("Open Link")
        self.open_btn.setObjectName("forgotSecondary")
        self.back_btn = QPushButton("Back to Login")
        self.back_btn.setObjectName("forgotSecondary")
        row.addWidget(self.send_btn)
        row.addWidget(self.open_btn)
        row.addWidget(self.back_btn)
        lay.addLayout(row)

        self.send_btn.clicked.connect(self._send_reset_link)
        self.open_btn.clicked.connect(self._open_link_from_input)
        self.back_btn.clicked.connect(self.back_to_login.emit)
        self.setStyleSheet(FORGOT_RESET_QSS)

    def _send_reset_link(self):
        email = self.email_input.text().strip()
        if not email:
            QMessageBox.warning(self, "Missing email", "Email is required.")
            return
        if not _is_valid_email(email):
            QMessageBox.warning(self, "Invalid email", "Please enter a valid email address.")
            return

        token = secrets.token_urlsafe(24)
        reset_link = _build_reset_link(token)
        try:
            _send_password_reset_email(email, reset_link)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Email send failed",
                f"Could not send reset email.\n\n{exc}",
            )
            return

        self.link_input.setText(reset_link)
        QMessageBox.information(
            self,
            "Reset Link Sent",
            "Password reset link sent successfully. Check your email and open the link.",
        )

    def _open_link_from_input(self):
        link = self.link_input.text().strip()
        if not link:
            QMessageBox.warning(self, "Missing link", "Paste the reset link from your email.")
            return
        self.open_reset_link.emit(link)


class ResetPasswordWindow(QWidget):
    back_to_login = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._token = ""
        self.setWindowTitle("ZIMON — Create New Password")
        self.setFixedSize(640, 420)
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("forgotRoot")
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 24, 26, 24)
        root.setSpacing(0)

        card = QFrame()
        card.setObjectName("forgotCard")
        root.addWidget(card, 1)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        title = QLabel("Create New Password")
        title.setObjectName("forgotTitle")
        sub = QLabel("Enter and confirm your new password.")
        sub.setObjectName("forgotSub")
        lay.addWidget(title)
        lay.addWidget(sub)

        token_lbl = QLabel("Reset Token")
        token_lbl.setObjectName("forgotLabel")
        lay.addWidget(token_lbl)
        self.token_input = QLineEdit()
        self.token_input.setObjectName("forgotInput")
        self.token_input.setPlaceholderText("Auto-filled from reset link")
        lay.addWidget(self.token_input)

        pw_lbl = QLabel("New Password")
        pw_lbl.setObjectName("forgotLabel")
        lay.addWidget(pw_lbl)
        self.new_password_input = QLineEdit()
        self.new_password_input.setObjectName("forgotInput")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addWidget(self.new_password_input)

        cpw_lbl = QLabel("Confirm Password")
        cpw_lbl.setObjectName("forgotLabel")
        lay.addWidget(cpw_lbl)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setObjectName("forgotInput")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addWidget(self.confirm_password_input)
        lay.addStretch(1)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.update_btn = QPushButton("Update Password")
        self.update_btn.setObjectName("forgotPrimary")
        self.back_btn = QPushButton("Back to Login")
        self.back_btn.setObjectName("forgotSecondary")
        row.addWidget(self.update_btn)
        row.addWidget(self.back_btn)
        lay.addLayout(row)

        self.update_btn.clicked.connect(self._update_password)
        self.back_btn.clicked.connect(self.back_to_login.emit)
        self.setStyleSheet(FORGOT_RESET_QSS)

    def set_token(self, token: str):
        self._token = token.strip()
        self.token_input.setText(self._token)

    def _update_password(self):
        token = self.token_input.text().strip() or self._token
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not token:
            QMessageBox.warning(self, "Missing token", "Reset token is required.")
            return
        if not new_password:
            QMessageBox.warning(self, "Missing password", "New password is required.")
            return
        if not confirm_password:
            QMessageBox.warning(self, "Missing confirm password", "Please confirm your password.")
            return
        if len(new_password) < 8:
            QMessageBox.warning(self, "Weak password", "Password must be at least 8 characters.")
            return
        if new_password != confirm_password:
            QMessageBox.warning(self, "Password mismatch", "Passwords do not match.")
            return

        payload = {"token": token, "password": new_password}
        try:
            response = requests.patch(
                RESET_PASSWORD_API_ENDPOINT,
                json=payload,
                timeout=15,
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Reset failed",
                f"Could not reach reset password API.\n\n{exc}",
            )
            return

        if 200 <= response.status_code < 300:
            QMessageBox.information(
                self,
                "Success",
                "Password updated successfully",
            )
            self.new_password_input.clear()
            self.confirm_password_input.clear()
            self.back_to_login.emit()
            return

        err = response.text.strip() or "Reset password request failed."
        QMessageBox.critical(self, "Reset failed", err)
