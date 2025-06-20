"""
refactoring_tab.py

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

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QTextEdit, QGroupBox, QSplitter,
    QHeaderView, QMessageBox, QFileDialog, QProgressBar, QComboBox,
    QCheckBox, QSpinBox, QListWidget, QListWidgetItem, QTreeWidget,
    QTreeWidgetItem, QDialog, QDialogButtonBox, QFormLayout, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette

from backend.services.refactoring import refactoring_engine, RefactoringSuggestion, RefactoringOperation
from backend.utils.constants import MAX_FILE_SIZE_KB

logger = logging.getLogger(__name__)

class RefactoringWorker(QThread):
    """Worker thread for refactoring operations."""
    
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    operation_completed = pyqtSignal(dict)  # result
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, operation: str, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs
    
    def run(self):
        """Run the refactoring operation."""
        try:
            if self.operation == "analyze":
                self._analyze_refactoring_opportunities()
            elif self.operation == "apply":
                self._apply_refactoring()
            elif self.operation == "preview":
                self._preview_refactoring()
            else:
                raise ValueError(f"Unknown operation: {self.operation}")
                
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _analyze_refactoring_opportunities(self):
        """Analyze project for refactoring opportunities."""
        project_path = self.kwargs.get('project_path')
        languages = self.kwargs.get('languages', None)
        
        self.progress_updated.emit(1, 3, "Analyzing project structure...")
        
        # Analyze refactoring opportunities
        suggestions = refactoring_engine.analyze_refactoring_opportunities(
            project_path, languages
        )
        
        self.progress_updated.emit(2, 3, f"Found {len(suggestions)} refactoring opportunities...")
        
        # Convert suggestions to serializable format
        serialized_suggestions = []
        for suggestion in suggestions:
            serialized = {
                'id': suggestion.id,
                'title': suggestion.title,
                'description': suggestion.description,
                'priority': suggestion.priority,
                'impact_score': suggestion.impact_score,
                'estimated_time': suggestion.estimated_time,
                'category': suggestion.category,
                'tags': suggestion.tags,
                'operations': []
            }
            
            for operation in suggestion.operations:
                serialized['operations'].append({
                    'operation_type': operation.operation_type,
                    'file_path': operation.file_path,
                    'line_start': operation.line_start,
                    'line_end': operation.line_end,
                    'description': operation.description,
                    'confidence': operation.confidence,
                    'risks': operation.risks,
                    'benefits': operation.benefits
                })
            
            serialized_suggestions.append(serialized)
        
        self.progress_updated.emit(3, 3, "Analysis complete!")
        
        result = {
            'success': True,
            'suggestions': serialized_suggestions,
            'total_count': len(suggestions)
        }
        
        self.operation_completed.emit(result)
    
    def _apply_refactoring(self):
        """Apply a refactoring suggestion."""
        suggestion_data = self.kwargs.get('suggestion')
        backup = self.kwargs.get('backup', True)
        
        # Reconstruct suggestion object
        suggestion = self._reconstruct_suggestion(suggestion_data)
        
        self.progress_updated.emit(1, 2, "Applying refactoring...")
        
        # Apply the refactoring
        result = refactoring_engine.apply_refactoring(suggestion, backup)
        
        self.progress_updated.emit(2, 2, "Refactoring applied!")
        
        self.operation_completed.emit(result)
    
    def _preview_refactoring(self):
        """Preview a refactoring suggestion."""
        suggestion_data = self.kwargs.get('suggestion')
        
        # Reconstruct suggestion object
        suggestion = self._reconstruct_suggestion(suggestion_data)
        
        self.progress_updated.emit(1, 2, "Generating preview...")
        
        # Generate preview
        preview = refactoring_engine.preview_refactoring(suggestion)
        
        self.progress_updated.emit(2, 2, "Preview generated!")
        
        result = {
            'success': True,
            'preview': preview
        }
        
        self.operation_completed.emit(result)
    
    def _reconstruct_suggestion(self, suggestion_data: Dict[str, Any]) -> RefactoringSuggestion:
        """Reconstruct a RefactoringSuggestion object from serialized data."""
        operations = []
        for op_data in suggestion_data.get('operations', []):
            operation = RefactoringOperation(
                operation_type=op_data['operation_type'],
                file_path=op_data['file_path'],
                line_start=op_data['line_start'],
                line_end=op_data['line_end'],
                description=op_data['description'],
                confidence=op_data['confidence'],
                original_code="",  # Will be loaded from file
                refactored_code="",  # Will be generated
                risks=op_data.get('risks', []),
                benefits=op_data.get('benefits', [])
            )
            operations.append(operation)
        
        return RefactoringSuggestion(
            id=suggestion_data['id'],
            title=suggestion_data['title'],
            description=suggestion_data['description'],
            priority=suggestion_data['priority'],
            operations=operations,
            impact_score=suggestion_data['impact_score'],
            estimated_time=suggestion_data['estimated_time'],
            category=suggestion_data['category'],
            tags=suggestion_data.get('tags', [])
        )

class RefactoringPreviewDialog(QDialog):
    """Dialog for previewing refactoring changes."""
    
    def __init__(self, preview_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.preview_data = preview_data
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the preview dialog UI."""
        self.setWindowTitle("Refactoring Preview")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Summary
        summary_group = QGroupBox("Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        summary_text = f"""
        Title: {self.preview_data.get('title', 'N/A')}
        Description: {self.preview_data.get('description', 'N/A')}
        Files Modified: {self.preview_data['summary']['files_modified']}
        Lines Added: {self.preview_data['summary']['lines_added']}
        Lines Removed: {self.preview_data['summary']['lines_removed']}
        Operations: {self.preview_data['summary']['operations']}
        """
        
        summary_label = QLabel(summary_text)
        summary_layout.addWidget(summary_label)
        layout.addWidget(summary_group)
        
        # File changes
        files_group = QGroupBox("File Changes")
        files_layout = QVBoxLayout(files_group)
        
        # Create tree widget for files
        self.files_tree = QTreeWidget()
        self.files_tree.setHeaderLabels(["File", "Operations"])
        self.files_tree.setColumnWidth(0, 300)
        
        for file_path, file_data in self.preview_data.get('files', {}).items():
            file_item = QTreeWidgetItem([file_path, f"{len(file_data.get('operations', []))} operations"])
            
            for operation in file_data.get('operations', []):
                op_item = QTreeWidgetItem([
                    f"  {operation['type']}",
                    f"Lines {operation['line_start']}-{operation['line_end']}"
                ])
                file_item.addChild(op_item)
            
            self.files_tree.addTopLevelItem(file_item)
        
        files_layout.addWidget(self.files_tree)
        layout.addWidget(files_group)
        
        # Diff view
        diff_group = QGroupBox("Changes Preview")
        diff_layout = QVBoxLayout(diff_group)
        
        self.diff_text = QTextEdit()
        self.diff_text.setFont(QFont("Courier", 10))
        self.diff_text.setReadOnly(True)
        
        # Show diff for selected file
        self.files_tree.itemClicked.connect(self._show_file_diff)
        
        diff_layout.addWidget(self.diff_text)
        layout.addWidget(diff_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _show_file_diff(self, item: QTreeWidgetItem, column: int):
        """Show diff for the selected file."""
        if item.parent() is None:  # Top-level file item
            file_path = item.text(0)
            file_data = self.preview_data.get('files', {}).get(file_path, {})
            
            diff_content = file_data.get('diff', 'No diff available')
            self.diff_text.setPlainText(diff_content)

class RefactoringTab(QWidget):
    """Advanced refactoring tab for the main application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_path = None
        self.suggestions = []
        self.current_suggestion = None
        self.worker = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the refactoring tab UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Advanced Refactoring"))
        header_layout.addStretch()
        
        self.analyze_btn = QPushButton("Analyze Project")
        self.analyze_btn.clicked.connect(self.analyze_project)
        header_layout.addWidget(self.analyze_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_suggestions)
        self.refresh_btn.setEnabled(False)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Main content
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Suggestions list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Filters
        filters_group = QGroupBox("Filters")
        filters_layout = QVBoxLayout(filters_group)
        
        # Priority filter
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("Priority:"))
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["All", "High", "Medium", "Low"])
        self.priority_filter.currentTextChanged.connect(self.apply_filters)
        priority_layout.addWidget(self.priority_filter)
        priority_layout.addStretch()
        filters_layout.addLayout(priority_layout)
        
        # Category filter
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItems(["All", "performance", "maintainability", "readability", "architecture"])
        self.category_filter.currentTextChanged.connect(self.apply_filters)
        category_layout.addWidget(self.category_filter)
        category_layout.addStretch()
        filters_layout.addLayout(category_layout)
        
        left_layout.addWidget(filters_group)
        
        # Suggestions table
        suggestions_group = QGroupBox("Refactoring Suggestions")
        suggestions_layout = QVBoxLayout(suggestions_group)
        
        self.suggestions_table = QTableWidget()
        self.suggestions_table.setColumnCount(5)
        self.suggestions_table.setHorizontalHeaderLabels([
            "Title", "Priority", "Category", "Impact", "Time"
        ])
        self.suggestions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.suggestions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.suggestions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.suggestions_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.suggestions_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.suggestions_table.itemSelectionChanged.connect(self.on_suggestion_selected)
        suggestions_layout.addWidget(self.suggestions_table)
        
        left_layout.addWidget(suggestions_group)
        main_splitter.addWidget(left_panel)
        
        # Right panel - Details and actions
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Suggestion details
        details_group = QGroupBox("Suggestion Details")
        details_layout = QVBoxLayout(details_group)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        details_layout.addWidget(self.details_text)
        
        right_layout.addWidget(details_group)
        
        # Operations list
        operations_group = QGroupBox("Operations")
        operations_layout = QVBoxLayout(operations_group)
        
        self.operations_list = QListWidget()
        self.operations_list.setMaximumHeight(150)
        operations_layout.addWidget(self.operations_list)
        
        right_layout.addWidget(operations_group)
        
        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.preview_btn = QPushButton("Preview Changes")
        self.preview_btn.clicked.connect(self.preview_suggestion)
        self.preview_btn.setEnabled(False)
        actions_layout.addWidget(self.preview_btn)
        
        self.apply_btn = QPushButton("Apply Refactoring")
        self.apply_btn.clicked.connect(self.apply_suggestion)
        self.apply_btn.setEnabled(False)
        actions_layout.addWidget(self.apply_btn)
        
        # Backup option
        self.backup_checkbox = QCheckBox("Create backup before applying")
        self.backup_checkbox.setChecked(True)
        actions_layout.addWidget(self.backup_checkbox)
        
        right_layout.addWidget(actions_group)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        right_layout.addStretch()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([400, 600])
        layout.addWidget(main_splitter)
        
        # Status
        self.status_label = QLabel("Ready to analyze project")
        layout.addWidget(self.status_label)
    
    def set_project_path(self, project_path: str):
        """Set the project path for analysis."""
        self.project_path = project_path
        self.analyze_btn.setEnabled(True)
        self.status_label.setText(f"Project: {project_path}")
    
    def analyze_project(self):
        """Analyze the project for refactoring opportunities."""
        if not self.project_path:
            QMessageBox.warning(self, "Warning", "Please select a project directory first.")
            return
        
        self.analyze_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Analyzing project...")
        
        # Start analysis worker
        self.worker = RefactoringWorker(
            "analyze",
            project_path=self.project_path,
            languages=['python', 'javascript', 'typescript', 'java', 'cpp']
        )
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.operation_completed.connect(self.handle_analysis_complete)
        self.worker.error_occurred.connect(self.handle_error)
        
        self.worker.start()
    
    def refresh_suggestions(self):
        """Refresh the suggestions list."""
        if self.project_path:
            self.analyze_project()
    
    def apply_filters(self):
        """Apply filters to the suggestions table."""
        priority_filter = self.priority_filter.currentText()
        category_filter = self.category_filter.currentText()
        
        for row in range(self.suggestions_table.rowCount()):
            priority_item = self.suggestions_table.item(row, 1)
            category_item = self.suggestions_table.item(row, 2)
            
            if priority_item and category_item:
                priority = priority_item.text()
                category = category_item.text()
                
                priority_match = priority_filter == "All" or priority == priority_filter
                category_match = category_filter == "All" or category == category_filter
                
                self.suggestions_table.setRowHidden(row, not (priority_match and category_match))
    
    def on_suggestion_selected(self):
        """Handle suggestion selection."""
        current_row = self.suggestions_table.currentRow()
        if current_row >= 0 and current_row < len(self.suggestions):
            self.current_suggestion = self.suggestions[current_row]
            self.update_suggestion_details()
            self.preview_btn.setEnabled(True)
            self.apply_btn.setEnabled(True)
        else:
            self.current_suggestion = None
            self.preview_btn.setEnabled(False)
            self.apply_btn.setEnabled(False)
    
    def update_suggestion_details(self):
        """Update the suggestion details display."""
        if not self.current_suggestion:
            return
        
        details = f"""
        <h3>{self.current_suggestion['title']}</h3>
        <p><strong>Description:</strong> {self.current_suggestion['description']}</p>
        <p><strong>Priority:</strong> {self.current_suggestion['priority']}</p>
        <p><strong>Category:</strong> {self.current_suggestion['category']}</p>
        <p><strong>Impact Score:</strong> {self.current_suggestion['impact_score']:.2f}</p>
        <p><strong>Estimated Time:</strong> {self.current_suggestion['estimated_time']}</p>
        <p><strong>Tags:</strong> {', '.join(self.current_suggestion.get('tags', []))}</p>
        """
        
        self.details_text.setHtml(details)
        
        # Update operations list
        self.operations_list.clear()
        for operation in self.current_suggestion.get('operations', []):
            item_text = f"{operation['operation_type']}: {operation['description']}"
            item = QListWidgetItem(item_text)
            self.operations_list.addItem(item)
    
    def preview_suggestion(self):
        """Preview the selected suggestion."""
        if not self.current_suggestion:
            return
        
        self.preview_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Generating preview...")
        
        # Start preview worker
        self.worker = RefactoringWorker(
            "preview",
            suggestion=self.current_suggestion
        )
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.operation_completed.connect(self.handle_preview_complete)
        self.worker.error_occurred.connect(self.handle_error)
        
        self.worker.start()
    
    def apply_suggestion(self):
        """Apply the selected suggestion."""
        if not self.current_suggestion:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Refactoring",
            f"Are you sure you want to apply the refactoring '{self.current_suggestion['title']}'?\n\n"
            "This will modify your source code. Make sure you have a backup!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.apply_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.status_label.setText("Applying refactoring...")
            
            # Start apply worker
            self.worker = RefactoringWorker(
                "apply",
                suggestion=self.current_suggestion,
                backup=self.backup_checkbox.isChecked()
            )
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.operation_completed.connect(self.handle_apply_complete)
            self.worker.error_occurred.connect(self.handle_error)
            
            self.worker.start()
    
    def update_progress(self, current: int, total: int, message: str):
        """Update progress display."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(message)
    
    def handle_analysis_complete(self, result: Dict[str, Any]):
        """Handle analysis completion."""
        self.analyze_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if result['success']:
            self.suggestions = result['suggestions']
            self.populate_suggestions_table()
            self.refresh_btn.setEnabled(True)
            self.status_label.setText(f"Found {result['total_count']} refactoring suggestions")
        else:
            self.status_label.setText("Analysis failed")
    
    def handle_preview_complete(self, result: Dict[str, Any]):
        """Handle preview completion."""
        self.preview_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if result['success']:
            preview_data = result['preview']
            dialog = RefactoringPreviewDialog(preview_data, self)
            dialog.exec()
            self.status_label.setText("Preview generated successfully")
        else:
            self.status_label.setText("Preview generation failed")
    
    def handle_apply_complete(self, result: Dict[str, Any]):
        """Handle apply completion."""
        self.apply_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if result['success']:
            applied_count = len(result['applied_operations'])
            modified_files = len(result['modified_files'])
            
            message = f"Refactoring applied successfully!\n\n"
            message += f"Applied operations: {applied_count}\n"
            message += f"Modified files: {modified_files}\n"
            
            if result.get('backup_files'):
                message += f"Backup files created: {len(result['backup_files'])}\n"
            
            if result.get('warnings'):
                message += f"\nWarnings: {len(result['warnings'])}"
            
            QMessageBox.information(self, "Success", message)
            self.status_label.setText("Refactoring applied successfully")
            
            # Refresh suggestions
            self.refresh_suggestions()
        else:
            error_message = "Refactoring failed:\n" + "\n".join(result.get('errors', []))
            QMessageBox.critical(self, "Error", error_message)
            self.status_label.setText("Refactoring failed")
    
    def handle_error(self, error_message: str):
        """Handle worker errors."""
        self.analyze_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.apply_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "Error", f"Operation failed: {error_message}")
        self.status_label.setText("Operation failed")
    
    def populate_suggestions_table(self):
        """Populate the suggestions table with data."""
        self.suggestions_table.setRowCount(len(self.suggestions))
        
        for row, suggestion in enumerate(self.suggestions):
            # Title
            title_item = QTableWidgetItem(suggestion['title'])
            title_item.setData(Qt.ItemDataRole.UserRole, suggestion)
            self.suggestions_table.setItem(row, 0, title_item)
            
            # Priority
            priority_item = QTableWidgetItem(suggestion['priority'])
            priority_color = {
                'high': QColor(255, 200, 200),  # Light red
                'medium': QColor(255, 255, 200),  # Light yellow
                'low': QColor(200, 255, 200)  # Light green
            }.get(suggestion['priority'], QColor(255, 255, 255))
            priority_item.setBackground(priority_color)
            self.suggestions_table.setItem(row, 1, priority_item)
            
            # Category
            category_item = QTableWidgetItem(suggestion['category'])
            self.suggestions_table.setItem(row, 2, category_item)
            
            # Impact
            impact_item = QTableWidgetItem(f"{suggestion['impact_score']:.2f}")
            self.suggestions_table.setItem(row, 3, impact_item)
            
            # Time
            time_item = QTableWidgetItem(suggestion['estimated_time'])
            self.suggestions_table.setItem(row, 4, time_item)
        
        # Apply current filters
        self.apply_filters() 