"""
Performance Optimization Tab

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2024 AI Coder Assistant Contributors
"""

"""
Performance Optimization Tab - Clean, modern interface for performance analysis.
"""

import concurrent.futures
import os
from typing import Any, Callable, Dict, Optional
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QFileDialog,
    QProgressBar,
)
from src.core.logging import LogManager
from src.utils.constants import (
    CPU_HIGH_THRESHOLD,
    CPU_MEDIUM_THRESHOLD,
    METRICS_UPDATE_INTERVAL_MS,
    CHAT_AREA_MAX_HEIGHT,
    DEFAULT_FONT_SIZE,
    LARGE_FONT_SIZE,
    BOLD_FONT_WEIGHT,
    NORMAL_FONT_WEIGHT,
    DEFAULT_TABLE_COLUMNS,
    DEFAULT_TABLE_ROW_HEIGHT,
    DEFAULT_TABLE_HEADER_HEIGHT,
    DEFAULT_FILE_FILTER,
    PYTHON_FILE_FILTER,
    PROGRESS_DIALOG_MAX_VALUE,
    PROGRESS_DIALOG_MIN_VALUE,
)


logger = LogManager().get_logger(__name__)


class OptimizationWorker(QObject):
    """Worker class for optimization operations."""
    
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int, str)
    
    def __init__(self, operation: str, target_path: str, optimization_type: str):
        super().__init__()
        self.operation = operation
        self.target_path = target_path
        self.optimization_type = optimization_type
        self._cancelled = False
    
    def run(self):
        """Run the optimization operation."""
        try:
            result = performance_optimization_backend(
                self.operation,
                self.target_path,
                self.optimization_type,
                progress_callback=self._progress_callback,
                log_message_callback=self._log_callback,
            )
            if not self._cancelled:
                self.finished.emit(result)
        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))
    
    def _progress_callback(self, current: int, total: int, message: str):
        """Progress callback for the worker."""
        if not self._cancelled:
            self.progress.emit(current, total, message)
    
    def _log_callback(self, message: str):
        """Log callback for the worker."""
        logger.info(f"Optimization: {message}")
    
    def cancel(self):
        """Cancel the operation."""
        self._cancelled = True


"""

# MIGRATION NEEDED: Replace QThread subclass with ThreadManager pattern

# 1. Remove this QThread subclass.
# 2. Create a backend function for the threaded operation:
#    def backend_func(..., progress_callback=None, log_message_callback=None, cancellation_callback=None):
#        # do work, call callbacks, return result
# 3. In the UI, use:
#    from .worker_threads import start_worker
#    worker_id = start_worker("task_type", backend_func, ..., progress_callback=..., log_message_callback=...)
# 4. Connect ThreadManager signals to UI slots for progress, result, and error.

"""


