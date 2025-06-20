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

import concurrent.futures
import logging
import os
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.backend.services.refactoring import (
    RefactoringOperation,
    RefactoringSuggestion,
    refactoring_engine,
)

logger = logging.getLogger(__name__)


# Backend functions for ThreadManager
def analyze_refactoring_opportunities_backend(
    project_path: str,
    languages: Optional[List[str]] = None,
    progress_callback=None,
    log_message_callback=None,
    cancellation_callback=None,
):
    """Backend function for analyzing refactoring opportunities."""
    try:
        if progress_callback:
            progress_callback(1, 3, "Analyzing project structure...")

        if cancellation_callback and cancellation_callback():
            return None

        # Analyze refactoring opportunities
        suggestions = refactoring_engine.analyze_refactoring_opportunities(
            project_path, languages
        )

        if progress_callback:
            progress_callback(
                2, 3, f"Found {len(suggestions)} refactoring opportunities..."
            )

        if cancellation_callback and cancellation_callback():
            return None

        # Convert suggestions to serializable format
        serialized_suggestions = []
        for suggestion in suggestions:
            serialized = {
                "id": suggestion.id,
                "title": suggestion.title,
                "description": suggestion.description,
                "priority": suggestion.priority,
                "impact_score": suggestion.impact_score,
                "estimated_time": suggestion.estimated_time,
                "category": suggestion.category,
                "tags": suggestion.tags,
                "operations": [],
            }

            for operation in suggestion.operations:
                serialized["operations"].append(
                    {
                        "operation_type": operation.operation_type,
                        "file_path": operation.file_path,
                        "line_start": operation.line_start,
                        "line_end": operation.line_end,
                        "description": operation.description,
                        "confidence": operation.confidence,
                        "risks": operation.risks,
                        "benefits": operation.benefits,
                    }
                )

            serialized_suggestions.append(serialized)

        if progress_callback:
            progress_callback(3, 3, "Analysis complete!")

        return {
            "success": True,
            "suggestions": serialized_suggestions,
            "total_count": len(suggestions),
        }

    except Exception as e:
        if log_message_callback:
            log_message_callback(f"Error analyzing refactoring opportunities: {e}")
        raise


def apply_refactoring_backend(
    suggestion_data: Dict[str, Any],
    backup: bool = True,
    progress_callback=None,
    log_message_callback=None,
    cancellation_callback=None,
):
    """Backend function for applying refactoring."""
    try:
        if progress_callback:
            progress_callback(1, 2, "Applying refactoring...")

        if cancellation_callback and cancellation_callback():
            return None

        # Reconstruct suggestion object
        suggestion = _reconstruct_suggestion(suggestion_data)

        # Apply the refactoring
        result = refactoring_engine.apply_refactoring(suggestion, backup)

        if progress_callback:
            progress_callback(2, 2, "Refactoring applied!")

        return result

    except Exception as e:
        if log_message_callback:
            log_message_callback(f"Error applying refactoring: {e}")
        raise


def preview_refactoring_backend(
    suggestion_data: Dict[str, Any],
    progress_callback=None,
    log_message_callback=None,
    cancellation_callback=None,
):
    """Backend function for previewing refactoring."""
    try:
        if progress_callback:
            progress_callback(1, 2, "Generating preview...")

        if cancellation_callback and cancellation_callback():
            return None

        # Reconstruct suggestion object
        suggestion = _reconstruct_suggestion(suggestion_data)

        # Generate preview
        preview = refactoring_engine.preview_refactoring(suggestion)

        if progress_callback:
            progress_callback(2, 2, "Preview generated!")

        return {"success": True, "preview": preview}

    except Exception as e:
        if log_message_callback:
            log_message_callback(f"Error generating preview: {e}")
        raise


