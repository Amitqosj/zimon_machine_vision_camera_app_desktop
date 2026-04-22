from __future__ import annotations

import re
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)
from database.db import get_connection


class FeedbackSupportDialog(QDialog):
    """Collect and persist user feedback in PostgreSQL."""

    _EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Feedback & Support")
        self.setObjectName("FeedbackSupportDialog")
        self.setModal(True)
        self.setMinimumWidth(540)
        self.setMinimumHeight(430)
        self.resize(620, 460)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        title = QLabel("Feedback & Support")
        title.setObjectName("FeedbackSupportTitle")
        subtitle = QLabel("Share a bug, request, or suggestion with the ZIMON team.")
        subtitle.setObjectName("FeedbackSupportSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        form = QFormLayout()
        form.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full Name (optional)")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email (optional)")

        self.category_input = QComboBox()
        self.category_input.addItems(
            [
                "Bug Report",
                "Feature Request",
                "General Feedback",
                "Suggestion",
            ]
        )

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Describe your feedback or support request…")
        self.message_input.setMinimumHeight(170)

        form.addRow("Full Name", self.name_input)
        form.addRow("Email", self.email_input)
        form.addRow("Category", self.category_input)
        form.addRow("Message*", self.message_input)
        root.addLayout(form, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch(1)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("ZBtnOutline")
        self.cancel_btn.clicked.connect(self.reject)

        self.submit_btn = QPushButton("Submit")
        self.submit_btn.setObjectName("ZBtnGhost")
        self.submit_btn.clicked.connect(self._submit_feedback)

        btn_row.addWidget(self.cancel_btn)
        btn_row.addWidget(self.submit_btn)
        root.addLayout(btn_row)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        parent = self.parentWidget()
        if parent is not None:
            parent_center = parent.frameGeometry().center()
            frame = self.frameGeometry()
            frame.moveCenter(parent_center)
            self.move(frame.topLeft())

    def _validate(self) -> tuple[bool, str]:
        message = self.message_input.toPlainText().strip()
        if not message:
            return False, "Message is required."

        email = self.email_input.text().strip()
        if email and not self._EMAIL_RE.match(email):
            return False, "Please enter a valid email address."

        return True, ""

    def _ensure_feedback_table(self, conn) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id BIGSERIAL PRIMARY KEY,
                name TEXT,
                email TEXT,
                category TEXT,
                message TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

    def _submit_feedback(self) -> None:
        ok, error = self._validate()
        if not ok:
            QMessageBox.warning(self, "Feedback & Support", error)
            return

        payload = {
            "name": self.name_input.text().strip(),
            "email": self.email_input.text().strip(),
            "category": self.category_input.currentText().strip(),
            "message": self.message_input.toPlainText().strip(),
            "created_at": datetime.utcnow().isoformat(timespec="seconds"),
        }

        try:
            with get_connection() as conn:
                self._ensure_feedback_table(conn)
                conn.execute(
                    """
                    INSERT INTO feedback (name, email, category, message, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        payload["name"],
                        payload["email"],
                        payload["category"],
                        payload["message"],
                        payload["created_at"],
                    ),
                )
                conn.commit()
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Feedback & Support",
                f"Failed to submit feedback.\n\n{exc}",
            )
            return

        self._clear_form()
        QMessageBox.information(
            self,
            "Feedback & Support",
            "Thanks for your feedback. It has been submitted successfully.",
        )
        self.accept()

    def _clear_form(self) -> None:
        self.name_input.clear()
        self.email_input.clear()
        self.category_input.setCurrentIndex(0)
        self.message_input.clear()