class MetricsWidget(QWidget):
    """Widget for displaying performance metrics."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setup_ui()
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self.update_metrics)
        self.metrics_timer.start(METRICS_UPDATE_INTERVAL_MS)  # Update every 2 seconds

    def setup_ui(self) -> None:
        """Setup the metrics UI."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("System Performance Metrics")
        title.setFont(QFont("Arial", LARGE_FONT_SIZE, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Metrics display
        self.cpu_label = QLabel("CPU Usage: 0%")
        self.memory_label = QLabel("Memory Usage: 0%")
        self.disk_label = QLabel("Disk I/O: 0 MB/s")

        for label in [self.cpu_label, self.memory_label, self.disk_label]:
            label.setFont(QFont("Arial", DEFAULT_FONT_SIZE))
            layout.addWidget(label)

        layout.addStretch()

    @pyqtSlot()
    def update_metrics(self) -> None:
        """Update metrics display."""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()

            self.cpu_label.setText(f"CPU Usage: {cpu_percent:.1f}%")
            self.memory_label.setText(f"Memory Usage: {memory.percent:.1f}%")

            # Color coding using constants
            if cpu_percent > CPU_HIGH_THRESHOLD:
                self.cpu_label.setStyleSheet("color: red;")
            elif cpu_percent > CPU_MEDIUM_THRESHOLD:
                self.cpu_label.setStyleSheet("color: orange;")
            else:
                self.cpu_label.setStyleSheet("color: green;")

        except Exception as e:
            logger.error(f"Error updating metrics: {e}")


class AnalysisWidget(QWidget):
    """Widget for code performance analysis."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the analysis widget."""
        super().__init__(parent)
        self.worker_id: Optional[str] = None
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the analysis UI."""
        layout = QVBoxLayout(self)

        # File/Directory selection
        selection_group = QGroupBox("Analysis Target")
        selection_layout = QVBoxLayout(selection_group)

        # File selection
        file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select a file to analyze...")
        file_layout.addWidget(self.file_path_edit)

        self.browse_file_button = QPushButton("Browse File")
        self.browse_file_button.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_file_button)

        selection_layout.addLayout(file_layout)

        # Directory selection
        dir_layout = QHBoxLayout()
        self.dir_path_edit = QLineEdit()
        self.dir_path_edit.setPlaceholderText(
            "Select a project directory to analyze..."
        )
        dir_layout.addWidget(self.dir_path_edit)

        self.browse_dir_button = QPushButton("Browse Directory")
        self.browse_dir_button.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.browse_dir_button)

        selection_layout.addLayout(dir_layout)

        # Analyze button
        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.clicked.connect(self.analyze_target)
        selection_layout.addWidget(self.analyze_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(PROGRESS_DIALOG_MIN_VALUE, PROGRESS_DIALOG_MAX_VALUE)
        selection_layout.addWidget(self.progress_bar)

        layout.addWidget(selection_group)

        # Results
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)

        # Optimization score
        score_layout = QHBoxLayout()
        score_layout.addWidget(QLabel("Optimization Score:"))
        self.score_label = QLabel("N/A")
        self.score_label.setFont(QFont("Arial", DEFAULT_FONT_SIZE, QFont.Weight.Bold))
        score_layout.addWidget(self.score_label)
        score_layout.addStretch()
        results_layout.addLayout(score_layout)

        # Issues table
        self.issues_table = QTableWidget()
        self.issues_table.setColumnCount(DEFAULT_TABLE_COLUMNS)
        self.issues_table.setHorizontalHeaderLabels(
            ["Line", "Type", "Severity", "Description"]
        )
        header = self.issues_table.horizontalHeader()
        if header:  # Check if header exists
            header.setStretchLastSection(True)
            header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
            header.setFixedHeight(DEFAULT_TABLE_HEADER_HEIGHT)
        
        self.issues_table.setAlternatingRowColors(True)
        self.issues_table.setRowHeight(0, DEFAULT_TABLE_ROW_HEIGHT)
        results_layout.addWidget(self.issues_table)

        layout.addWidget(results_group)

    def browse_file(self) -> None:
        """Browse for a file to analyze."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", f"{PYTHON_FILE_FILTER};{DEFAULT_FILE_FILTER}"
        )
        if file_path:
            self.file_path_edit.setText(file_path)

    def browse_directory(self) -> None:
        """Browse for a directory to analyze."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.dir_path_edit.setText(dir_path)

    def analyze_target(self) -> None:
        """Analyze the selected target."""
        file_path = self.file_path_edit.text().strip()
        dir_path = self.dir_path_edit.text().strip()

        if not file_path and not dir_path:
            self.show_error("Please select a file or directory to analyze.")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(PROGRESS_DIALOG_MIN_VALUE)
        self.analyze_button.setEnabled(False)

        # Use ThreadPoolExecutor for background processing
        from concurrent.futures import ThreadPoolExecutor
        executor = ThreadPoolExecutor(max_workers=1)
        
        if file_path:
            # Analyze single file
            future = executor.submit(
                analyze_file_performance_backend,
                file_path,
                progress_callback=self._progress_callback,
                log_callback=self._log_callback,
            )
        else:
            # Analyze directory
            future = executor.submit(
                analyze_directory_performance_backend,
                dir_path,
                progress_callback=self._progress_callback,
                log_callback=self._log_callback,
            )
        
        # Store the future for cancellation if needed
        self._current_future = future
        future.add_done_callback(self._on_analysis_complete)

    def _progress_callback(self, current: int, total: int, message: str):
        """Progress callback for the analysis."""
        # Use QTimer.singleShot to update UI from main thread
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.progress_bar.setValue(current))

    def _log_callback(self, message: str):
        """Log callback for the analysis."""
        logger.info(f"Analysis: {message}")

    def _on_analysis_complete(self, future):
        """Handle analysis completion."""
        try:
            result = future.result()
            # Use QTimer.singleShot to update UI from main thread
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.show_analysis_result(result))
        except Exception as e:
            # Use QTimer.singleShot to update UI from main thread
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.show_error(str(e)))

    @pyqtSlot(str, int, int, str)
    def update_progress_slot(
        self, worker_id: str, current: int, total: int, message: str
    ) -> None:
        """Update progress bar."""
        if worker_id == self.worker_id:
            self.progress_bar.setValue(current)

    def handle_log_message(self, message: str) -> None:
        """Handle log messages."""
        logger.info(f"Analysis: {message}")

    @pyqtSlot(str, object)
    def on_worker_finished(self, worker_id: str, result: Any):
        """Handle worker completion."""
        if worker_id == self.worker_id:
            self.show_analysis_result(result)

    @pyqtSlot(str, str)
    def on_worker_error(self, worker_id: str, error_msg: str):
        """Handle worker error."""
        if worker_id == self.worker_id:
            self.show_error(error_msg)

    def show_analysis_result(self, result: Dict[str, Any]) -> None:
        """Display analysis results."""
        self.progress_bar.setVisible(False)
        self.analyze_button.setEnabled(True)

        if not result:
            self.show_error("No analysis results available.")
            return

        # Update score
        score = result.get("score", 0)
        self.score_label.setText(f"{score:.1f}/100")

        # Update issues table
        issues = result.get("issues", [])
        self.issues_table.setRowCount(len(issues))

        for i, issue in enumerate(issues):
            self.issues_table.setItem(i, 0, QTableWidgetItem(str(issue.get("line", ""))))
            self.issues_table.setItem(i, 1, QTableWidgetItem(issue.get("type", "")))
            self.issues_table.setItem(i, 2, QTableWidgetItem(issue.get("severity", "")))
            self.issues_table.setItem(i, 3, QTableWidgetItem(issue.get("description", "")))

        # Color code severity
        for i in range(self.issues_table.rowCount()):
            severity_item = self.issues_table.item(i, 2)
            if severity_item:
                severity = severity_item.text().lower()
                if severity == "high":
                    severity_item.setBackground(QColor(255, 200, 200))
                elif severity == "medium":
                    severity_item.setBackground(QColor(255, 255, 200))
                elif severity == "low":
                    severity_item.setBackground(QColor(200, 255, 200))

    def show_error(self, error: str) -> None:
        """Show error message."""
        self.progress_bar.setVisible(False)
        self.analyze_button.setEnabled(True)
        logger.error(f"Analysis error: {error}")


class ProfilingWidget(QWidget):
    """Widget for performance profiling."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the profiling UI."""
        layout = QVBoxLayout(self)

        # Profiling controls
        controls_group = QGroupBox("Profiling Controls")
        controls_layout = QVBoxLayout(controls_group)

        # Process selection
        process_layout = QHBoxLayout()
        process_layout.addWidget(QLabel("Target Process:"))
        self.process_combo = QComboBox()
        self.process_combo.addItem("Current Process")
        process_layout.addWidget(self.process_combo)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_processes)
        process_layout.addWidget(self.refresh_button)
        controls_layout.addLayout(process_layout)

        # Profiling buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Profiling")
        self.start_button.clicked.connect(self.start_profiling)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Profiling")
        self.stop_button.clicked.connect(self.stop_profiling)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        controls_layout.addLayout(button_layout)
        layout.addWidget(controls_group)

        # Status
        status_group = QGroupBox("Profiling Status")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("Ready to start profiling")
        status_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)

        layout.addWidget(status_group)

        # Profile output
        output_group = QGroupBox("Profile Output")
        output_layout = QVBoxLayout(output_group)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(200)
        output_layout.addWidget(self.output_text)

        layout.addWidget(output_group)

    def refresh_processes(self):
        """Refresh the process list."""
        try:
            import psutil

            self.process_combo.clear()
            self.process_combo.addItem("Current Process")

            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    self.process_combo.addItem(
                        f"{proc.info['name']} (PID: {proc.info['pid']})"
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"Error refreshing processes: {e}")

    def start_profiling(self):
        """Start profiling."""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Profiling active...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.output_text.append("Profiling started...")

    def stop_profiling(self):
        """Stop profiling."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Profiling stopped")
        self.progress_bar.setVisible(False)
        self.output_text.append("Profiling stopped.")


class PerformanceOptimizationTab(QWidget):
    """Main Performance Optimization tab with clean, modern design."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.setup_ui()
        self.load_sample_data()
        self.apply_styles()

    def setup_ui(self):
        """Setup the main UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Title
        title = QLabel("Performance Optimization")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Description
        description = QLabel(
            "Analyze code performance, monitor system metrics, and optimize your applications."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)

        # Tab widget for different features
        self.tab_widget = QTabWidget()

        # System Metrics Tab
        self.metrics_widget = MetricsWidget()
        self.tab_widget.addTab(self.metrics_widget, "System Metrics")

        # Code Analysis Tab
        self.analysis_widget = AnalysisWidget()
        self.tab_widget.addTab(self.analysis_widget, "Code Analysis")

        # Profiling Tab
        self.profiling_widget = ProfilingWidget()
        self.tab_widget.addTab(self.profiling_widget, "Profiling")

        layout.addWidget(self.tab_widget)

    def apply_styles(self):
        """Apply modern styling."""
        self.setStyleSheet(
            """
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
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
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
            }
            QLineEdit:focus {
                border-color: #007bff;
                outline: none;
            }
            QTextEdit {
                border: 1px solid #444444;
                border-radius: 4px;
                background: #2F2F2F;
                color: #CCCCCC;
                padding: 8px;
            }
            QTableWidget {
                border: 1px solid #444444;
                border-radius: 4px;
                background: #2F2F2F;
                color: #CCCCCC;
                gridline-color: #444444;
            }
            QTableWidget::item {
                padding: 4px;
                color: #CCCCCC;
            }
            QTableWidget::item:selected {
                background-color: #3F3F3F;
                color: #CCCCCC;
            }
            QHeaderView::section {
                background-color: #1F1F1F;
                color: #CCCCCC;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #444444;
                font-weight: bold;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #444444;
                border-radius: 4px;
                background: #2F2F2F;
                color: #CCCCCC;
            }
            QComboBox:focus {
                border-color: #007bff;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #CCCCCC;
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
            QTabWidget::pane {
                border: 1px solid #444444;
                background: #1F1F1F;
            }
            QTabBar::tab {
                background: #2F2F2F;
                color: #CCCCCC;
                padding: 8px 16px;
                border: 1px solid #444444;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #1F1F1F;
                border-bottom: 1px solid #1F1F1F;
            }
            QTabBar::tab:hover {
                background: #3F3F3F;
            }
        """
        )

    def start_optimization(self):
        """Start performance optimization analysis."""
        if not self.validate_inputs():
            return

        self.optimize_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Starting optimization analysis...")

        # Start optimization using ThreadPoolExecutor
        future = self.executor.submit(
            performance_optimization_backend,
            "analyze",
            target_path=self.target_path.text(),
            optimization_type=self.optimization_type.currentText(),
            progress_callback=self.update_progress,
            log_message_callback=self.handle_error,
        )
        future.add_done_callback(self._on_optimization_complete)

    def _on_optimization_complete(self, future):
        def update_ui():
            try:
                result = future.result()
                self.display_results(result)
                self.optimize_btn.setEnabled(True)
                self.progress_bar.setVisible(False)
                self.status_label.setText("Optimization analysis complete")
            except Exception as e:
                self.handle_error(f"Optimization failed: {e}")
                self.optimize_btn.setEnabled(True)
                self.progress_bar.setVisible(False)

        QTimer.singleShot(0, update_ui)

    def load_sample_data(self):
        """Load sample data for demonstration."""
        # This method will be implemented when the full UI is added
        pass


# Backend functions for ThreadManager
def analyze_directory_performance_backend(
    dir_path: str,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    log_callback: Optional[Callable[[str], None]] = None,
    cancellation_callback: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    """Analyze performance of all Python files in a directory."""
    import time

    if progress_callback:
        progress_callback(0, 100, "Starting directory analysis...")

    if log_callback:
        log_callback(f"Analyzing directory: {dir_path}")

    # Mock analysis for now
    time.sleep(1)

    if progress_callback:
        progress_callback(100, 100, "Analysis complete")

    return {
        "directory_path": dir_path,
        "summary": {"average_score": 85.5, "files_analyzed": 10, "total_issues": 5},
        "issues": [
            {
                "line": 42,
                "type": "Performance",
                "severity": "Medium",
                "description": "Consider using list comprehension instead of map()",
            }
        ],
    }


def analyze_file_performance_backend(
    file_path: str,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    log_callback: Optional[Callable[[str], None]] = None,
    cancellation_callback: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    """Analyze performance of a single Python file."""
    import time

    if progress_callback:
        progress_callback(0, 100, "Starting file analysis...")

    if log_callback:
        log_callback(f"Analyzing file: {file_path}")

    # Mock analysis for now
    time.sleep(1)

    if progress_callback:
        progress_callback(100, 100, "Analysis complete")

    return {
        "file_path": file_path,
        "score": 85.5,
        "issues": [
            {
                "line": 42,
                "type": "Performance",
                "severity": "Medium",
                "description": "Consider using list comprehension instead of map()",
            }
        ],
    }


@pyqtSlot(object)
def _on_optimization_complete(self, result: Optional[Dict[str, Any]]):
    """Callback for when optimization is complete."""
    try:
        _ = self.isVisible()
    except RuntimeError:
        return  # Widget is deleted

    self.progress_bar.hide()
    if result and result.get("success"):
        self.results_text.setPlainText(result.get("optimized_code", ""))
        QMessageBox.information(self, "Success", "Optimization complete.")
    else:
        error = (
            result.get("error", "An unknown error occurred.")
            if result
            else "An unknown error occurred."
        )
        QMessageBox.critical(
            self, "Optimization Failed", f"Optimization failed: {error}"
        )


# Stub backend function
def performance_optimization_backend(
    operation: str,
    target_path: str,
    optimization_type: str,
    progress_callback=None,
    log_message_callback=None,
):
    """Stub function for performance optimization backend."""
    import time

    time.sleep(1)
    return {"success": True, "result": "Performance optimization completed"}
