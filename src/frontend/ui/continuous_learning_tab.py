"""
continuous_learning_tab.py

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
Continuous Learning Tab Widgets
Provides GUI components for continuous learning management and monitoring.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QLineEdit, QMessageBox, QGroupBox, 
    QCheckBox, QSpinBox, QListWidget, QListWidgetItem, QProgressBar, 
    QTabWidget, QSplitter, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QDateEdit, QCalendarWidget, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QTimer
from PyQt6.QtGui import QFont, QTextCursor

from backend.services.continuous_learning import (
    get_continuous_learning_service,
    FeedbackType,
    DataQuality,
    ContinuousLearningService
)
from backend.utils.constants import (
    WAIT_TIMEOUT_SHORT_MS,
    CONTINUOUS_LEARNING_DB_PATH,
    CONTINUOUS_LEARNING_MIN_INPUT_LENGTH,
    CONTINUOUS_LEARNING_MIN_OUTPUT_LENGTH,
    CONTINUOUS_LEARNING_MAX_INPUT_LENGTH,
    CONTINUOUS_LEARNING_MAX_OUTPUT_LENGTH,
    CONTINUOUS_LEARNING_REPLAY_BUFFER_SIZE,
    CONTINUOUS_LEARNING_QUALITY_THRESHOLD,
    CONTINUOUS_LEARNING_BATCH_SIZE,
    CONTINUOUS_LEARNING_UPDATE_INTERVAL_HOURS
)

logger = logging.getLogger(__name__)


class ContinuousLearningWorker(QThread):
    """Worker thread for continuous learning operations."""
    
    progress_updated = pyqtSignal(int, int, str)
    operation_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, operation: str, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs
    
    def run(self):
        try:
            service = get_continuous_learning_service()
            
            if self.operation == "trigger_update":
                batch_size = self.kwargs.get('batch_size', 100)
                force_update = self.kwargs.get('force_update', False)
                
                self.progress_updated.emit(1, 3, "Checking data availability...")
                self.msleep(WAIT_TIMEOUT_SHORT_MS)
                
                self.progress_updated.emit(2, 3, "Triggering model update...")
                update_id = service.trigger_model_update(batch_size=batch_size, force_update=force_update)
                
                self.progress_updated.emit(3, 3, "Update completed!")
                
                result = {
                    'success': update_id is not None,
                    'update_id': update_id,
                    'message': f"Model update {'triggered' if update_id else 'failed'}"
                }
                
            elif self.operation == "get_stats":
                start_date = self.kwargs.get('start_date')
                end_date = self.kwargs.get('end_date')
                
                self.progress_updated.emit(1, 2, "Collecting statistics...")
                stats = service.get_feedback_stats(start_date=start_date, end_date=end_date)
                
                self.progress_updated.emit(2, 2, "Statistics collected!")
                
                result = {
                    'success': True,
                    'stats': stats
                }
                
            elif self.operation == "export_data":
                output_path = self.kwargs.get('output_path')
                start_date = self.kwargs.get('start_date')
                end_date = self.kwargs.get('end_date')
                
                self.progress_updated.emit(1, 2, "Exporting data...")
                service.export_data(output_path, start_date=start_date, end_date=end_date)
                
                self.progress_updated.emit(2, 2, "Data exported!")
                
                result = {
                    'success': True,
                    'output_path': output_path
                }
                
            elif self.operation == "cleanup_data":
                days_to_keep = self.kwargs.get('days_to_keep', 30)
                
                self.progress_updated.emit(1, 2, "Cleaning up old data...")
                deleted_count = service.cleanup_old_data(days_to_keep)
                
                self.progress_updated.emit(2, 2, "Cleanup completed!")
                
                result = {
                    'success': True,
                    'deleted_count': deleted_count
                }
            
            self.operation_completed.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class ContinuousLearningTab(QWidget):
    """Main continuous learning management tab."""
    
    def __init__(self):
        super().__init__()
        self.service = get_continuous_learning_service()
        self.worker = None
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.refresh_stats)
        self.stats_timer.start(30000)  # Refresh every 30 seconds
        
        self.init_ui()
        self.refresh_stats()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget for different sections
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Add tabs
        self.tab_widget.addTab(self.create_dashboard_tab(), "Dashboard")
        self.tab_widget.addTab(self.create_feedback_tab(), "Feedback Collection")
        self.tab_widget.addTab(self.create_model_management_tab(), "Model Management")
        self.tab_widget.addTab(self.create_admin_tab(), "Admin")
    
    def create_dashboard_tab(self) -> QWidget:
        """Create the main dashboard tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Statistics overview
        stats_group = QGroupBox("Statistics Overview")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.stats_table.setMaximumHeight(200)
        stats_layout.addWidget(self.stats_table)
        
        layout.addWidget(stats_group)
        
        # Recent activity
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout(activity_group)
        
        self.activity_list = QListWidget()
        self.activity_list.setMaximumHeight(150)
        activity_layout.addWidget(self.activity_list)
        
        layout.addWidget(activity_group)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        self.refresh_btn = QPushButton("Refresh Stats")
        self.refresh_btn.clicked.connect(self.refresh_stats)
        actions_layout.addWidget(self.refresh_btn)
        
        self.trigger_update_btn = QPushButton("Trigger Model Update")
        self.trigger_update_btn.clicked.connect(self.trigger_model_update)
        actions_layout.addWidget(self.trigger_update_btn)
        
        self.export_btn = QPushButton("Export Data")
        self.export_btn.clicked.connect(self.export_data)
        actions_layout.addWidget(self.export_btn)
        
        layout.addWidget(actions_group)
        
        layout.addStretch()
        return widget
    
    def create_feedback_tab(self) -> QWidget:
        """Create the feedback collection tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Feedback collection form
        form_group = QGroupBox("Collect Feedback")
        form_layout = QVBoxLayout(form_group)
        
        # Feedback type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Feedback Type:"))
        self.feedback_type_combo = QComboBox()
        self.feedback_type_combo.addItems([ft.value for ft in FeedbackType])
        type_layout.addWidget(self.feedback_type_combo)
        form_layout.addLayout(type_layout)
        
        # Original input
        form_layout.addWidget(QLabel("Original Input:"))
        self.original_input_edit = QTextEdit()
        self.original_input_edit.setMaximumHeight(100)
        form_layout.addWidget(self.original_input_edit)
        
        # Original output
        form_layout.addWidget(QLabel("Original Output:"))
        self.original_output_edit = QTextEdit()
        self.original_output_edit.setMaximumHeight(100)
        form_layout.addWidget(self.original_output_edit)
        
        # Corrected output
        form_layout.addWidget(QLabel("Corrected Output (Optional):"))
        self.corrected_output_edit = QTextEdit()
        self.corrected_output_edit.setMaximumHeight(100)
        form_layout.addWidget(self.corrected_output_edit)
        
        # User rating
        rating_layout = QHBoxLayout()
        rating_layout.addWidget(QLabel("User Rating (1-5):"))
        self.user_rating_spin = QSpinBox()
        self.user_rating_spin.setRange(1, 5)
        self.user_rating_spin.setValue(3)
        rating_layout.addWidget(self.user_rating_spin)
        form_layout.addLayout(rating_layout)
        
        # User comment
        form_layout.addWidget(QLabel("User Comment (Optional):"))
        self.user_comment_edit = QLineEdit()
        form_layout.addWidget(self.user_comment_edit)
        
        # Submit button
        self.submit_feedback_btn = QPushButton("Submit Feedback")
        self.submit_feedback_btn.clicked.connect(self.submit_feedback)
        form_layout.addWidget(self.submit_feedback_btn)
        
        layout.addWidget(form_group)
        
        # Feedback history
        history_group = QGroupBox("Recent Feedback")
        history_layout = QVBoxLayout(history_group)
        
        self.feedback_history_list = QListWidget()
        history_layout.addWidget(self.feedback_history_list)
        
        layout.addWidget(history_group)
        
        return widget
    
    def create_model_management_tab(self) -> QWidget:
        """Create the model management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Model update controls
        update_group = QGroupBox("Model Update Controls")
        update_layout = QVBoxLayout(update_group)
        
        # Batch size
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("Batch Size:"))
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(10, 1000)
        self.batch_size_spin.setValue(100)
        batch_layout.addWidget(self.batch_size_spin)
        update_layout.addLayout(batch_layout)
        
        # Force update checkbox
        self.force_update_check = QCheckBox("Force Update (ignore data requirements)")
        update_layout.addWidget(self.force_update_check)
        
        # Trigger update button
        self.trigger_update_btn2 = QPushButton("Trigger Model Update")
        self.trigger_update_btn2.clicked.connect(self.trigger_model_update)
        update_layout.addWidget(self.trigger_update_btn2)
        
        layout.addWidget(update_group)
        
        # Update history
        history_group = QGroupBox("Update History")
        history_layout = QVBoxLayout(history_group)
        
        self.update_history_table = QTableWidget()
        self.update_history_table.setColumnCount(5)
        self.update_history_table.setHorizontalHeaderLabels([
            "ID", "Timestamp", "Status", "Samples", "Performance"
        ])
        self.update_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        history_layout.addWidget(self.update_history_table)
        
        layout.addWidget(history_group)
        
        return widget
    
    def create_admin_tab(self) -> QWidget:
        """Create the admin tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Data management
        data_group = QGroupBox("Data Management")
        data_layout = QVBoxLayout(data_group)
        
        # Date range for operations
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Start Date:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(datetime.now().date() - timedelta(days=7))
        date_layout.addWidget(self.start_date_edit)
        
        date_layout.addWidget(QLabel("End Date:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(datetime.now().date())
        date_layout.addWidget(self.end_date_edit)
        data_layout.addLayout(date_layout)
        
        # Export data
        export_layout = QHBoxLayout()
        self.export_path_edit = QLineEdit()
        self.export_path_edit.setPlaceholderText("Export file path...")
        export_layout.addWidget(self.export_path_edit)
        
        self.browse_export_btn = QPushButton("Browse")
        self.browse_export_btn.clicked.connect(self.browse_export_path)
        export_layout.addWidget(self.browse_export_btn)
        
        self.export_data_btn = QPushButton("Export Data")
        self.export_data_btn.clicked.connect(self.export_data)
        export_layout.addWidget(self.export_data_btn)
        data_layout.addLayout(export_layout)
        
        # Cleanup data
        cleanup_layout = QHBoxLayout()
        cleanup_layout.addWidget(QLabel("Keep data for (days):"))
        self.cleanup_days_spin = QSpinBox()
        self.cleanup_days_spin.setRange(1, 365)
        self.cleanup_days_spin.setValue(30)
        cleanup_layout.addWidget(self.cleanup_days_spin)
        
        self.cleanup_btn = QPushButton("Cleanup Old Data")
        self.cleanup_btn.clicked.connect(self.cleanup_data)
        cleanup_layout.addWidget(self.cleanup_btn)
        cleanup_layout.addStretch()
        data_layout.addLayout(cleanup_layout)
        
        layout.addWidget(data_group)
        
        # System information
        info_group = QGroupBox("System Information")
        info_layout = QVBoxLayout(info_group)
        
        self.system_info_text = QTextEdit()
        self.system_info_text.setReadOnly(True)
        self.system_info_text.setMaximumHeight(150)
        info_layout.addWidget(self.system_info_text)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        return widget
    
    def refresh_stats(self):
        """Refresh statistics display."""
        try:
            stats = self.service.get_feedback_stats()
            
            # Update statistics table
            self.stats_table.setRowCount(0)
            metrics = [
                ("Total Feedback", str(stats['total'])),
                ("Accepted Feedback", str(stats['accepted'])),
                ("Rejected Feedback", str(stats['rejected'])),
                ("Acceptance Rate", f"{stats['acceptance_rate']:.1f}%"),
                ("Replay Buffer Size", str(stats['replay_buffer_size'])),
                ("Model Updates", str(stats['model_updates'])),
                ("Successful Updates", str(stats['successful_updates'])),
                ("Failed Updates", str(stats['failed_updates'])),
                ("Rollbacks", str(stats['rollbacks']))
            ]
            
            for i, (metric, value) in enumerate(metrics):
                self.stats_table.insertRow(i)
                self.stats_table.setItem(i, 0, QTableWidgetItem(metric))
                self.stats_table.setItem(i, 1, QTableWidgetItem(value))
            
            # Update activity list
            self.activity_list.clear()
            history = self.service.get_update_history(limit=5)
            for update in history:
                item_text = f"{update.timestamp.strftime('%Y-%m-%d %H:%M')} - {update.status}"
                if update.samples_accepted > 0:
                    item_text += f" ({update.samples_accepted} samples)"
                self.activity_list.addItem(item_text)
            
            # Update update history table
            self.update_history_table.setRowCount(0)
            for i, update in enumerate(history):
                self.update_history_table.insertRow(i)
                self.update_history_table.setItem(i, 0, QTableWidgetItem(update.id[:8]))
                self.update_history_table.setItem(i, 1, QTableWidgetItem(update.timestamp.strftime('%Y-%m-%d %H:%M')))
                self.update_history_table.setItem(i, 2, QTableWidgetItem(update.status))
                self.update_history_table.setItem(i, 3, QTableWidgetItem(f"{update.samples_accepted}/{update.samples_processed}"))
                
                if update.performance_change is not None:
                    perf_text = f"{update.performance_change:+.3f}"
                else:
                    perf_text = "N/A"
                self.update_history_table.setItem(i, 4, QTableWidgetItem(perf_text))
            
        except Exception as e:
            logger.error(f"Error refreshing stats: {e}")
    
    def submit_feedback(self):
        """Submit feedback to the continuous learning service."""
        try:
            feedback_type = FeedbackType(self.feedback_type_combo.currentText())
            original_input = self.original_input_edit.toPlainText().strip()
            original_output = self.original_output_edit.toPlainText().strip()
            corrected_output = self.corrected_output_edit.toPlainText().strip() or None
            user_rating = self.user_rating_spin.value()
            user_comment = self.user_comment_edit.text().strip() or None
            
            if not original_input or not original_output:
                QMessageBox.warning(self, "Warning", "Please provide both original input and output.")
                return
            
            feedback_id = self.service.collect_feedback(
                feedback_type=feedback_type,
                original_input=original_input,
                original_output=original_output,
                corrected_output=corrected_output,
                user_rating=user_rating,
                user_comment=user_comment
            )
            
            QMessageBox.information(self, "Success", f"Feedback submitted successfully! ID: {feedback_id}")
            
            # Clear form
            self.original_input_edit.clear()
            self.original_output_edit.clear()
            self.corrected_output_edit.clear()
            self.user_comment_edit.clear()
            self.user_rating_spin.setValue(3)
            
            # Refresh stats
            self.refresh_stats()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to submit feedback: {e}")
    
    def trigger_model_update(self):
        """Trigger a model update."""
        try:
            batch_size = self.batch_size_spin.value()
            force_update = self.force_update_check.isChecked()
            
            reply = QMessageBox.question(
                self, "Confirm Update", 
                f"Are you sure you want to trigger a model update?\nBatch size: {batch_size}\nForce update: {force_update}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker = ContinuousLearningWorker(
                    "trigger_update",
                    batch_size=batch_size,
                    force_update=force_update
                )
                self.worker.progress_updated.connect(self.update_progress)
                self.worker.operation_completed.connect(self.handle_update_complete)
                self.worker.error_occurred.connect(self.handle_error)
                
                self.worker.start()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to trigger update: {e}")
    
    def export_data(self):
        """Export feedback data."""
        try:
            output_path = self.export_path_edit.text().strip()
            if not output_path:
                QMessageBox.warning(self, "Warning", "Please specify an export path.")
                return
            
            start_date = self.start_date_edit.date().toPyDate()
            end_date = self.end_date_edit.date().toPyDate()
            
            self.worker = ContinuousLearningWorker(
                "export_data",
                output_path=output_path,
                start_date=datetime.combine(start_date, datetime.min.time()),
                end_date=datetime.combine(end_date, datetime.max.time())
            )
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.operation_completed.connect(self.handle_export_complete)
            self.worker.error_occurred.connect(self.handle_error)
            
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export data: {e}")
    
    def cleanup_data(self):
        """Clean up old data."""
        try:
            days_to_keep = self.cleanup_days_spin.value()
            
            reply = QMessageBox.question(
                self, "Confirm Cleanup", 
                f"Are you sure you want to delete data older than {days_to_keep} days?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker = ContinuousLearningWorker(
                    "cleanup_data",
                    days_to_keep=days_to_keep
                )
                self.worker.progress_updated.connect(self.update_progress)
                self.worker.operation_completed.connect(self.handle_cleanup_complete)
                self.worker.error_occurred.connect(self.handle_error)
                
                self.worker.start()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to cleanup data: {e}")
    
    def browse_export_path(self):
        """Browse for export file path."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Export File", "", 
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            self.export_path_edit.setText(file_path)
    
    @pyqtSlot(int, int, str)
    def update_progress(self, current: int, total: int, message: str):
        """Update progress display."""
        # This could be enhanced with a progress dialog
        logger.info(f"Progress: {current}/{total} - {message}")
    
    @pyqtSlot(dict)
    def handle_update_complete(self, result: Dict[str, Any]):
        """Handle model update completion."""
        if result['success']:
            QMessageBox.information(self, "Success", result['message'])
        else:
            QMessageBox.warning(self, "Warning", result['message'])
        
        self.refresh_stats()
    
    @pyqtSlot(dict)
    def handle_export_complete(self, result: Dict[str, Any]):
        """Handle data export completion."""
        QMessageBox.information(self, "Success", f"Data exported to: {result['output_path']}")
    
    @pyqtSlot(dict)
    def handle_cleanup_complete(self, result: Dict[str, Any]):
        """Handle data cleanup completion."""
        QMessageBox.information(self, "Success", f"Cleaned up {result['deleted_count']} old records.")
        self.refresh_stats()
    
    @pyqtSlot(str)
    def handle_error(self, error: str):
        """Handle worker errors."""
        QMessageBox.critical(self, "Error", f"Operation failed: {error}") 