from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QMessageBox,
)

from database.auth import login_user
from gui.register_window import RegisterWindow


class LoginWindow(QWidget):
    login_success = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.register_window = None
        self.forgot_password_window = None
        self.setWindowTitle("ZIMON - Login")
        self.setFixedSize(820, 760)
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("loginRoot")
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(0)

        card_row = QHBoxLayout()
        root_layout.addLayout(card_row)

        card = QFrame()
        card.setObjectName("authCard")
        card.setMinimumWidth(620)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card_row.addStretch()
        card_row.addWidget(card, 1)
        card_row.addStretch()

        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        brand_row = QHBoxLayout()
        brand_badge = QLabel("🧬")
        brand_badge.setObjectName("brandBadge")
        brand_name = QLabel("ZIMON")
        brand_name.setObjectName("brandTitle")
        brand_row.addWidget(brand_badge)
        brand_row.addWidget(brand_name)
        brand_row.addStretch(1)
        layout.addLayout(brand_row)

        brand_tagline = QLabel("Behavior Tracking System")
        brand_tagline.setObjectName("brandTagline")
        layout.addWidget(brand_tagline)

        title = QLabel("Welcome back")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Sign in to access the behavior tracking dashboard")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        user_label = QLabel("Username or Email")
        user_label.setObjectName("fieldLabel")
        layout.addWidget(user_label)
        self.username_or_email_input = QLineEdit()
        self.username_or_email_input.setPlaceholderText("Username or Email")
        self.username_or_email_input.setObjectName("fieldInput")
        layout.addWidget(self.username_or_email_input)

        pass_label = QLabel("Password")
        pass_label.setObjectName("fieldLabel")
        layout.addWidget(pass_label)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("fieldInput")
        layout.addWidget(self.password_input)

        layout.addStretch(1)

        self.login_btn = QPushButton("Login")
        self.login_btn.setObjectName("primaryBtn")
        self.forgot_password_btn = QPushButton("Forgot Password?")
        self.forgot_password_btn.setObjectName("secondaryBtn")
        self.create_account_btn = QPushButton("Create Account")
        self.create_account_btn.setObjectName("secondaryBtn")
        layout.addWidget(self.login_btn)
        layout.addWidget(self.forgot_password_btn)
        layout.addWidget(self.create_account_btn)

        self.setStyleSheet(
            """
            QWidget#loginRoot { background-color: #0f172a; }
            QFrame#authCard { background-color: #111827; border: 1px solid #1f2937; border-radius: 14px; }
            QLabel#titleLabel { color: #f9fafb; font-size: 24px; font-weight: 700; padding-bottom: 2px; }
            QLabel#brandBadge {
                min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px;
                border-radius: 17px; color: white; font-size: 18px; font-weight: 800;
                background-color: #2563eb; qproperty-alignment: AlignCenter;
            }
            QLabel#brandTitle { color: #93c5fd; font-size: 28px; font-weight: 900; letter-spacing: 1px; padding-left: 10px; }
            QLabel#brandTagline { color: #cbd5e1; font-size: 13px; padding-bottom: 14px; }
            QLabel#subtitleLabel { color: #9ca3af; font-size: 13px; padding-bottom: 4px; }
            QLabel#fieldLabel { color: #d1d5db; font-size: 12px; font-weight: 600; }
            QLineEdit#fieldInput {
                min-height: 38px; border: 1px solid #374151; border-radius: 8px; padding: 0 10px;
                background-color: #0b1220; color: #f9fafb;
            }
            QLineEdit#fieldInput:focus { border: 1px solid #60a5fa; }
            QPushButton#primaryBtn {
                min-height: 38px; border-radius: 8px; border: none; font-weight: 700; color: white;
                background-color: #2563eb;
            }
            QPushButton#primaryBtn:hover { background-color: #1d4ed8; }
            QPushButton#secondaryBtn {
                min-height: 38px; border-radius: 8px; font-weight: 600; color: #dbeafe;
                border: 1px solid #3b82f6; background-color: transparent;
            }
            QPushButton#secondaryBtn:hover { background-color: #1e3a8a; }
            """
        )

        self.login_btn.clicked.connect(self._on_login)
        self.forgot_password_btn.clicked.connect(self._open_forgot_password)
        self.create_account_btn.clicked.connect(self._open_register)

    def _on_login(self):
        username_or_email = self.username_or_email_input.text().strip()
        password = self.password_input.text()
        if not username_or_email or not password:
            QMessageBox.warning(self, "Missing Fields", "Please enter username/email and password.")
            return

        ok, payload = login_user(username_or_email, password)
        if ok:
            QMessageBox.information(self, "Login Successful", f"Welcome, {payload['full_name']}")
            self.login_success.emit(payload)
            self.close()
        else:
            QMessageBox.warning(self, "Login Failed", str(payload))

    def _open_register(self):
        if self.register_window is None:
            self.register_window = RegisterWindow()
            self.register_window.back_to_login.connect(self._back_from_register)
        self.register_window.showNormal()
        self.register_window.raise_()
        self.register_window.activateWindow()
        self.hide()

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

    def _back_from_register(self):
        if self.register_window is not None:
            self.register_window.hide()
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.show()


