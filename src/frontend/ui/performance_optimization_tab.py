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

import os
from typing import Optional, Any, Dict, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, QPushButton,
    QLabel, QTextEdit, QProgressBar, QFileDialog, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont
from core.logging import LogManager
import concurrent.futures

logger = LogManager().get_logger(__name__)


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
        self.metrics_timer.start(2000)  # Update every 2 seconds
    
    def setup_ui(self) -> None:
        """Setup the metrics UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("System Performance Metrics")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Metrics display
        self.cpu_label = QLabel("CPU Usage: 0%")
        self.memory_label = QLabel("Memory Usage: 0%")
        self.disk_label = QLabel("Disk I/O: 0 MB/s")
        
        for label in [self.cpu_label, self.memory_label, self.disk_label]:
            label.setFont(QFont("Arial", 12))
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
            
            # Color coding
            if cpu_percent > 80:
                self.cpu_label.setStyleSheet("color: red;")
            elif cpu_percent > 60:
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
        self.dir_path_edit.setPlaceholderText("Select a project directory to analyze...")
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
        selection_layout.addWidget(self.progress_bar)
        
        layout.addWidget(selection_group)
        
        # Results
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)
        
        # Optimization score
        score_layout = QHBoxLayout()
        score_layout.addWidget(QLabel("Optimization Score:"))
        self.score_label = QLabel("N/A")
        self.score_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        score_layout.addWidget(self.score_label)
        score_layout.addStretch()
        results_layout.addLayout(score_layout)
        
        # Issues table
        self.issues_table = QTableWidget()
        self.issues_table.setColumnCount(4)
        self.issues_table.setHorizontalHeaderLabels([
            "Line", "Type", "Severity", "Description"
        ])
        header = self.issues_table.horizontalHeader()
        if header:  # Check if header exists
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        results_layout.addWidget(self.issues_table)
        
        layout.addWidget(results_group)
    
    def browse_file(self) -> None:
        """Browse for a file to analyze."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Analyze", "",
            "Python Files (*.py);;All Files (*)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)
            self.dir_path_edit.clear()  # Clear directory path when file is selected
    
    def browse_directory(self) -> None:
        """Browse for a directory to analyze."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Project Directory to Analyze"
        )
        if dir_path:
            self.dir_path_edit.setText(dir_path)
            self.file_path_edit.clear()  # Clear file path when directory is selected
    
    def analyze_target(self) -> None:
        """Analyze the selected file or directory."""
        file_path = self.file_path_edit.text()
        dir_path = self.dir_path_edit.text()
        
        if not file_path and not dir_path:
            QMessageBox.warning(self, "Warning", "Please select a file or directory to analyze.")
            return
        
        if file_path and dir_path:
            QMessageBox.warning(self, "Warning", "Please select either a file or directory, not both.")
            return

        target_path = file_path or dir_path
        backend_func = analyze_file_performance_backend if file_path else analyze_directory_performance_backend

        if not os.path.exists(target_path):
            QMessageBox.warning(self, "Warning", "Selected path does not exist.")
            return
        
        self.analyze_button.setEnabled(False)
        self.analyze_button.setText("Analyzing...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        try:
            self.worker_id = 'performance_optimization'
            worker = self.thread_manager.start_worker(
                self.worker_id,
                backend_func,
                target_path
            )
            worker.progress.connect(self.update_progress_slot)
            worker.finished.connect(self.on_worker_finished)
            worker.error.connect(self.on_worker_error)
            worker.log_message.connect(self.handle_log_message)
            
        except Exception as e:
            self.analyze_button.setEnabled(True)
            self.analyze_button.setText("Analyze")
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Failed to start analysis: {str(e)}")
    
    @pyqtSlot(str, int, int, str)
    def update_progress_slot(self, worker_id: str, current: int, total: int, message: str) -> None:
        """Update progress information."""
        if worker_id == self.worker_id:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
    
    def handle_log_message(self, message: str) -> None:
        """Handle log messages from the worker."""
        logger.info(f"Analysis log: {message}")
    
    @pyqtSlot(str, object)
    def on_worker_finished(self, worker_id: str, result: Any):
        if self.worker_id == worker_id:
            self.show_analysis_result(result)

    @pyqtSlot(str, str)
    def on_worker_error(self, worker_id: str, error_msg: str):
        if self.worker_id == worker_id:
            self.show_error(error_msg)

    def show_analysis_result(self, result: Dict[str, Any]) -> None:
        """Show analysis results."""
        self.progress_bar.setVisible(False)
        try:
            self.analyze_button.setEnabled(True)
            self.analyze_button.setText("Analyze")
            
            if not isinstance(result, dict):
                raise ValueError("Invalid result format")
            
            if "error" in result:
                raise ValueError(result["error"])
            
            # Handle directory analysis
            if "directory_path" in result:
                self.score_label.setText(f"{result['summary']['average_score']:.1f}")
                
                # Clear and update issues table
                self.issues_table.setRowCount(0)
                
                for issue in result["issues"]:
                    row = self.issues_table.rowCount()
                    self.issues_table.insertRow(row)
                    
                    self.issues_table.setItem(row, 0, QTableWidgetItem(str(issue["line"])))
                    self.issues_table.setItem(row, 1, QTableWidgetItem(issue["type"]))
                    self.issues_table.setItem(row, 2, QTableWidgetItem(issue["severity"]))
                    self.issues_table.setItem(row, 3, QTableWidgetItem(issue["description"]))
            
            # Handle file analysis
            else:
                self.score_label.setText(f"{result['score']:.1f}")
                
                # Clear and update issues table
                self.issues_table.setRowCount(0)
                
                for issue in result["issues"]:
                    row = self.issues_table.rowCount()
                    self.issues_table.insertRow(row)
                    
                    self.issues_table.setItem(row, 0, QTableWidgetItem(str(issue["line"])))
                    self.issues_table.setItem(row, 1, QTableWidgetItem(issue["type"]))
                    self.issues_table.setItem(row, 2, QTableWidgetItem(issue["severity"]))
                    self.issues_table.setItem(row, 3, QTableWidgetItem(issue["description"]))
        
        except Exception as e:
            self.show_error(str(e))
    
    def show_error(self, error: str) -> None:
        """Show error message."""
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("Analyze")
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", error)


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
            
            for proc in psutil.process_iter(['pid', 'name']):
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
        """) 

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
            'analyze',
            target_path=self.target_path.text(),
            optimization_type=self.optimization_type.currentText(),
            progress_callback=self.update_progress,
            log_message_callback=self.handle_error
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
def analyze_directory_performance_backend(dir_path: str, progress_callback: Optional[Callable[[int, int, str], None]] = None, log_callback: Optional[Callable[[str], None]] = None, cancellation_callback: Optional[Callable[[], bool]] = None) -> Dict[str, Any]:
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
        "summary": {
            "average_score": 85.5,
            "files_analyzed": 10,
            "total_issues": 5
        },
        "issues": [
            {
                "line": 42,
                "type": "Performance",
                "severity": "Medium",
                "description": "Consider using list comprehension instead of map()"
            }
        ]
    }

def analyze_file_performance_backend(file_path: str, progress_callback: Optional[Callable[[int, int, str], None]] = None, log_callback: Optional[Callable[[str], None]] = None, cancellation_callback: Optional[Callable[[], bool]] = None) -> Dict[str, Any]:
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
                "description": "Consider using list comprehension instead of map()"
            }
        ]
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
        error = result.get("error", "An unknown error occurred.") if result else "An unknown error occurred."
        QMessageBox.critical(self, "Optimization Failed", f"Optimization failed: {error}") 

# Stub backend function
def performance_optimization_backend(operation: str, target_path: str, optimization_type: str, progress_callback=None, log_message_callback=None):
    """Stub function for performance optimization backend."""
    import time
    time.sleep(1)
    return {"success": True, "result": "Performance optimization completed"} 