def _reconstruct_suggestion(suggestion_data: Dict[str, Any]) -> RefactoringSuggestion:
    """Reconstruct a RefactoringSuggestion object from serialized data."""
    operations = []
    for op_data in suggestion_data.get("operations", []):
        operation = RefactoringOperation(
            operation_type=op_data["operation_type"],
            file_path=op_data["file_path"],
            line_start=op_data["line_start"],
            line_end=op_data["line_end"],
            description=op_data["description"],
            confidence=op_data["confidence"],
            original_code="",  # Will be loaded from file
            refactored_code="",  # Will be generated
            risks=op_data.get("risks", []),
            benefits=op_data.get("benefits", []),
        )
        operations.append(operation)

    return RefactoringSuggestion(
        id=suggestion_data["id"],
        title=suggestion_data["title"],
        description=suggestion_data["description"],
        priority=suggestion_data["priority"],
        operations=operations,
        impact_score=suggestion_data["impact_score"],
        estimated_time=suggestion_data["estimated_time"],
        category=suggestion_data["category"],
        tags=suggestion_data.get("tags", []),
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

        for file_path, file_data in self.preview_data.get("files", {}).items():
            file_item = QTreeWidgetItem(
                [file_path, f"{len(file_data.get('operations', []))} operations"]
            )

            for operation in file_data.get("operations", []):
                op_item = QTreeWidgetItem(
                    [
                        f"  {operation['type']}",
                        f"Lines {operation['line_start']}-{operation['line_end']}",
                    ]
                )
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
            file_data = self.preview_data.get("files", {}).get(file_path, {})

            diff_content = file_data.get("diff", "No diff available")
            self.diff_text.setPlainText(diff_content)


class RefactoringTab(QWidget):
    """Advanced refactoring tab for the main application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_path = None
        self.current_suggestion = None
        self.suggestions = []
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup the refactoring tab UI."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Advanced Refactoring"))

        # Project selection
        project_layout = QHBoxLayout()
        self.project_path_label = QLabel("Project:")
        project_layout.addWidget(self.project_path_label)

        self.project_path_input = QLineEdit()
        self.project_path_input.setReadOnly(True)
        self.project_path_input.setPlaceholderText("Select project directory...")
        project_layout.addWidget(self.project_path_input)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_project)
        project_layout.addWidget(self.browse_btn)

        header_layout.addLayout(project_layout)
        header_layout.addStretch()

        self.analyze_btn = QPushButton("Analyze Project")
        self.analyze_btn.clicked.connect(self.analyze_project)
        self.analyze_btn.setEnabled(False)  # Disabled until project is selected
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
        self.category_filter.addItems(
            ["All", "performance", "maintainability", "readability", "architecture"]
        )
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
        self.suggestions_table.setHorizontalHeaderLabels(
            ["Title", "Priority", "Category", "Impact", "Time"]
        )
        self.suggestions_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.suggestions_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.suggestions_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.suggestions_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.suggestions_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )

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

    def browse_project(self):
        """Open file dialog to select project directory."""
        project_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Project Directory",
            os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
        )

        if project_dir:
            self.set_project_path(project_dir)
            self.project_path_input.setText(project_dir)

    def set_project_path(self, project_path: str):
        """Set the project path for analysis."""
        self.project_path = project_path
        self.analyze_btn.setEnabled(True)
        self.status_label.setText(f"Project: {project_path}")

    def analyze_project(self):
        """Analyze the project for refactoring opportunities."""
        if not self.project_path:
            QMessageBox.warning(
                self, "Warning", "Please select a project directory first."
            )
            return

        self.analyze_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Analyzing project...")

        # Start analysis using ThreadPoolExecutor
        future = self.executor.submit(
            analyze_refactoring_opportunities_backend,
            self.project_path,
            ["python", "javascript", "typescript", "java", "cpp"],
            progress_callback=self.update_progress,
            log_message_callback=self.handle_error,
        )
        future.add_done_callback(self._on_analysis_complete)

    def _on_analysis_complete(self, future):
        def update_ui():
            try:
                result = future.result()
                self.suggestions = result
                self.refresh_suggestions_list()
                self.analyze_btn.setEnabled(True)
                self.progress_bar.setVisible(False)
                self.status_label.setText("Analysis complete")
            except Exception as e:
                self.handle_error(f"Analysis failed: {e}")
                self.analyze_btn.setEnabled(True)
                self.progress_bar.setVisible(False)

        QTimer.singleShot(0, update_ui)

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

                self.suggestions_table.setRowHidden(
                    row, not (priority_match and category_match)
                )

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
        for operation in self.current_suggestion.get("operations", []):
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

        # Start preview using ThreadPoolExecutor
        future = self.executor.submit(
            preview_refactoring_backend,
            self.current_suggestion,
            progress_callback=self.update_progress,
            log_message_callback=self.handle_error,
        )
        future.add_done_callback(self._on_preview_complete)

    def _on_preview_complete(self, future):
        def update_ui():
            try:
                result = future.result()
                self.show_preview(result)
                self.preview_btn.setEnabled(True)
                self.progress_bar.setVisible(False)
                self.status_label.setText("Preview complete")
            except Exception as e:
                self.handle_error(f"Preview failed: {e}")
                self.preview_btn.setEnabled(True)
                self.progress_bar.setVisible(False)

        QTimer.singleShot(0, update_ui)

    def apply_suggestion(self):
        """Apply the selected suggestion."""
        if not self.current_suggestion:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Refactoring",
            f"Are you sure you want to apply the refactoring '{self.current_suggestion['title']}'?\n\n"
            "This will modify your source code. Make sure you have a backup!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.apply_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.status_label.setText("Applying refactoring...")

            # Start apply using ThreadPoolExecutor
            future = self.executor.submit(
                apply_refactoring_backend,
                self.current_suggestion,
                backup=self.backup_checkbox.isChecked(),
                progress_callback=self.update_progress,
                log_message_callback=self.handle_error,
            )
            future.add_done_callback(self._on_apply_complete)

    def _on_apply_complete(self, future):
        def update_ui():
            try:
                result = future.result()
                self.handle_apply_complete(result)
            except Exception as e:
                self.handle_error(f"Apply failed: {e}")
                self.apply_btn.setEnabled(True)
                self.progress_bar.setVisible(False)

        QTimer.singleShot(0, update_ui)

    def update_progress(self, current: int, total: int, message: str):
        """Update progress display."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(message)

    def handle_analysis_complete(self, result: Dict[str, Any]):
        """Handle analysis completion."""
        self.analyze_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        if result["success"]:
            self.suggestions = result["suggestions"]
            self.populate_suggestions_table()
            self.refresh_btn.setEnabled(True)
            self.status_label.setText(
                f"Found {result['total_count']} refactoring suggestions"
            )
        else:
            self.status_label.setText("Analysis failed")

    def handle_preview_complete(self, result: Dict[str, Any]):
        """Handle preview completion."""
        self.preview_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        if result["success"]:
            preview_data = result["preview"]
            dialog = RefactoringPreviewDialog(preview_data, self)
            dialog.exec()
            self.status_label.setText("Preview generated successfully")
        else:
            self.status_label.setText("Preview generation failed")

    def handle_apply_complete(self, result: Dict[str, Any]):
        """Handle apply completion."""
        self.apply_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        if result["success"]:
            applied_count = len(result["applied_operations"])
            modified_files = len(result["modified_files"])

            message = "Refactoring applied successfully!\n\n"
            message += f"Applied operations: {applied_count}\n"
            message += f"Modified files: {modified_files}\n"

            if result.get("backup_files"):
                message += f"Backup files created: {len(result['backup_files'])}\n"

            if result.get("warnings"):
                message += f"\nWarnings: {len(result['warnings'])}"

            QMessageBox.information(self, "Success", message)
            self.status_label.setText("Refactoring applied successfully")

            # Refresh suggestions
            self.refresh_suggestions()
        else:
            error_message = (
                f"Refactoring failed:\n{chr(10).join(result.get('errors', []))}"
            )
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
            title_item = QTableWidgetItem(suggestion["title"])
            title_item.setData(Qt.ItemDataRole.UserRole, suggestion)
            self.suggestions_table.setItem(row, 0, title_item)

            # Priority
            priority_item = QTableWidgetItem(suggestion["priority"])
            priority_color = {
                "high": QColor(255, 200, 200),  # Light red
                "medium": QColor(255, 255, 200),  # Light yellow
                "low": QColor(200, 255, 200),  # Light green
            }.get(suggestion["priority"], QColor(255, 255, 255))
            priority_item.setBackground(priority_color)
            self.suggestions_table.setItem(row, 1, priority_item)

            # Category
            category_item = QTableWidgetItem(suggestion["category"])
            self.suggestions_table.setItem(row, 2, category_item)

            # Impact
            impact_item = QTableWidgetItem(f"{suggestion['impact_score']:.2f}")
            self.suggestions_table.setItem(row, 3, impact_item)

            # Time
            time_item = QTableWidgetItem(suggestion["estimated_time"])
            self.suggestions_table.setItem(row, 4, time_item)

        # Apply current filters
        self.apply_filters()

    @pyqtSlot(object)
    def _on_refactor_complete(self, result: Optional[Dict[str, str]]):
        """Handle refactoring completion."""
        try:
            _ = self.isVisible()
        except RuntimeError:
            return  # Widget is deleted

        self.progress_bar.hide()
        if result and "refactored_code" in result:
            self.refactored_code_edit.setPlainText(result["refactored_code"])
            QMessageBox.information(self, "Success", "Code refactored successfully.")
        else:
            QMessageBox.warning(
                self,
                "Refactoring Failed",
                result.get("error", "An unknown error occurred."),
            )

    @pyqtSlot(object)
    def _on_test_generation_complete(self, result: Optional[Dict[str, str]]):
        """Handle test generation completion."""
        try:
            _ = self.isVisible()
        except RuntimeError:
            return  # Widget is deleted

        self.progress_bar.hide()
        if result and "test_code" in result:
            # Assuming you have a widget to display the tests, e.g.,
            # self.generated_tests_edit
            self.generated_tests_edit.setPlainText(result["test_code"])
            QMessageBox.information(self, "Success", "Tests generated successfully.")
        else:
            QMessageBox.warning(
                self,
                "Test Generation Failed",
                result.get("error", "An unknown error occurred."),
            )

    @pyqtSlot(object)
    def _on_docstring_generation_complete(self, result: Optional[Dict[str, str]]):
        """Handle docstring generation completion."""
        try:
            _ = self.isVisible()
        except RuntimeError:
            return  # Widget is deleted

        self.progress_bar.hide()
        if result and "code_with_docstrings" in result:
            self.refactored_code_edit.setPlainText(result["code_with_docstrings"])
            QMessageBox.information(
                self, "Success", "Docstrings generated successfully."
            )
        else:
            QMessageBox.warning(
                self,
                "Docstring Generation Failed",
                result.get("error", "An unknown error occurred."),
            )

    def connect_signals(self):
        """Connect signals and slots for the tab."""
        # This method will be implemented when the full UI is added
        pass
