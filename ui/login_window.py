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
from ui.register_window import RegisterWindow


class LoginWindow(QWidget):
    login_success = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.register_window = None
        self.setWindowTitle("ZIMON - Login")
        self.setMinimumSize(520, 430)
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("loginRoot")
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(28, 28, 28, 28)

        card_row = QHBoxLayout()
        root_layout.addLayout(card_row)

        card = QFrame()
        card.setObjectName("authCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card_row.addStretch()
        card_row.addWidget(card, 1)
        card_row.addStretch()

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("ZIMON Login")
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
        self.create_account_btn = QPushButton("Create Account")
        self.create_account_btn.setObjectName("secondaryBtn")
        layout.addWidget(self.login_btn)
        layout.addWidget(self.create_account_btn)

        self.setStyleSheet(
            """
            QWidget#loginRoot {
                background-color: #0f172a;
            }
            QFrame#authCard {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 14px;
            }
            QLabel#titleLabel {
                color: #f9fafb;
                font-size: 24px;
                font-weight: 700;
                padding-bottom: 2px;
            }
            QLabel#subtitleLabel {
                color: #9ca3af;
                font-size: 13px;
                padding-bottom: 4px;
            }
            QLabel#fieldLabel {
                color: #d1d5db;
                font-size: 12px;
                font-weight: 600;
            }
            QLineEdit#fieldInput {
                min-height: 38px;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 0 10px;
                background-color: #0b1220;
                color: #f9fafb;
            }
            QLineEdit#fieldInput:focus {
                border: 1px solid #60a5fa;
            }
            QPushButton#primaryBtn {
                min-height: 38px;
                border-radius: 8px;
                border: none;
                font-weight: 700;
                color: white;
                background-color: #2563eb;
            }
            QPushButton#primaryBtn:hover {
                background-color: #1d4ed8;
            }
            QPushButton#secondaryBtn {
                min-height: 38px;
                border-radius: 8px;
                font-weight: 600;
                color: #dbeafe;
                border: 1px solid #3b82f6;
                background-color: transparent;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #1e3a8a;
            }
            """
        )

        self.login_btn.clicked.connect(self._on_login)
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

        self.register_window.show()
        self.hide()

    def _back_from_register(self):
        if self.register_window is not None:
            self.register_window.hide()
        self.show()

