from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QSizePolicy,
    QMessageBox,
)

from database.auth import ROLE_ADMIN, ROLE_STUDENT, create_user


class RegisterWindow(QWidget):
    back_to_login = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZIMON - Register")
        self.setMinimumSize(560, 580)
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("registerRoot")
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
        layout.setSpacing(10)

        title = QLabel("Create Account")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Register to use ZIMON with your own account")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addWidget(self._field_label("Full Name"))
        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Full Name")
        self.full_name_input.setObjectName("fieldInput")
        layout.addWidget(self.full_name_input)

        layout.addWidget(self._field_label("Username"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setObjectName("fieldInput")
        layout.addWidget(self.username_input)

        layout.addWidget(self._field_label("Email"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setObjectName("fieldInput")
        layout.addWidget(self.email_input)

        layout.addWidget(self._field_label("Password"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("fieldInput")
        layout.addWidget(self.password_input)

        layout.addWidget(self._field_label("Confirm Password"))
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm Password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setObjectName("fieldInput")
        layout.addWidget(self.confirm_password_input)

        layout.addWidget(self._field_label("Role"))
        self.role_input = QComboBox()
        self.role_input.addItems(["user", "admin"])
        self.role_input.setObjectName("fieldInput")
        layout.addWidget(self.role_input)

        layout.addSpacing(24)

        row = QHBoxLayout()
        self.register_btn = QPushButton("Register")
        self.register_btn.setObjectName("primaryBtn")
        self.back_btn = QPushButton("Back to Login")
        self.back_btn.setObjectName("secondaryBtn")
        row.addWidget(self.register_btn)
        row.addWidget(self.back_btn)
        layout.addLayout(row)

        self.setStyleSheet(
            """
            QWidget#registerRoot {
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
            QLineEdit#fieldInput, QComboBox#fieldInput {
                min-height: 38px;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 0 10px;
                background-color: #0b1220;
                color: #f9fafb;
            }
            QLineEdit#fieldInput:focus, QComboBox#fieldInput:focus {
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

        self.register_btn.clicked.connect(self._on_register)
        self.back_btn.clicked.connect(self.back_to_login.emit)

    def _field_label(self, text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _on_register(self):
        full_name = self.full_name_input.text().strip()
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        role = self.role_input.currentText()

        if not full_name or not username or not email or not password:
            QMessageBox.warning(self, "Missing Fields", "Please fill all required fields.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Password Mismatch", "Password and confirm password do not match.")
            return

        role_norm = (role or "").strip().lower()
        db_role = ROLE_ADMIN if role_norm == "admin" else ROLE_STUDENT
        ok, result = create_user(full_name, username, email, password, db_role)
        if ok:
            QMessageBox.information(
                self, "Success", "Account created. You can sign in now."
            )
            self.back_to_login.emit()
        else:
            QMessageBox.warning(self, "Registration Failed", str(result))

