from PyQt6.QtWidgets import QMessageBox

from database.auth import clear_active_session
from gui.login_window import LoginWindow
from gui.main_window import MainWindow as AppMainWindow


class MainWindow(AppMainWindow):
    def __init__(self, user_data=None, runner=None, arduino=None, camera=None):
        super().__init__(
            runner=runner,
            arduino=arduino,
            camera=camera,
            user_data=user_data,
        )
        self.login_window = None
        self._apply_user_context()

    def _apply_user_context(self):
        full_name = self.user_data.get("full_name", "User")
        role = self.user_data.get("role", "user")
        base = self.windowTitle() or "ZIMON"
        self.setWindowTitle(f"{base} | Welcome, {full_name} ({role})")

    def _logout(self):
        confirm = QMessageBox.question(
            self,
            "Logout",
            "Logout and go back to login screen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        clear_active_session()
        self.login_window = LoginWindow()
        self.login_window.login_success.connect(self._on_relogin_success)
        self.login_window.show()
        self.close()

    def _on_relogin_success(self, user_data):
        self.user_data = user_data or {}
        uid = self.user_data.get("id")
        if hasattr(self, "presets_tab"):
            self.presets_tab.refresh_for_user(uid if uid is not None else None)
        self._refresh_account_profile()
        self._apply_user_context()
        self.show()
        if self.login_window is not None:
            self.login_window.close()

