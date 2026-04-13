# main.py
import sys
import logging
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("zimon_app")

# imports
from gui.loading_screen import LoadingScreen
from gui.login_window import LoginWindow
from ui.main_window import MainWindow
from database.db import init_db
from database.auth import get_active_session_user
from backend.arduino_controller import ArduinoController
from backend.camera_interface import CameraController
from backend.experiment_runner import ExperimentRunner

# Global references to avoid premature garbage collection.
MAIN_WINDOW = None
LOGIN_WINDOW = None
APP_INSTANCE = None


def main():
    global APP_INSTANCE, LOGIN_WINDOW
    logger.info("Starting ZIMON application")
    init_db()
    logger.info("SQLite database initialized")
    app = QApplication(sys.argv)
    APP_INSTANCE = app



    # =========================
    # LOAD GLOBAL STYLESHEET (dark / light from QSettings)
    # =========================
    try:
        from gui.theme import load_application_stylesheet

        load_application_stylesheet(app)
        logger.info("Stylesheet loaded (theme from QSettings)")
    except Exception as e:
        logger.warning(f"Failed to load stylesheet: {e}")

    active_user = get_active_session_user()
    loading = LoadingScreen()
    loading.show()

    if active_user:
        QTimer.singleShot(800, lambda: init_backend(loading, active_user))
    else:
        QTimer.singleShot(800, lambda: show_login_window(loading))

    sys.exit(app.exec())


def on_login_success(user_data):
    global LOGIN_WINDOW
    if LOGIN_WINDOW:
        LOGIN_WINDOW.close()
        LOGIN_WINDOW = None

    init_backend(None, user_data)


def init_backend(loading, user_data):
    logger.info("Initializing backend")

    arduino = ArduinoController()
    camera = CameraController()
    runner = ExperimentRunner(
        arduino_controller=arduino,
        camera_controller=camera,
        logger=logger
    )

    launch_main(loading, arduino, camera, runner, user_data)


def show_login_window(loading=None):
    global LOGIN_WINDOW
    if loading is not None:
        loading.close()

    if LOGIN_WINDOW is None:
        LOGIN_WINDOW = LoginWindow()
        LOGIN_WINDOW.login_success.connect(on_login_success)
    LOGIN_WINDOW.show()
    LOGIN_WINDOW.raise_()
    LOGIN_WINDOW.activateWindow()


def launch_main(loading, arduino, camera, runner, user_data):
    global MAIN_WINDOW

    logger.info("Opening main dashboard")

    MAIN_WINDOW = MainWindow(
        user_data=user_data,
        runner=runner,
        arduino=arduino,
        camera=camera
    )

    if loading is not None:
        loading.close()
    MAIN_WINDOW.show()
    MAIN_WINDOW.raise_()
    MAIN_WINDOW.activateWindow()



if __name__ == "__main__":
    main()
