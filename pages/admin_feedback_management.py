from __future__ import annotations

import csv
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from database.db import get_connection


class AdminFeedbackManagementDialog(QDialog):
    """Admin screen for viewing and managing submitted feedback."""

    COLUMNS = ["ID", "Name", "Email", "Category", "Message", "Date"]
    CATEGORIES = [
        "All",
        "Bug Report",
        "Feature Request",
        "General Feedback",
        "Suggestion",
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Feedback Management")
        self.setObjectName("AdminFeedbackDialog")
        self.resize(1220, 760)
        self.setMinimumSize(980, 620)
        self.setModal(True)

        self._all_feedback: list[dict[str, str]] = []
        self._current_feedback: list[dict[str, str]] = []
        self._reviewed_ids: set[int] = set()
        self._build_ui()
        self._load_feedback()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QFrame()
        header.setObjectName("ZPanel")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(14, 12, 14, 12)
        header_layout.setSpacing(10)

        title = QLabel("Feedback Management")
        title.setObjectName("ZCardTitle")
        subtitle = QLabel("View and manage user feedback submissions.")
        subtitle.setObjectName("ZCardSubtitle")
        subtitle.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        top_controls = QHBoxLayout()
        top_controls.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, email, or message...")
        self.search_input.textChanged.connect(self._apply_filters)
        top_controls.addWidget(self.search_input, 1)

        self.category_filter = QComboBox()
        self.category_filter.addItems(self.CATEGORIES)
        self.category_filter.currentTextChanged.connect(self._apply_filters)
        top_controls.addWidget(self.category_filter, 0)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("ZBtnOutline")
        self.refresh_btn.clicked.connect(self._load_feedback)
        top_controls.addWidget(self.refresh_btn, 0)

        header_layout.addLayout(top_controls)
        root.addWidget(header, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(7)

        left_panel = QFrame()
        left_panel.setObjectName("ZCard")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setObjectName("AdminFeedbackTable")
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setWordWrap(False)
        self.table.setSortingEnabled(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.itemSelectionChanged.connect(self._sync_detail_panel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)

        header_view = self.table.horizontalHeader()
        header_view.setStretchLastSection(False)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        left_layout.addWidget(self.table, 1)
        splitter.addWidget(left_panel)

        right_panel = QFrame()
        right_panel.setObjectName("ZCard")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(14, 12, 14, 12)
        right_layout.setSpacing(10)

        detail_title = QLabel("Selected Feedback")
        detail_title.setObjectName("SectionTitle")
        right_layout.addWidget(detail_title)

        detail_grid = QGridLayout()
        detail_grid.setHorizontalSpacing(10)
        detail_grid.setVerticalSpacing(8)

        self.detail_name = QLineEdit()
        self.detail_name.setReadOnly(True)
        self.detail_email = QLineEdit()
        self.detail_email.setReadOnly(True)
        self.detail_category = QLineEdit()
        self.detail_category.setReadOnly(True)
        self.detail_date = QLineEdit()
        self.detail_date.setReadOnly(True)
        self.detail_message = QTextEdit()
        self.detail_message.setReadOnly(True)
        self.detail_message.setMinimumHeight(260)

        detail_grid.addWidget(QLabel("Full Name"), 0, 0)
        detail_grid.addWidget(self.detail_name, 0, 1)
        detail_grid.addWidget(QLabel("Email"), 1, 0)
        detail_grid.addWidget(self.detail_email, 1, 1)
        detail_grid.addWidget(QLabel("Category"), 2, 0)
        detail_grid.addWidget(self.detail_category, 2, 1)
        detail_grid.addWidget(QLabel("Submitted Date"), 3, 0)
        detail_grid.addWidget(self.detail_date, 3, 1)
        detail_grid.addWidget(QLabel("Full Message"), 4, 0, Qt.AlignmentFlag.AlignTop)
        detail_grid.addWidget(self.detail_message, 4, 1)

        right_layout.addLayout(detail_grid)
        right_layout.addStretch(1)
        splitter.addWidget(right_panel)
        splitter.setSizes([770, 430])

        root.addWidget(splitter, 1)

        actions = QWidget()
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setObjectName("ZBtnDanger")
        self.delete_btn.clicked.connect(self._delete_selected)

        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setObjectName("ZBtnGhost")
        self.export_btn.clicked.connect(self._export_csv)

        self.review_btn = QPushButton("Mark Reviewed")
        self.review_btn.setObjectName("ZBtnOutline")
        self.review_btn.clicked.connect(self._mark_reviewed)

        self.close_btn = QPushButton("Close")
        self.close_btn.setObjectName("ZBtnOutline")
        self.close_btn.clicked.connect(self.accept)

        actions_layout.addWidget(self.delete_btn)
        actions_layout.addWidget(self.export_btn)
        actions_layout.addWidget(self.review_btn)
        actions_layout.addStretch(1)
        actions_layout.addWidget(self.close_btn)
        root.addWidget(actions, 0)

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

    def _load_feedback(self) -> None:
        try:
            with get_connection() as conn:
                self._ensure_feedback_table(conn)
                cursor = conn.execute(
                    """
                    SELECT id, name, email, category, message, created_at
                    FROM feedback
                    ORDER BY id DESC
                    """
                )
                rows = cursor.fetchall()
        except Exception as exc:
            QMessageBox.critical(self, "Feedback Management", f"Failed to load feedback.\n\n{exc}")
            return

        self._all_feedback = [
            {
                "id": int(row[0]),
                "name": str(row[1] or ""),
                "email": str(row[2] or ""),
                "category": str(row[3] or ""),
                "message": str(row[4] or ""),
                "created_at": str(row[5] or ""),
            }
            for row in rows
        ]
        self._apply_filters()

    def _apply_filters(self) -> None:
        query = self.search_input.text().strip().lower()
        selected_category = self.category_filter.currentText()

        self._current_feedback = []
        for item in self._all_feedback:
            if selected_category != "All" and item["category"] != selected_category:
                continue
            searchable = " ".join([item["name"], item["email"], item["message"]]).lower()
            if query and query not in searchable:
                continue
            self._current_feedback.append(item)

        self._render_table()

    def _render_table(self) -> None:
        self.table.setRowCount(len(self._current_feedback))
        for row_idx, item in enumerate(self._current_feedback):
            values = [
                str(item["id"]),
                item["name"] or "—",
                item["email"] or "—",
                item["category"] or "—",
                self._message_preview(item["message"]),
                item["created_at"] or "—",
            ]
            for col_idx, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if col_idx == 0:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if int(item["id"]) in self._reviewed_ids:
                    cell.setForeground(Qt.GlobalColor.darkGray)
                self.table.setItem(row_idx, col_idx, cell)

        if self._current_feedback:
            self.table.selectRow(0)
        else:
            self._clear_details()

    def _message_preview(self, message: str) -> str:
        compact = " ".join(message.split())
        if len(compact) <= 90:
            return compact or "—"
        return compact[:87].rstrip() + "..."

    def _selected_item(self) -> dict[str, str] | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._current_feedback):
            return None
        return self._current_feedback[row]

    def _sync_detail_panel(self) -> None:
        selected = self._selected_item()
        if not selected:
            self._clear_details()
            return
        self.detail_name.setText(selected["name"] or "—")
        self.detail_email.setText(selected["email"] or "—")
        self.detail_category.setText(selected["category"] or "—")
        self.detail_date.setText(selected["created_at"] or "—")
        self.detail_message.setPlainText(selected["message"] or "")

    def _clear_details(self) -> None:
        self.detail_name.clear()
        self.detail_email.clear()
        self.detail_category.clear()
        self.detail_date.clear()
        self.detail_message.clear()

    def _delete_selected(self) -> None:
        selected = self._selected_item()
        if not selected:
            QMessageBox.information(self, "Feedback Management", "Please select a feedback row first.")
            return
        confirm = QMessageBox.question(
            self,
            "Delete Feedback",
            f"Delete feedback ID #{selected['id']}?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            with get_connection() as conn:
                conn.execute("DELETE FROM feedback WHERE id = %s", (selected["id"],))
                conn.commit()
        except Exception as exc:
            QMessageBox.critical(self, "Feedback Management", f"Failed to delete feedback.\n\n{exc}")
            return

        self._load_feedback()

    def _export_csv(self) -> None:
        if not self._current_feedback:
            QMessageBox.information(self, "Feedback Management", "No feedback rows to export.")
            return
        default_path = str(Path.home() / "zimon_feedback_export.csv")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Feedback to CSV",
            default_path,
            "CSV Files (*.csv)",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["id", "name", "email", "category", "message", "created_at"])
                for item in self._current_feedback:
                    writer.writerow(
                        [
                            item["id"],
                            item["name"],
                            item["email"],
                            item["category"],
                            item["message"],
                            item["created_at"],
                        ]
                    )
        except Exception as exc:
            QMessageBox.critical(self, "Feedback Management", f"Failed to export CSV.\n\n{exc}")
            return

        QMessageBox.information(self, "Feedback Management", f"Exported {len(self._current_feedback)} row(s).")

    def _mark_reviewed(self) -> None:
        selected = self._selected_item()
        if not selected:
            QMessageBox.information(self, "Feedback Management", "Please select a feedback row first.")
            return
        self._reviewed_ids.add(int(selected["id"]))
        self._render_table()