class ForgotPasswordWindow(QWidget):
    back_to_login = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZIMON - Reset Password")
        self.setFixedSize(760, 460)
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("forgotRoot")
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(0)

        card_row = QHBoxLayout()
        root_layout.addLayout(card_row)

        card = QFrame()
        card.setObjectName("authCard")
        card.setMinimumWidth(620)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card_row.addStretch()
        card_row.addWidget(card, 1)
        card_row.addStretch()

        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)

        brand_row = QHBoxLayout()
        brand_badge = QLabel("🧬")
        brand_badge.setObjectName("brandBadge")
        brand_name = QLabel("ZIMON")
        brand_name.setObjectName("brandTitle")
        brand_row.addWidget(brand_badge)
        brand_row.addWidget(brand_name)
        brand_row.addStretch(1)
        layout.addLayout(brand_row)

        description = QLabel("Enter the email to receive the password reset link")
        description.setObjectName("brandTagline")
        layout.addWidget(description)

        title = QLabel("Password Reset")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        email_label = QLabel("Email")
        email_label.setObjectName("fieldLabel")
        layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setObjectName("fieldInput")
        layout.addWidget(self.email_input)

        layout.addSpacing(18)
        layout.addStretch(3)

        row = QHBoxLayout()
        self.send_btn = QPushButton("Send Reset Link")
        self.send_btn.setObjectName("primaryBtn")
        self.back_btn = QPushButton("Back to Login")
        self.back_btn.setObjectName("secondaryBtn")
        row.addWidget(self.send_btn)
        row.addWidget(self.back_btn)
        layout.addLayout(row)

        self.setStyleSheet(
            """
            QWidget#forgotRoot { background-color: #0f172a; }
            QFrame#authCard { background-color: #111827; border: 1px solid #1f2937; border-radius: 14px; }
            QLabel#titleLabel { color: #f9fafb; font-size: 24px; font-weight: 700; padding-bottom: 2px; }
            QLabel#brandBadge {
                min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px;
                border-radius: 17px; color: white; font-size: 18px; font-weight: 800;
                background-color: #2563eb; qproperty-alignment: AlignCenter;
            }
            QLabel#brandTitle { color: #93c5fd; font-size: 28px; font-weight: 900; letter-spacing: 1px; padding-left: 10px; }
            QLabel#brandTagline { color: #cbd5e1; font-size: 13px; padding-bottom: 14px; }
            QLabel#subtitleLabel { color: #9ca3af; font-size: 13px; padding-bottom: 4px; }
            QLabel#fieldLabel { color: #d1d5db; font-size: 12px; font-weight: 600; }
            QLineEdit#fieldInput {
                min-height: 38px; border: 1px solid #374151; border-radius: 8px; padding: 0 10px;
                background-color: #0b1220; color: #f9fafb;
            }
            QLineEdit#fieldInput:focus { border: 1px solid #60a5fa; }
            QPushButton#primaryBtn {
                min-height: 38px; border-radius: 8px; border: none; font-weight: 700; color: white;
                background-color: #2563eb;
            }
            QPushButton#primaryBtn:hover { background-color: #1d4ed8; }
            QPushButton#secondaryBtn {
                min-height: 38px; border-radius: 8px; font-weight: 600; color: #dbeafe;
                border: 1px solid #3b82f6; background-color: transparent;
            }
            QPushButton#secondaryBtn:hover { background-color: #1e3a8a; }
            """
        )

        self.send_btn.clicked.connect(self._send_reset_link)
        self.back_btn.clicked.connect(self.back_to_login.emit)

    def _send_reset_link(self):
        email = self.email_input.text().strip()
        if not email:
            QMessageBox.warning(self, "Missing Email", "Please enter your email address.")
            return

        QMessageBox.information(
            self,
            "Reset Link Sent",
            "If this email is registered, a password reset link will be sent."
        )
        self.back_to_login.emit()

