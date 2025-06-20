"""Scanner UI component for AI Coder Assistant."""

from typing import Optional
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QPushButton, QProgressBar
from PyQt6.QtCore import pyqtSlot, QTimer, QMutex, QMutexLocker

from frontend.components.base_component import BaseComponent, ComponentState
from core.events import Event, EventType
from core.logging import LogManager
from core.error import ErrorSeverity

class ScannerComponent(BaseComponent):
    """UI component for code scanning functionality with thread safety."""
    def __init__(self, parent: Optional[object] = None):
        super().__init__(parent)
        self._logger = LogManager().get_logger("ScannerComponent")
        self._progress = 0
        self._mutex = QMutex()  # Add mutex for thread safety
        self._ui_update_timer = QTimer()  # Timer for queuing UI updates
        self._ui_update_timer.timeout.connect(self._process_ui_updates)
        self._ui_update_timer.start(50)  # Process UI updates every 50ms
        self._pending_ui_updates = []  # Queue for UI updates
        
        self._setup_ui()
        self.subscribe_to_event(EventType.SCAN_PROGRESS, self.on_scan_progress)
        self.subscribe_to_event(EventType.SCAN_COMPLETED, self.on_scan_completed)
        self.subscribe_to_event(EventType.SCAN_FAILED, self.on_scan_failed)

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.status_label = QLabel("Ready to scan.")
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.scan_button = QPushButton("Start Scan")
        self.scan_button.clicked.connect(self.start_scan)
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.scan_button)
        self.setLayout(self.layout)

    @pyqtSlot()
    def start_scan(self):
        """Start scan operation (called on main thread)."""
        self._queue_ui_update('set_status', "Scanning...")
        self._queue_ui_update('set_progress', 0)
        self.state = ComponentState.ACTIVATING
        # Publish event to start scan (actual scan logic handled by backend)
        self.publish_event(Event(type=EventType.SCAN_STARTED, data={"source": "ui"}))

    def on_scan_progress(self, event: Event):
        """Handle scan progress event (thread-safe)."""
        progress = event.data.get("progress", 0) if event.data else 0
        self._queue_ui_update('set_progress', progress)
        self._queue_ui_update('set_status', f"Scanning... {progress}%")
        self._logger.info(f"Scan progress: {progress}%")

    def on_scan_completed(self, event: Event):
        """Handle scan completion event (thread-safe)."""
        self._queue_ui_update('set_progress', 100)
        self._queue_ui_update('set_status', "Scan completed!")
        self.state = ComponentState.DEACTIVATED
        self._logger.info("Scan completed.")

    def on_scan_failed(self, event: Event):
        """Handle scan failure event (thread-safe)."""
        error_msg = event.data.get("error", "Unknown error") if event.data else "Unknown error"
        self._queue_ui_update('set_status', f"Scan failed: {error_msg}")
        self.state = ComponentState.ERROR
        self._logger.error(f"Scan failed: {error_msg}")
        self.error_occurred.emit(error_msg, ErrorSeverity.ERROR)

    def _queue_ui_update(self, update_type: str, *args):
        """Queue UI update for processing on main thread."""
        try:
            with QMutexLocker(self._mutex):
                self._pending_ui_updates.append((update_type, args))
        except Exception as e:
            self._logger.error(f"Error queuing UI update: {e}")

    def _process_ui_updates(self):
        """Process queued UI updates on main thread."""
        try:
            with QMutexLocker(self._mutex):
                updates = self._pending_ui_updates.copy()
                self._pending_ui_updates.clear()
            
            # Process all queued updates
            for update_type, args in updates:
                self._apply_ui_update(update_type, *args)
                
        except Exception as e:
            self._logger.error(f"Error processing UI updates: {e}")

    def _apply_ui_update(self, update_type: str, *args):
        """Apply UI update (called on main thread)."""
        try:
            if update_type == 'set_status':
                self.status_label.setText(args[0])
            elif update_type == 'set_progress':
                self.progress_bar.setValue(args[0])
            elif update_type == 'set_button_enabled':
                self.scan_button.setEnabled(args[0])
            else:
                self._logger.warning(f"Unknown UI update type: {update_type}")
        except Exception as e:
            self._logger.error(f"Error applying UI update {update_type}: {e}")

    async def initialize(self) -> bool:
        self.state = ComponentState.INITIALIZED
        return True

    async def activate(self) -> bool:
        self.state = ComponentState.ACTIVE
        return True

    async def deactivate(self) -> bool:
        self.state = ComponentState.DEACTIVATED
        return True 