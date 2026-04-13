from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QMessageBox,
    QFileDialog,
    QLineEdit,
    QWidget,
    QFrame,
    QScrollArea,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QDateTime, QTimer, pyqtSignal
import serial.tools.list_ports
import logging
import os


class SettingsCard(QFrame):
    """Reusable dark neon settings card with floating section label."""

    def __init__(self, section_label: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsCard")
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 22, 20, 18)
        root.setSpacing(12)
        cap_row = QHBoxLayout()
        cap_row.setContentsMargins(0, 0, 0, 0)
        self._cap = QLabel(section_label.upper())
        self._cap.setObjectName("CardCaption")
        cap_row.addWidget(self._cap, 0, Qt.AlignmentFlag.AlignLeft)
        cap_row.addStretch(1)
        root.addLayout(cap_row)
        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(12)
        root.addLayout(self.body)


class ArduinoSettingsCard(SettingsCard):
    def __init__(self, parent=None) -> None:
        super().__init__("Arduino Settings", parent)


class ZebraZoomSettingsCard(SettingsCard):
    def __init__(self, parent=None) -> None:
        super().__init__("ZebraZoom Settings", parent)


class StatusFooter(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SettingsFooter")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(16)
        self.left = QLabel(
            "System: Disconnected   |   Camera: Idle   |   Chamber: Idle   |   Temperature: —   |   Water flow: —"
        )
        self.left.setObjectName("FooterLeft")
        self.left.setWordWrap(True)
        self.right = QLabel("")
        self.right.setObjectName("FooterRight")
        lay.addWidget(self.left, 1)
        lay.addWidget(self.right, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)


class SettingsDialog(QDialog):
    back_to_home_requested = pyqtSignal()

    def __init__(self, arduino_controller, parent=None, zebrazoom_integration=None):
        # Compatibility:
        # - SettingsDialog(self) from ui/main_window.py
        # - SettingsDialog(self.arduino, self, self.zebrazoom) from gui/main_window.py
        if parent is None and arduino_controller is not None and not hasattr(arduino_controller, "connect"):
            parent = arduino_controller
            arduino_controller = getattr(parent, "arduino", None)
            zebrazoom_integration = getattr(parent, "zebrazoom", zebrazoom_integration)

        super().__init__(parent)
        self.arduino = arduino_controller
        self.zebrazoom = zebrazoom_integration
        self.logger = logging.getLogger("settings_dialog")

        self.setWindowTitle("Settings")
        self.resize(980, 700)
        self.setMinimumSize(860, 560)

        self.setStyleSheet("""
            QDialog {
                background-color: #06111F;
                color: #FFFFFF;
                font-family: "Segoe UI", "Inter", "Poppins", sans-serif;
            }
            QWidget#SettingsRoot {
                background: #06111F;
            }
            QFrame#HeaderWrap {
                background: transparent;
            }
            QLabel#HeaderTitle {
                color: #FFFFFF;
                font-size: 28px;
                font-weight: 800;
            }
            QLabel#HeaderSub {
                color: #94A3B8;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton#BackHomeBtn {
                background: transparent;
                border: 1px solid transparent;
                color: #9CC7E8;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton#BackHomeBtn:hover {
                background: rgba(0, 200, 255, 0.08);
                border: 1px solid #15324D;
            }
            QFrame#SettingsCard {
                background: #0D1420;
                border: 1px solid #15324D;
                border-radius: 14px;
            }
            QLabel#CardCaption {
                color: #9CC7E8;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 1.2px;
                background: #0D1420;
                padding: 2px 8px;
            }
            QLabel#RowLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 500;
            }
            QLabel#Muted {
                color: #94A3B8;
                font-size: 11px;
            }
            QLabel#Danger {
                color: #FF5D73;
                font-size: 14px;
                font-weight: 700;
            }
            QLabel#Success {
                color: #22C55E;
                font-size: 14px;
                font-weight: 700;
            }
            QLabel#Warning {
                color: #FACC15;
                font-size: 14px;
                font-weight: 700;
            }
            QFrame#Divider {
                background: #15324D;
                min-height: 1px;
                max-height: 1px;
                border: none;
            }
            QLineEdit, QComboBox {
                background: #0B1B2C;
                border: 1px solid #15324D;
                border-radius: 10px;
                color: #FFFFFF;
                min-height: 40px;
                padding: 0 12px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #00C8FF;
            }
            QComboBox::drop-down {
                width: 24px;
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #9CC7E8;
                margin-right: 6px;
            }
            QPushButton {
                border-radius: 10px;
                min-height: 40px;
                padding: 0 16px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton#PrimaryBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5B5CFF, stop:1 #007BFF);
                color: #FFFFFF;
                border: 1px solid rgba(110, 165, 255, 0.75);
            }
            QPushButton#PrimaryBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6E70FF, stop:1 #1E8EFF);
            }
            QPushButton#SecondaryBtn {
                background: #0B1B2C;
                color: #E7F2FF;
                border: 1px solid #15324D;
            }
            QPushButton#SecondaryBtn:hover {
                border: 1px solid #00C8FF;
                background: rgba(0, 200, 255, 0.08);
            }
            QPushButton#DangerBtn {
                background: #111824;
                color: #FFCDD4;
                border: 1px solid #7A2A38;
            }
            QPushButton#DangerBtn:hover {
                border: 1px solid #FF5D73;
                background: rgba(255, 93, 115, 0.10);
            }
            QFrame#SettingsFooter {
                background: #071426;
                border-top: 1px solid #15324D;
            }
            QLabel#FooterLeft, QLabel#FooterRight {
                color: #94A3B8;
                font-size: 11px;
            }
        """)

        self._build_ui()
        self._refresh_ports()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        body = QWidget()
        body.setObjectName("SettingsRoot")
        root.addWidget(body, 1)
        b = QVBoxLayout(body)
        b.setContentsMargins(12, 12, 12, 8)
        b.setSpacing(12)

        header = QFrame()
        header.setObjectName("HeaderWrap")
        hh = QHBoxLayout(header)
        hh.setContentsMargins(0, 0, 0, 0)
        hleft = QVBoxLayout()
        hleft.setSpacing(2)
        title = QLabel("Settings")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel(
            "Arduino serial link and ZebraZoom executable — same layout as desktop app."
        )
        subtitle.setObjectName("HeaderSub")
        subtitle.setWordWrap(True)
        hleft.addWidget(title)
        hleft.addWidget(subtitle)
        hh.addLayout(hleft, 1)
        self._btn_back_home = QPushButton("Back to Home")
        self._btn_back_home.setObjectName("BackHomeBtn")
        self._btn_back_home.clicked.connect(self._on_back_to_home)
        hh.addWidget(self._btn_back_home, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        b.addWidget(header)

        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sc.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        sc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(18)
        container = QWidget()
        container.setMaximumWidth(980)
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(18)

        # Arduino Settings Card
        arduino_card = ArduinoSettingsCard()
        arduino_layout = arduino_card.body

        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        status_label = QLabel("Connection status:")
        status_label.setObjectName("RowLabel")
        status_label.setMinimumWidth(120)
        self.status_value = QLabel("Checking...")
        self.status_value.setObjectName("Warning")
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_value)
        status_layout.addStretch()
        arduino_layout.addLayout(status_layout)

        port_layout = QHBoxLayout()
        port_layout.setSpacing(10)
        port_label = QLabel("Serial port:")
        port_label.setObjectName("RowLabel")
        port_label.setMinimumWidth(120)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(220)
        self.port_combo.setEditable(False)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("SecondaryBtn")
        refresh_btn.setMinimumWidth(80)
        refresh_btn.clicked.connect(self._refresh_ports)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_combo, 1)
        port_layout.addWidget(refresh_btn)
        arduino_layout.addLayout(port_layout)

        div1 = QFrame()
        div1.setObjectName("Divider")
        arduino_layout.addWidget(div1)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("PrimaryBtn")
        self.connect_btn.setMinimumWidth(96)
        self.connect_btn.clicked.connect(self._connect_arduino)

        self.auto_connect_btn = QPushButton("Auto-connect")
        self.auto_connect_btn.setObjectName("SecondaryBtn")
        self.auto_connect_btn.setMinimumWidth(110)
        self.auto_connect_btn.clicked.connect(self._connect_arduino)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setObjectName("DangerBtn")
        self.disconnect_btn.setMinimumWidth(96)
        self.disconnect_btn.clicked.connect(self._disconnect_arduino)
        self.disconnect_btn.setEnabled(False)

        self.test_btn = QPushButton("Test connection")
        self.test_btn.setObjectName("SecondaryBtn")
        self.test_btn.setMinimumWidth(120)
        self.test_btn.clicked.connect(self._test_connection)

        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.auto_connect_btn)
        button_layout.addWidget(self.disconnect_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.test_btn)
        arduino_layout.addLayout(button_layout)

        info_layout = QHBoxLayout()
        info_label = QLabel("Current port:")
        info_label.setObjectName("RowLabel")
        info_label.setMinimumWidth(120)
        self.current_port_label = QLabel("None")
        self.current_port_label.setObjectName("Muted")
        info_layout.addWidget(info_label)
        info_layout.addWidget(self.current_port_label)
        info_layout.addStretch()
        arduino_layout.addLayout(info_layout)

        cl.addWidget(arduino_card)

        # ZebraZoom Settings Card
        zebrazoom_card = ZebraZoomSettingsCard()
        zz_layout = zebrazoom_card.body

        info_label = QLabel(
            "Specify the path to ZebraZoom.exe (the file, not the folder) — used by Analysis."
        )
        info_label.setObjectName("Muted")
        info_label.setWordWrap(True)
        zz_layout.addWidget(info_label)

        zz_status_layout = QHBoxLayout()
        zz_status_layout.setSpacing(10)
        zz_status_label = QLabel("Status:")
        zz_status_label.setObjectName("RowLabel")
        zz_status_label.setMinimumWidth(120)
        self.zz_status_value = QLabel("Checking...")
        self.zz_status_value.setObjectName("Warning")
        zz_status_layout.addWidget(zz_status_label)
        zz_status_layout.addWidget(self.zz_status_value)
        zz_status_layout.addStretch()
        zz_layout.addLayout(zz_status_layout)

        zz_path_layout = QHBoxLayout()
        zz_path_layout.setSpacing(10)
        zz_path_label = QLabel("ZebraZoom.exe:")
        zz_path_label.setObjectName("RowLabel")
        zz_path_label.setMinimumWidth(120)
        self.zz_path_edit = QLineEdit()
        self.zz_path_edit.setPlaceholderText("C:\\path\\to\\ZebraZoom.exe")

        # Initialize path if zebrazoom exists
        if self.zebrazoom:
            if self.zebrazoom.zebrazoom_exe:
                self.zz_path_edit.setText(self.zebrazoom.zebrazoom_exe)
            elif self.zebrazoom.zebrazoom_lib:
                self.zz_path_edit.setText("Library (imported)")
                self.zz_path_edit.setEnabled(False)
            else:
                # Try to find default path
                default_path = r"C:\Users\{}\Downloads\ZebraZoom-Windows\ZebraZoom.exe".format(os.getenv("USERNAME", ""))
                if os.path.exists(default_path):
                    self.zz_path_edit.setText(default_path)

        zz_browse_btn = QPushButton("Browse")
        zz_browse_btn.setObjectName("SecondaryBtn")
        zz_browse_btn.setMinimumWidth(80)
        zz_browse_btn.clicked.connect(self._browse_zebrazoom_path)
        zz_path_layout.addWidget(zz_path_label)
        zz_path_layout.addWidget(self.zz_path_edit, 1)
        zz_path_layout.addWidget(zz_browse_btn)
        zz_layout.addLayout(zz_path_layout)

        note = QLabel(
            "Browse opens a file dialog on the machine running this app. "
            "If it does not appear, paste the full ZebraZoom.exe path manually."
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)
        zz_layout.addWidget(note)

        div2 = QFrame()
        div2.setObjectName("Divider")
        zz_layout.addWidget(div2)

        zz_btns = QHBoxLayout()
        zz_btns.setSpacing(10)
        self._zz_save_btn = QPushButton("Save path")
        self._zz_save_btn.setObjectName("SecondaryBtn")
        self._zz_save_btn.clicked.connect(lambda: self._test_zebrazoom(save_only=True))
        zz_test_btn = QPushButton("Test & save")
        zz_test_btn.setObjectName("PrimaryBtn")
        zz_test_btn.setMinimumWidth(120)
        zz_test_btn.clicked.connect(self._test_zebrazoom)
        zz_btns.addWidget(self._zz_save_btn, 0)
        zz_btns.addWidget(zz_test_btn, 0)
        zz_btns.addStretch(1)
        zz_layout.addLayout(zz_btns)

        cl.addWidget(zebrazoom_card)
        cl.addStretch(1)
        center_row = QHBoxLayout()
        center_row.setContentsMargins(0, 0, 0, 0)
        center_row.addStretch(1)
        center_row.addWidget(container, 0)
        center_row.addStretch(1)
        wl.addLayout(center_row)
        sc.setWidget(wrap)
        b.addWidget(sc, 1)

        self._footer = StatusFooter()
        b.addWidget(self._footer, 0)

        # Initialize ZebraZoom if not exists
        if not self.zebrazoom:
            try:
                from backend.zebrazoom_integration import ZebraZoomIntegration
                self.zebrazoom = ZebraZoomIntegration()
            except Exception as e:
                self.logger.warning(f"Could not initialize ZebraZoom: {e}")
                self.zebrazoom = None

        self._update_zebrazoom_status()

        self._clock = QTimer(self)
        self._clock.timeout.connect(self._tick_clock)
        self._clock.start(1000)
        self._tick_clock()

        # Update UI state
        self._update_ui_state()

    def _tick_clock(self) -> None:
        self._footer.right.setText(
            QDateTime.currentDateTime().toString("h:mm AP MMM d, yyyy")
        )

    def _on_back_to_home(self) -> None:
        self.back_to_home_requested.emit()
        if self.isModal():
            self.accept()
        
    def _refresh_ports(self):
        """Refresh the list of available serial ports"""
        self.port_combo.clear()
        ports = [p.device for p in serial.tools.list_ports.comports()]
        
        if ports:
            self.port_combo.addItems(ports)
            # Select current port if connected
            if self.arduino and self.arduino.is_connected():
                current_port = getattr(self.arduino, 'port', None)
                if current_port and current_port in ports:
                    index = self.port_combo.findText(current_port)
                    if index >= 0:
                        self.port_combo.setCurrentIndex(index)
        else:
            self.port_combo.addItem("No ports available")
            self.port_combo.setEnabled(False)
            
    def _update_ui_state(self):
        """Update UI based on connection state"""
        if not self.arduino:
            self.status_value.setText("Not Available")
            self.status_value.setObjectName("Danger")
            self.status_value.style().unpolish(self.status_value)
            self.status_value.style().polish(self.status_value)
            self.connect_btn.setEnabled(False)
            self.auto_connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)
            self.current_port_label.setText("None")
            return
            
        is_connected = self.arduino.is_connected()
        
        if is_connected:
            port = getattr(self.arduino, 'port', 'Unknown')
            self.status_value.setText("Connected")
            self.status_value.setObjectName("Success")
            self.status_value.style().unpolish(self.status_value)
            self.status_value.style().polish(self.status_value)
            self.connect_btn.setEnabled(False)
            self.auto_connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.current_port_label.setText(port)
        else:
            self.status_value.setText("Disconnected")
            self.status_value.setObjectName("Danger")
            self.status_value.style().unpolish(self.status_value)
            self.status_value.style().polish(self.status_value)
            self.connect_btn.setEnabled(True)
            self.auto_connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.current_port_label.setText("None")
            
    def _connect_arduino(self):
        """Connect to selected Arduino port"""
        if not self.arduino:
            QMessageBox.warning(self, "Error", "Arduino controller not available")
            return
            
        selected_port = self.port_combo.currentText()
        if not selected_port or selected_port == "No ports available":
            QMessageBox.warning(self, "Error", "Please select a valid serial port")
            return
            
        try:
            self.status_value.setText("Connecting...")
            self.status_value.setObjectName("Warning")
            self.status_value.style().unpolish(self.status_value)
            self.status_value.style().polish(self.status_value)
            self.connect_btn.setEnabled(False)
            
            if self.arduino.connect(selected_port):
                QMessageBox.information(self, "Success", f"Connected to {selected_port}")
                self._update_ui_state()
                # Notify parent to update status
                if self.parent():
                    if hasattr(self.parent(), '_update_arduino_status'):
                        port = getattr(self.arduino, 'port', 'Unknown')
                        self.parent()._update_arduino_status(True, f"Connected ({port})")
            else:
                QMessageBox.warning(self, "Error", f"Failed to connect to {selected_port}\n\nMake sure:\n- Arduino is connected\n- Firmware is loaded\n- Port is not in use by another program")
                self._update_ui_state()
        except Exception as e:
            self.logger.error(f"Connection error: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Connection error: {str(e)}")
            self._update_ui_state()
            
    def _disconnect_arduino(self):
        """Disconnect from Arduino"""
        if not self.arduino:
            return
            
        try:
            self.arduino.close()
            self._update_ui_state()
            # Notify parent to update status
            if self.parent():
                if hasattr(self.parent(), '_update_arduino_status'):
                    self.parent()._update_arduino_status(False, "Disconnected")
            QMessageBox.information(self, "Disconnected", "Arduino disconnected successfully")
        except Exception as e:
            self.logger.error(f"Disconnect error: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Error disconnecting: {str(e)}")
            
    def _test_connection(self):
        """Test the Arduino connection"""
        if not self.arduino:
            QMessageBox.warning(self, "Error", "Arduino controller not available")
            return
            
        if not self.arduino.is_connected():
            QMessageBox.warning(self, "Not Connected", "Arduino is not connected. Please connect first.")
            return
            
        try:
            # Try sending STATUS command
            reply = self.arduino.send("STATUS")
            if reply:
                QMessageBox.information(self, "Test Successful", f"Arduino responded:\n{reply}")
            else:
                QMessageBox.warning(self, "Test Failed", "Arduino did not respond to STATUS command")
        except Exception as e:
            self.logger.error(f"Test error: {e}", exc_info=True)
            QMessageBox.critical(self, "Test Error", f"Error testing connection: {str(e)}")
            
    def _browse_zebrazoom_path(self):
        """Browse for ZebraZoom executable"""
        # Start from common location if exists
        start_dir = r"C:\Users\{}\Downloads\ZebraZoom-Windows".format(os.getenv("USERNAME", ""))
        if not os.path.exists(start_dir):
            start_dir = ""
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select ZebraZoom.exe File",
            start_dir,
            "Executable Files (*.exe);;All Files (*)"
        )
        
        if file_path:
            # Verify it's actually ZebraZoom.exe
            if not file_path.lower().endswith('.exe'):
                QMessageBox.warning(self, "Invalid File", "Please select the ZebraZoom.exe file")
                return
            
            self.zz_path_edit.setText(file_path)
            # Update ZebraZoom integration
            if self.zebrazoom:
                self.zebrazoom.zebrazoom_exe = file_path
                self.zebrazoom.zebrazoom_lib = None
            else:
                # Create new integration if doesn't exist
                try:
                    from backend.zebrazoom_integration import ZebraZoomIntegration
                    self.zebrazoom = ZebraZoomIntegration(zebrazoom_path=file_path)
                except Exception as e:
                    self.logger.error(f"Error creating ZebraZoom integration: {e}")
            
            self._update_zebrazoom_status()
    
    def _test_zebrazoom(self, save_only: bool = False):
        """Test ZebraZoom connection and save path"""
        # Get path from text field
        path = self.zz_path_edit.text().strip()
        
        if not path or path == "Library (imported)":
            QMessageBox.warning(self, "No Path", "Please specify the path to ZebraZoom.exe")
            return
        
        # Verify file exists
        if not os.path.exists(path):
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The file does not exist:\n{path}\n\nPlease check the path and try again."
            )
            return
        
        # Verify it's an .exe file
        if not path.lower().endswith('.exe'):
            QMessageBox.warning(
                self,
                "Invalid File",
                "Please select the ZebraZoom.exe file, not a folder.\n\n"
                "The path should end with: ZebraZoom.exe"
            )
            return
        
        # Create or update ZebraZoom integration
        try:
            if not self.zebrazoom:
                from backend.zebrazoom_integration import ZebraZoomIntegration
                self.zebrazoom = ZebraZoomIntegration(zebrazoom_path=path)
            else:
                self.zebrazoom.zebrazoom_exe = path
                self.zebrazoom.zebrazoom_lib = None
            
            # Test if available
            if self.zebrazoom.is_available():
                # Check for optional dependencies using the same method as the integration module
                missing_deps = []
                
                # Check pandas
                try:
                    import pandas
                except ImportError:
                    missing_deps.append("pandas")
                
                # Check numpy
                try:
                    import numpy
                except ImportError:
                    missing_deps.append("numpy")
                
                # Check scipy
                try:
                    import scipy
                except ImportError:
                    missing_deps.append("scipy")
                
                # Check scikit-learn
                try:
                    import sklearn
                except ImportError:
                    missing_deps.append("scikit-learn")
                
                # Check h5py
                try:
                    import h5py
                except ImportError:
                    missing_deps.append("h5py")
                
                if missing_deps and not save_only:
                    import sys
                    dep_list = ", ".join(missing_deps)
                    python_exe = sys.executable
                    
                    # Create install command
                    install_cmd = f"{python_exe} -m pip install {dep_list}"
                    
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Icon.Warning)
                    msg.setWindowTitle("Dependencies Missing")
                    msg.setText(
                        f"ZebraZoom path is set, but some optional dependencies are missing:\n\n"
                        f"Missing: {dep_list}\n\n"
                        f"To install, run this command in a terminal:\n\n"
                        f"{install_cmd}\n\n"
                        f"Or run the install_dependencies.py script:\n"
                        f"{python_exe} install_dependencies.py\n\n"
                        f"Note: Make sure you're using the same Python that runs ZIMON:\n"
                        f"{python_exe}"
                    )
                    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                    msg.exec()
                elif not save_only:
                    QMessageBox.information(
                        self,
                        "Success",
                        f"ZebraZoom found and ready to use!\n\nPath: {path}\n\n"
                        "All dependencies are installed.\n"
                        "You can now use the Analysis tab to analyze videos."
                    )
                
                self._update_zebrazoom_status()
                
                # Update parent window's zebrazoom reference
                if self.parent() and hasattr(self.parent(), 'zebrazoom'):
                    self.parent().zebrazoom = self.zebrazoom
                    # Update analysis tab if it exists
                    if hasattr(self.parent(), '_update_zebrazoom_in_analysis'):
                        self.parent()._update_zebrazoom_in_analysis()
            elif not save_only:
                QMessageBox.warning(
                    self,
                    "Not Available",
                    "ZebraZoom path was set but could not be verified.\n\n"
                    "Please ensure:\n"
                    "1. The file is ZebraZoom.exe\n"
                    "2. The file is not corrupted\n"
                    "3. You have permission to access it"
                )
        except Exception as e:
            self.logger.error(f"Error testing ZebraZoom: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error setting up ZebraZoom:\n{str(e)}"
            )
    
    def _update_zebrazoom_status(self):
        """Update ZebraZoom status display"""
        if not self.zebrazoom:
            return
        
        if self.zebrazoom.is_available():
            if self.zebrazoom.zebrazoom_exe:
                self.zz_status_value.setText("Available (Executable)")
                self.zz_status_value.setObjectName("Success")
                self.zz_status_value.style().unpolish(self.zz_status_value)
                self.zz_status_value.style().polish(self.zz_status_value)
            elif self.zebrazoom.zebrazoom_lib:
                self.zz_status_value.setText("Available (Library)")
                self.zz_status_value.setObjectName("Success")
                self.zz_status_value.style().unpolish(self.zz_status_value)
                self.zz_status_value.style().polish(self.zz_status_value)
        else:
            self.zz_status_value.setText("Not Available")
            self.zz_status_value.setObjectName("Warning")
            self.zz_status_value.style().unpolish(self.zz_status_value)
            self.zz_status_value.style().polish(self.zz_status_value)
    
    def showEvent(self, event):
        """Update UI when dialog is shown"""
        super().showEvent(event)
        self._refresh_ports()
        self._update_ui_state()
        if self.zebrazoom:
            self._update_zebrazoom_status()

