"""
Web Server Mode Tab - Clean, modern interface for web server management.
"""

import logging
import webbrowser
import concurrent.futures
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QTextEdit, QLineEdit, QSpinBox, QCheckBox, QFormLayout,
    QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont
from src.backend.utils.constants import TEST_PORT

logger = logging.getLogger(__name__)

# Backend functions for ThreadManager
def web_server_backend(operation: str, **kwargs):
    import time
    progress_callback = kwargs.get('progress_callback')
    log_message_callback = kwargs.get('log_message_callback')
    cancellation_callback = kwargs.get('cancellation_callback')
    operation_args = kwargs.get('operation_args', {})
    
    steps = [
        ("Initializing web server...", 1),
        ("Starting server process...", 2),
        ("Configuring routes...", 3),
        ("Server ready...", 4),
        ("Operation complete!", 5),
    ]
    total = len(steps)
    for i, (msg, step) in enumerate(steps, 1):
        if cancellation_callback and cancellation_callback():
            if log_message_callback:
                log_message_callback("Web server operation cancelled.")
            return None
        if progress_callback:
            progress_callback(step, total, msg)
        time.sleep(0.2)
    
    # Return mock result based on operation
    if operation == "start_server":
        result = {
            'success': True,
            'server_url': f"http://{operation_args.get('host', 'localhost')}:{operation_args.get('port', 8080)}",
            'status': 'running',
            'pid': 12345
        }
    elif operation == "stop_server":
        result = {
            'success': True,
            'status': 'stopped'
        }
    elif operation == "restart_server":
        result = {
            'success': True,
            'server_url': f"http://{operation_args.get('host', 'localhost')}:{operation_args.get('port', 8080)}",
            'status': 'running',
            'pid': 12346
        }
    else:
        result = {
            'success': True,
            'operation': operation,
            'status': 'complete'
        }
    return result

class WebServerTab(QWidget):
    """Main Web Server Mode tab with clean, modern design."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.executor = concurrent.futures.ThreadPoolExecutor()
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
        self.port_spin.setValue(TEST_PORT)
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
        # Remove old worker signal connections - using new threading pattern
        pass
    
    def start_server(self):
        """Start the web server."""
        if not self.validate_inputs():
            return
        
        self.start_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Starting web server...")
        
        # Start server using ThreadPoolExecutor
        future = self.executor.submit(
            web_server_backend,
            'start',
            port=int(self.port_spin.value()),
            host=self.host_edit.text(),
            progress_callback=self.update_progress,
            log_message_callback=self.handle_error
        )
        future.add_done_callback(self._on_server_start_complete)

    def _on_server_start_complete(self, future):
        """Handle server start completion."""
        try:
            result = future.result()
            self.handle_server_result(result)
            self.start_button.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.status_label.setText("Server started successfully")
        except Exception as e:
            self.handle_error(f"Server start failed: {e}")
            self.start_button.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def stop_server(self):
        """Stop the web server."""
        try:
            self.stop_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Start stop using ThreadPoolExecutor
            future = self.executor.submit(
                web_server_backend,
                'stop',
                progress_callback=self.update_progress,
                log_message_callback=self.handle_log_message
            )
            future.add_done_callback(self._on_server_stop_complete)
            
        except Exception as e:
            logger.error(f"Error stopping server: {e}")
            QMessageBox.warning(self, "Error", f"Failed to stop server: {e}")

    def _on_server_stop_complete(self, future):
        """Handle server stop completion."""
        try:
            result = future.result()
            self.handle_server_stopped()
        except Exception as e:
            self.handle_error(f"Server stop failed: {e}")
            self.stop_button.setEnabled(True)
            self.progress_bar.setVisible(False)
    
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

    def _on_worker_progress(self, worker_id, current, total, message):
        if hasattr(self, 'worker_id') and worker_id == self.worker_id:
            self.update_progress(current, total, message)

    def _on_worker_finished(self, worker_id):
        if hasattr(self, 'worker_id') and worker_id == self.worker_id:
            result = web_server_backend('mock_operation')
            self.handle_server_operation_complete(result)
            self.progress_bar.setVisible(False)

    def _on_worker_error(self, worker_id, error):
        if hasattr(self, 'worker_id') and worker_id == self.worker_id:
            self.show_error(error)
            self.progress_bar.setVisible(False)

    def handle_log_message(self, message):
        """Handle log messages from worker."""
        self.log_message(message)

    def handle_server_operation_complete(self, result):
        """Handle server operation completion."""
        if result['success']:
            if result.get('status') == 'running':
                self.status_label.setText("Running")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.open_browser_button.setEnabled(True)
                self.log_message("Server started successfully")
            elif result.get('status') == 'stopped':
                self.status_label.setText("Stopped")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.open_browser_button.setEnabled(False)
                self.log_message("Server stopped successfully")
            QMessageBox.information(self, "Success", "Server operation completed successfully")
        else:
            QMessageBox.warning(self, "Error", "Server operation failed")

    def show_error(self, error):
        """Handle server operation error."""
        QMessageBox.critical(self, "Error", f"Server operation failed: {error}")
        self.log_message(f"Error: {error}")

    def update_progress(self, current, total, message):
        """Update progress bar."""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(int((current / total) * 100))
            if hasattr(self, 'status_label'):
                self.status_label.setText(message)

    @pyqtSlot(object)
    def _on_server_control_complete(self, result):
        """Callback for server control actions."""
        try:
            _ = self.isVisible()
        except RuntimeError:
            return  # Widget is deleted

        self.start_button.setDisabled(False)
        self.stop_button.setDisabled(False)
        
        if result and result.get("success"):
            self.log_message(result.get("message", "Operation successful."))
            self.update_server_status()
        else:
            error = result.get("error", "An unknown error occurred.")
            self.log_message(f"Error: {error}")
            QMessageBox.critical(self, "Server Error", error) 