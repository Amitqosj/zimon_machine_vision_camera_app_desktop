"""Presets management: save analysis paths per user and apply to Data tab."""

import logging
import os
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QHeaderView,
)

from database import presets as presets_db

logger = logging.getLogger("presets_tab")


class PresetsTab(QWidget):
    def __init__(self, main_window, user_id: Optional[int] = None):
        super().__init__()
        self.main_window = main_window
        self.user_id = user_id
        self._editing_preset_id: Optional[int] = None
        self._build_ui()
        if self.user_id is not None:
            self._reload_table()
        else:
            self._set_form_enabled(False)

    def refresh_for_user(self, user_id: Optional[int]):
        """Call after login / relogin when user id may change."""
        self.user_id = user_id
        self._login_hint.setVisible(user_id is None)
        self._set_form_enabled(user_id is not None)
        self._new_preset()
        if user_id is not None:
            self._reload_table()
        else:
            self.table.setRowCount(0)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(
            """
            QScrollArea { border: none; background: transparent; }
            QScrollArea > QWidget > QWidget { background: #1a1d23; }
            """
        )

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(14)

        header = QLabel("Presets")
        header.setStyleSheet(
            "font-size: 18px; font-weight: 600; color: #e8e9ea; padding: 8px 0px;"
        )
        inner_layout.addWidget(header)

        self._login_hint = QLabel(
            "Log in to create and manage presets. Presets store video, ZebraZoom config, "
            "and output folder for quick use on the Data tab."
        )
        self._login_hint.setWordWrap(True)
        self._login_hint.setStyleSheet(
            "color: #fbbf24; font-size: 12px; padding: 12px; background: #2a2d36; "
            "border-radius: 8px; border: 1px solid #fbbf24;"
        )
        self._login_hint.setVisible(self.user_id is None)
        inner_layout.addWidget(self._login_hint)

        list_box = QGroupBox("Saved presets")
        list_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        list_layout = QVBoxLayout(list_box)
        list_layout.setContentsMargins(16, 20, 16, 16)
        list_layout.setSpacing(10)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Video", "Output", "Created"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setMinimumHeight(180)
        self.table.itemSelectionChanged.connect(self._on_table_selection)
        list_layout.addWidget(self.table)

        row_btns = QHBoxLayout()
        row_btns.addStretch()
        self.new_btn = QPushButton("New")
        self.new_btn.clicked.connect(self._new_preset)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_preset)
        self.apply_btn = QPushButton("Apply to Data")
        self.apply_btn.clicked.connect(self._apply_to_data)
        row_btns.addWidget(self.new_btn)
        row_btns.addWidget(self.delete_btn)
        row_btns.addWidget(self.apply_btn)
        list_layout.addLayout(row_btns)

        inner_layout.addWidget(list_box)

        form_box = QGroupBox("Preset details")
        form_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        form_layout = QVBoxLayout(form_box)
        form_layout.setContentsMargins(16, 20, 16, 16)
        form_layout.setSpacing(10)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Standard 5dpf tracking")
        name_row.addWidget(self.name_edit, 1)
        form_layout.addLayout(name_row)

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Optional description…")
        self.desc_edit.setMaximumHeight(72)
        form_layout.addWidget(QLabel("Description:"))
        form_layout.addWidget(self.desc_edit)

        self._path_row(form_layout, "Video:", "video_path_label", "video_btn", self._pick_video)
        self._path_row(form_layout, "Config:", "config_path_label", "config_btn", self._pick_config)
        self._path_row(form_layout, "Output:", "output_path_label", "output_btn", self._pick_output)

        save_row = QHBoxLayout()
        save_row.addStretch()
        self.save_btn = QPushButton("Save preset")
        self.save_btn.clicked.connect(self._save_preset)
        save_row.addWidget(self.save_btn)
        form_layout.addLayout(save_row)

        inner_layout.addWidget(form_box)
        inner_layout.addStretch()

        scroll.setWidget(inner)
        layout.addWidget(scroll)

    def _path_row(self, parent_layout, label_text, label_attr, btn_attr, slot):
        row = QHBoxLayout()
        row.addWidget(QLabel(label_text))
        lab = QLabel("—")
        lab.setStyleSheet("color: #a0a4ac; padding: 4px;")
        lab.setWordWrap(True)
        lab.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        setattr(self, label_attr, lab)
        btn = QPushButton("Browse…")
        btn.clicked.connect(slot)
        setattr(self, btn_attr, btn)
        row.addWidget(lab, 1)
        row.addWidget(btn)
        parent_layout.addLayout(row)

    def _set_form_enabled(self, enabled: bool):
        for w in (
            self.table,
            self.new_btn,
            self.delete_btn,
            self.apply_btn,
            self.name_edit,
            self.desc_edit,
            self.save_btn,
            getattr(self, "video_btn"),
            getattr(self, "config_btn"),
            getattr(self, "output_btn"),
        ):
            w.setEnabled(enabled)

    def _set_path_label(self, label: QLabel, path: str, empty_text: str):
        if path:
            label.setText(os.path.basename(path) or path)
            label.setToolTip(path)
        else:
            label.setText(empty_text)
            label.setToolTip("")

    def _pick_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Video file",
            "",
            "Video Files (*.avi *.mp4 *.mov *.mkv);;All Files (*)",
        )
        if path:
            self._set_path_label(self.video_path_label, path, "No video")

    def _pick_config(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "ZebraZoom config",
            "",
            "JSON (*.json);;All Files (*)",
        )
        if path:
            self._set_path_label(self.config_path_label, path, "Default config")

    def _pick_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Output folder", "")
        if folder:
            self._set_path_label(self.output_path_label, folder, "Default (next to video)")

    def _reload_table(self):
        self.table.setRowCount(0)
        if self.user_id is None:
            return
        for p in presets_db.list_presets(self.user_id):
            r = self.table.rowCount()
            self.table.insertRow(r)
            name_item = QTableWidgetItem(p["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, p["id"])
            self.table.setItem(r, 0, name_item)
            vp = p.get("video_path") or ""
            self.table.setItem(r, 1, QTableWidgetItem(os.path.basename(vp) if vp else "—"))
            od = p.get("output_dir") or ""
            self.table.setItem(r, 2, QTableWidgetItem(os.path.basename(od) if od else "—"))
            self.table.setItem(r, 3, QTableWidgetItem(str(p.get("created_at") or "")))

    def _on_table_selection(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows or self.user_id is None:
            return
        row = rows[0].row()
        item = self.table.item(row, 0)
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        if pid is None:
            return
        rec = presets_db.get_preset(self.user_id, int(pid))
        if not rec:
            return
        self._editing_preset_id = int(rec["id"])
        self.name_edit.setText(rec["name"] or "")
        self.desc_edit.setPlainText(rec["description"] or "")
        self._set_path_label(
            self.video_path_label, rec.get("video_path") or "", "No video"
        )
        self._set_path_label(
            self.config_path_label, rec.get("config_path") or "", "Default config"
        )
        self._set_path_label(
            self.output_path_label, rec.get("output_dir") or "", "Default (next to video)"
        )

    def _new_preset(self):
        self._editing_preset_id = None
        self.table.clearSelection()
        self.name_edit.clear()
        self.desc_edit.clear()
        self._set_path_label(self.video_path_label, "", "No video")
        self._set_path_label(self.config_path_label, "", "Default config")
        self._set_path_label(self.output_path_label, "", "Default (next to video)")

    def _save_preset(self):
        if self.user_id is None:
            return
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Preset", "Please enter a name.")
            return
        desc = self.desc_edit.toPlainText().strip()
        v, c, o = self._paths_from_form()
        try:
            if self._editing_preset_id is None:
                presets_db.create_preset(
                    self.user_id, name, desc, v or None, c or None, o or None
                )
            else:
                presets_db.update_preset(
                    self.user_id,
                    self._editing_preset_id,
                    name,
                    desc,
                    v or None,
                    c or None,
                    o or None,
                )
        except Exception as e:
            logger.exception("save preset")
            QMessageBox.critical(self, "Preset", f"Could not save: {e}")
            return
        self._reload_table()
        QMessageBox.information(self, "Preset", "Preset saved.")

    def _delete_preset(self):
        if self.user_id is None or self._editing_preset_id is None:
            QMessageBox.information(self, "Preset", "Select a preset to delete.")
            return
        if (
            QMessageBox.question(
                self,
                "Delete preset",
                "Delete this preset?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        presets_db.delete_preset(self.user_id, self._editing_preset_id)
        self._new_preset()
        self._reload_table()

    def _apply_to_data(self):
        if not hasattr(self.main_window, "analysis_tab"):
            QMessageBox.warning(self, "Apply", "Analysis tab is not available.")
            return
        if self.user_id is None:
            QMessageBox.information(self, "Apply", "Log in to use presets.")
            return
        rows = self.table.selectionModel().selectedRows()
        pid = None
        if rows:
            item = self.table.item(rows[0].row(), 0)
            if item:
                pid = item.data(Qt.ItemDataRole.UserRole)
        if pid is None and self._editing_preset_id is not None:
            pid = self._editing_preset_id
        rec = None
        if pid is not None:
            rec = presets_db.get_preset(self.user_id, int(pid))
        if rec:
            v = rec.get("video_path") or ""
            if not v:
                QMessageBox.warning(self, "Apply", "This preset has no video path.")
                return
            self.main_window.analysis_tab.apply_paths(
                video_path=v,
                config_path=rec.get("config_path") or None,
                output_dir=rec.get("output_dir") or None,
            )
        else:
            v, c, o = self._paths_from_form()
            if not v:
                QMessageBox.warning(
                    self,
                    "Apply",
                    "Select a saved preset or choose a video path in the form.",
                )
                return
            self.main_window.analysis_tab.apply_paths(
                video_path=v, config_path=c or None, output_dir=o or None
            )
        QMessageBox.information(
            self,
            "Apply",
            "Paths applied to the Data tab. Open Data to run analysis.",
        )

    def _paths_from_form(self):
        """Paths from form labels (tooltips hold full paths when set via Browse)."""
        def tip(lab: QLabel, empty_display: tuple):
            t = lab.toolTip() or ""
            if lab.text() in empty_display and not t:
                return ""
            return t

        v = tip(self.video_path_label, ("—", "No video"))
        c = tip(self.config_path_label, ("—", "Default config"))
        o = tip(self.output_path_label, ("—", "Default (next to video)"))
        return v, c, o
