"""
Web Server Mode Tab - Clean, modern interface for web server management.
"""

import logging
import threading
import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QTextEdit, QLineEdit, QSpinBox, QCheckBox, QFormLayout,
    QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class WebServerWorker(QThread):
    """Worker thread for web server operations."""
    
    server_started = pyqtSignal()
    server_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.server_running = False
    
    def start_server(self, host: str, port: int):
        """Start the web server."""
        self.host = host
        self.port = port
        self.server_running = True
        self.start()
    
    def stop_server(self):
        """Stop the web server."""
        self.server_running = False
    
    def run(self):
        """Run the worker thread."""
        try:
            if self.server_running:
                # Simulate server startup
                import time
                time.sleep(2)  # Simulate startup time
                self.server_started.emit()
                
                # Keep server running
                while self.server_running:
                    time.sleep(1)
                
                self.server_stopped.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))


class WebServerTab(QWidget):
    """Main Web Server Mode tab with clean, modern design."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = WebServerWorker()
        self.setup_ui()
        self.connect_signals()
        self.apply_styles()
    
    def setup_ui(self):
        """Setup the main UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Web Server Mode")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Description
        description = QLabel(
            "Enable web-based interface for remote access and multi-user collaboration."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Configuration Group
        config_group = QGroupBox("Server Configuration")
        config_layout = QFormLayout(config_group)
        
        # Host configuration
        self.host_edit = QLineEdit("localhost")
        self.host_edit.setPlaceholderText("Enter host address")
        config_layout.addRow("Host:", self.host_edit)
        
        # Port configuration
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(8080)
        config_layout.addRow("Port:", self.port_spin)
        
        # Options
        self.debug_checkbox = QCheckBox("Enable debug mode")
        self.cors_checkbox = QCheckBox("Enable CORS")
        self.cors_checkbox.setChecked(True)
        config_layout.addRow("", self.debug_checkbox)
        config_layout.addRow("", self.cors_checkbox)
        
        layout.addWidget(config_group)
        
        # Control Group
        control_group = QGroupBox("Server Controls")
        control_layout = QVBoxLayout(control_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Server")
        self.start_button.clicked.connect(self.start_server)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Server")
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.open_browser_button = QPushButton("Open in Browser")
        self.open_browser_button.clicked.connect(self.open_browser)
        self.open_browser_button.setEnabled(False)
        button_layout.addWidget(self.open_browser_button)
        
        control_layout.addLayout(button_layout)
        
        # Status
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Stopped")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        control_layout.addLayout(status_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        layout.addWidget(control_group)
        
        # Log Group
        log_group = QGroupBox("Server Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        # Log controls
        log_controls_layout = QHBoxLayout()
        self.clear_log_button = QPushButton("Clear Log")
        self.clear_log_button.clicked.connect(self.clear_log)
        log_controls_layout.addWidget(self.clear_log_button)
        log_controls_layout.addStretch()
        log_layout.addLayout(log_controls_layout)
        
        layout.addWidget(log_group)
        
        # Information Group
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel(
            "The web server provides:\n"
            "• Web-based interface for remote access\n"
            "• Multi-user collaboration capabilities\n"
            "• REST API for external integrations\n"
            "• Real-time WebSocket communication\n"
            "• Cross-platform accessibility"
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
    
    def connect_signals(self):
        """Connect signals."""
        self.worker.server_started.connect(self.handle_server_started)
        self.worker.server_stopped.connect(self.handle_server_stopped)
        self.worker.error_occurred.connect(self.handle_error)
    
    def start_server(self):
        """Start the web server."""
        try:
            host = self.host_edit.text().strip()
            port = self.port_spin.value()
            
            if not host:
                QMessageBox.warning(self, "Warning", "Please enter a valid host address.")
                return
            
            # Update UI
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.open_browser_button.setEnabled(False)
            self.status_label.setText("Starting...")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Log
            self.log_message(f"Starting web server on {host}:{port}")
            
            # Start server in background
            self.worker.start_server(host, port)
            
        except Exception as e:
            self.handle_error(str(e))
    
    def stop_server(self):
        """Stop the web server."""
        try:
            self.worker.stop_server()
            self.log_message("Stopping web server...")
        except Exception as e:
            self.handle_error(str(e))
    
    def open_browser(self):
        """Open the web interface in browser."""
        try:
            host = self.host_edit.text().strip()
            port = self.port_spin.value()
            url = f"http://{host}:{port}"
            webbrowser.open(url)
            self.log_message(f"Opened browser to {url}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening browser: {e}")
    
    def handle_server_started(self):
        """Handle server started event."""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.open_browser_button.setEnabled(True)
        self.status_label.setText("Running")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        self.progress_bar.setVisible(False)
        
        host = self.host_edit.text().strip()
        port = self.port_spin.value()
        self.log_message(f"Web server started successfully on {host}:{port}")
        
        # Show success message
        QMessageBox.information(
            self, "Success", 
            f"Web server started successfully!\n\n"
            f"Access the interface at: http://{host}:{port}\n\n"
            f"You can now open it in your browser or share the URL with others."
        )
    
    def handle_server_stopped(self):
        """Handle server stopped event."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.open_browser_button.setEnabled(False)
        self.status_label.setText("Stopped")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.progress_bar.setVisible(False)
        
        self.log_message("Web server stopped")
    
    def handle_error(self, error: str):
        """Handle server error."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.open_browser_button.setEnabled(False)
        self.status_label.setText("Error")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.progress_bar.setVisible(False)
        
        self.log_message(f"Error: {error}")
        QMessageBox.critical(self, "Error", f"Server error: {error}")
    
    def log_message(self, message: str):
        """Add message to log."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Clear the log."""
        self.log_text.clear()
    
    def apply_styles(self):
        """Apply modern styling."""
        self.setStyleSheet("""
            QWidget {
                background-color: #1F1F1F;
                color: #CCCCCC;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #444444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background: #2F2F2F;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #CCCCCC;
            }
            QPushButton {
                background-color: #007bff;
                color: #CCCCCC;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #444444;
                border-radius: 4px;
                background: #2F2F2F;
                color: #CCCCCC;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #007bff;
                outline: none;
            }
            QSpinBox {
                padding: 8px;
                border: 1px solid #444444;
                border-radius: 4px;
                background: #2F2F2F;
                color: #CCCCCC;
                font-size: 12px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: #444444;
                border: none;
                border-radius: 2px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #555555;
            }
            QTextEdit {
                border: 1px solid #444444;
                border-radius: 4px;
                background: #2F2F2F;
                color: #CCCCCC;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
            QCheckBox {
                font-size: 12px;
                spacing: 8px;
                color: #CCCCCC;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background: #2F2F2F;
                border: 1px solid #444444;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background: #007bff;
                border: 1px solid #007bff;
            }
            QCheckBox::indicator:checked::after {
                content: "✓";
                color: #CCCCCC;
                font-weight: bold;
            }
            QLabel {
                font-size: 12px;
                color: #CCCCCC;
            }
            QProgressBar {
                border: 1px solid #444444;
                border-radius: 4px;
                text-align: center;
                background: #2F2F2F;
                color: #CCCCCC;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
        """) 