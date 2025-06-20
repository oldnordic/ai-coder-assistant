"""
Code Standards Tab

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
Code Standards Tab - Enforce company-specific coding standards.
"""

import concurrent.futures
import logging
import os
from typing import Any, Callable, Dict, List, Optional
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from src.frontend.controllers import BackendController


logger = logging.getLogger(__name__)


# Backend functions for ThreadManager
def analyze_code_file_backend(
    backend_controller: BackendController,
    file_path: str,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    log_message_callback: Optional[Callable[[str], None]] = None,
    cancellation_callback: Optional[Callable[[], bool]] = None,
) -> Optional[Dict[str, Any]]:
    """Backend function for code file analysis."""
    try:
        if progress_callback:
            progress_callback(25, 100, f"Analyzing file: {os.path.basename(file_path)}")

        if cancellation_callback and cancellation_callback():
            return None

        result = backend_controller.analyze_code_file(file_path)

        if progress_callback:
            progress_callback(100, 100, "Analysis completed")

        return result
    except Exception as e:
        if log_message_callback:
            log_message_callback(f"Error analyzing code: {e}")
        raise


def analyze_code_directory_backend(
    backend_controller: BackendController,
    directory_path: str,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    log_message_callback: Optional[Callable[[str], None]] = None,
    cancellation_callback: Optional[Callable[[], bool]] = None,
) -> Optional[List[Dict[str, Any]]]:
    """Backend function for code directory analysis."""
    try:
        if progress_callback:
            progress_callback(
                25, 100, f"Analyzing directory: {os.path.basename(directory_path)}"
            )

        if cancellation_callback and cancellation_callback():
            return None

        results = backend_controller.analyze_code_directory(directory_path)

        if progress_callback:
            progress_callback(100, 100, "Analysis completed")

        return results
    except Exception as e:
        if log_message_callback:
            log_message_callback(f"Error analyzing directory: {e}")
        raise


class AddRuleDialog(QDialog):
    """Dialog for adding code rules."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Code Rule")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.rule_id = QLineEdit()
        self.rule_name = QLineEdit()
        self.rule_description = QTextEdit()
        self.rule_description.setMaximumHeight(100)

        self.rule_language = QComboBox()
        self.rule_language.addItems(
            [
                "python",
                "javascript",
                "typescript",
                "java",
                "cpp",
                "csharp",
                "go",
                "rust",
                "php",
                "ruby",
            ]
        )

        self.rule_severity = QComboBox()
        self.rule_severity.addItems(["error", "warning", "info"])

        self.rule_pattern = QLineEdit()
        self.rule_message = QLineEdit()
        self.rule_category = QComboBox()
        self.rule_category.addItems(
            [
                "naming",
                "style",
                "security",
                "performance",
                "complexity",
                "documentation",
            ]
        )

        self.rule_enabled = QCheckBox("Enabled")
        self.rule_enabled.setChecked(True)

        self.rule_auto_fix = QCheckBox("Auto-fixable")
        self.rule_fix_template = QLineEdit()

        form_layout.addRow("ID:", self.rule_id)
        form_layout.addRow("Name:", self.rule_name)
        form_layout.addRow("Description:", self.rule_description)
        form_layout.addRow("Language:", self.rule_language)
        form_layout.addRow("Severity:", self.rule_severity)
        form_layout.addRow("Pattern:", self.rule_pattern)
        form_layout.addRow("Message:", self.rule_message)
        form_layout.addRow("Category:", self.rule_category)
        form_layout.addRow("Enabled:", self.rule_enabled)
        form_layout.addRow("Auto-fix:", self.rule_auto_fix)
        form_layout.addRow("Fix Template:", self.rule_fix_template)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_rule_data(self) -> Dict:
        """Get the rule data from the dialog."""
        return {
            "id": self.rule_id.text(),
            "name": self.rule_name.text(),
            "description": self.rule_description.toPlainText(),
            "language": self.rule_language.currentText(),
            "severity": self.rule_severity.currentText(),
            "pattern": self.rule_pattern.text(),
            "message": self.rule_message.text(),
            "category": self.rule_category.currentText(),
            "enabled": self.rule_enabled.isChecked(),
            "auto_fix": self.rule_auto_fix.isChecked(),
            "fix_template": self.rule_fix_template.text(),
            "tags": [],
        }


class CodeStandardsTab(QWidget):
    """Code Standards Tab Widget."""

    def __init__(
        self, backend_controller: BackendController, parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.backend_controller = backend_controller
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()

        # Create tabs
        self.standards_tab = self.create_standards_tab()
        self.analysis_tab = self.create_analysis_tab()

        self.tab_widget.addTab(self.standards_tab, "Standards Management")
        self.tab_widget.addTab(self.analysis_tab, "Code Analysis")

        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def create_standards_tab(self) -> QWidget:
        """Create the standards management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Current standard section
        current_group = QGroupBox("Current Standard")
        current_layout = QHBoxLayout()

        self.current_standard_label = QLabel("No standard selected")
        current_layout.addWidget(self.current_standard_label)

        set_current_btn = QPushButton("Set Current")
        set_current_btn.clicked.connect(self.set_current_standard)
        current_layout.addWidget(set_current_btn)

        current_group.setLayout(current_layout)
        layout.addWidget(current_group)

        # Standards table section
        standards_group = QGroupBox("Available Standards")
        standards_layout = QVBoxLayout()

        # Buttons
        buttons_layout = QHBoxLayout()
        add_btn = QPushButton("Add Standard")
        add_btn.clicked.connect(self.add_code_standard)
        buttons_layout.addWidget(add_btn)

        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self.import_code_standard)
        buttons_layout.addWidget(import_btn)

        buttons_layout.addStretch()
        standards_layout.addLayout(buttons_layout)

        # Standards table
        self.standards_table = QTableWidget()
        self.standards_table.setColumnCount(6)
        self.standards_table.setHorizontalHeaderLabels(
            ["Name", "Company", "Version", "Languages", "Rules", "Actions"]
        )

        header = self.standards_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        standards_layout.addWidget(self.standards_table)
        standards_group.setLayout(standards_layout)
        layout.addWidget(standards_group)

        return widget

    def create_analysis_tab(self) -> QWidget:
        """Create the code analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.analyze_file_btn = QPushButton("Analyze File")
        self.analyze_file_btn.clicked.connect(self.analyze_file)
        layout.addWidget(self.analyze_file_btn)

        self.analyze_dir_btn = QPushButton("Analyze Directory")
        self.analyze_dir_btn.clicked.connect(self.analyze_directory)
        layout.addWidget(self.analyze_dir_btn)

        self.results_tree = QTreeWidget()
        layout.addWidget(self.results_tree)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        return widget

    def load_data(self):
        """Load code standards data."""
        try:
            self.load_standards()
            self.load_current_standard()
        except Exception as e:
            logger.error(f"Error loading code standards data: {e}")
            QMessageBox.warning(
                self, "Error", f"Failed to load code standards data: {e}"
            )

    def load_standards(self):
        """Load code standards."""
        try:
            standards = self.backend_controller.get_code_standards()
            self.populate_standards_table(standards)
        except Exception as e:
            logger.error(f"Error loading standards: {e}")

    def load_current_standard(self):
        """Load current standard."""
        try:
            current_standard = self.backend_controller.get_current_code_standard()
            if current_standard:
                self.current_standard_label.setText(
                    current_standard.get("name", "Unknown")
                )
            else:
                self.current_standard_label.setText("No standard selected")
        except Exception as e:
            logger.error(f"Error loading current standard: {e}")

    def populate_standards_table(self, standards: List[Dict]):
        """Populate standards table."""
        self.standards_table.setRowCount(len(standards))

        for row, standard in enumerate(standards):
            self.standards_table.setItem(
                row, 0, QTableWidgetItem(standard.get("name", ""))
            )
            self.standards_table.setItem(
                row, 1, QTableWidgetItem(standard.get("company", ""))
            )
            self.standards_table.setItem(
                row, 2, QTableWidgetItem(standard.get("version", ""))
            )

            languages = ", ".join(standard.get("languages", []))
            self.standards_table.setItem(row, 3, QTableWidgetItem(languages))

            rules_count = len(standard.get("rules", []))
            self.standards_table.setItem(row, 4, QTableWidgetItem(str(rules_count)))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)

            export_btn = QPushButton("Export")
            export_btn.clicked.connect(
                lambda checked, s=standard: self.export_standard(s)
            )
            actions_layout.addWidget(export_btn)

            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(
                lambda checked, s=standard: self.remove_standard(s)
            )
            actions_layout.addWidget(remove_btn)

            actions_widget.setLayout(actions_layout)
            self.standards_table.setCellWidget(row, 5, actions_widget)

    def add_code_standard(self):
        """Add a new code standard."""
        try:
            # Simple dialog for adding standards
            name, ok = QLineEdit.getText(self, "Add Standard", "Standard Name:")
            if not ok or not name:
                return

            company, ok = QLineEdit.getText(self, "Add Standard", "Company:")
            if not ok:
                return

            version, ok = QLineEdit.getText(self, "Add Standard", "Version:")
            if not ok:
                return

            standard_data = {
                "name": name,
                "description": f"Code standard for {company}",
                "company": company,
                "version": version,
                "languages": ["python"],
                "rules": [],
                "enabled": True,
            }

            self.backend_controller.add_code_standard(standard_data)
            self.load_standards()
            QMessageBox.information(self, "Success", "Code standard added successfully")

        except Exception as e:
            logger.error(f"Error adding code standard: {e}")
            QMessageBox.warning(self, "Error", f"Failed to add code standard: {e}")

    def remove_standard(self, standard: Dict):
        """Remove a code standard."""
        try:
            name = standard.get("name", "")
            reply = QMessageBox.question(
                self,
                "Confirm Removal",
                f"Are you sure you want to remove the code standard '{name}'?",
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.backend_controller.remove_code_standard(name)
                self.load_standards()
                self.load_current_standard()
                QMessageBox.information(
                    self, "Success", f"Code standard '{name}' removed"
                )

        except Exception as e:
            logger.error(f"Error removing code standard: {e}")
            QMessageBox.warning(self, "Error", f"Failed to remove code standard: {e}")

    def set_current_standard(self):
        """Set the current standard."""
        try:
            standards = self.backend_controller.get_code_standards()
            if not standards:
                QMessageBox.warning(self, "Error", "No code standards available")
                return

            standard_names = [s.get("name", "") for s in standards]
            name, ok = QComboBox.getItem(
                self,
                "Set Current Standard",
                "Select Standard:",
                standard_names,
                0,
                False,
            )

            if ok and name:
                self.backend_controller.set_current_code_standard(name)
                self.load_current_standard()
                QMessageBox.information(
                    self, "Success", f"Code standard '{name}' set as current"
                )

        except Exception as e:
            logger.error(f"Error setting current standard: {e}")
            QMessageBox.warning(self, "Error", f"Failed to set current standard: {e}")

    def export_standard(self, standard: Dict):
        """Export a code standard."""
        try:
            name = standard.get("name", "")
            file_path, _ = QFileDialog.getSaveFileName(
                self, f"Export {name}", f"{name}.json", "JSON Files (*.json)"
            )

            if file_path:
                self.backend_controller.export_code_standard(name, file_path)
                QMessageBox.information(
                    self, "Success", f"Code standard exported to {file_path}"
                )

        except Exception as e:
            logger.error(f"Error exporting code standard: {e}")
            QMessageBox.warning(self, "Error", f"Failed to export code standard: {e}")

    def import_code_standard(self):
        """Import a code standard."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Import Code Standard", "", "JSON Files (*.json)"
            )

            if file_path:
                self.backend_controller.import_code_standard(file_path)
                self.load_standards()
                QMessageBox.information(
                    self, "Success", "Code standard imported successfully"
                )

        except Exception as e:
            logger.error(f"Error importing code standard: {e}")
            QMessageBox.warning(self, "Error", f"Failed to import code standard: {e}")

    def analyze_file(self):
        """Analyze a single code file."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Code File")
        if not file_path:
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        worker = self.executor.submit(
            analyze_code_file_backend,
            self.backend_controller,
            file_path,
            self.update_progress,
            self.handle_error,
        )
        if worker:
            worker.result().connect(self.on_analysis_finished)

    def analyze_directory(self):
        """Analyze a directory of code files."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if not dir_path:
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        worker = self.executor.submit(
            analyze_code_directory_backend,
            self.backend_controller,
            dir_path,
            self.update_progress,
            self.handle_error,
        )
        if worker:
            worker.result().connect(self.on_directory_analysis_finished)

    @pyqtSlot(str, int, int, str)
    def update_progress(self, worker_id: str, current: int, total: int, message: str):
        """Update the progress bar."""
        if worker_id in ["analyze_file", "analyze_directory"]:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)

    @pyqtSlot(object)
    def on_analysis_finished(self, result: Optional[Dict[str, Any]]):
        """Handle completion of file analysis."""
        self.progress_bar.setVisible(False)
        if result:
            self.display_analysis_results(result)
        else:
            QMessageBox.warning(
                self, "Analysis Failed", "File analysis failed or was cancelled."
            )

    @pyqtSlot(object)
    def on_directory_analysis_finished(self, results: Optional[List[Dict[str, Any]]]):
        """Handle completion of directory analysis."""
        self.progress_bar.setVisible(False)
        if results:
            self.display_directory_results(results)
        else:
            QMessageBox.warning(
                self, "Analysis Failed", "Directory analysis failed or was cancelled."
            )

    def display_analysis_results(self, result: Dict[str, Any]):
        """Display analysis results for a single file."""
        self.results_tree.clear()
        self.results_tree.setHeaderLabels(["File", "Line", "Severity", "Message"])
        file_item = QTreeWidgetItem([result.get("file_path", "Unknown File")])
        self.results_tree.addTopLevelItem(file_item)
        for violation in result.get("violations", []):
            violation_item = QTreeWidgetItem(
                [
                    "",
                    str(violation.get("line", "")),
                    violation.get("severity", ""),
                    violation.get("message", ""),
                ]
            )
            file_item.addChild(violation_item)

    def display_directory_results(self, results: List[Dict[str, Any]]):
        """Display analysis results for a directory."""
        self.results_tree.clear()
        self.results_tree.setHeaderLabels(["File", "Line", "Severity", "Message"])
        for result in results:
            file_item = QTreeWidgetItem([result.get("file_path", "Unknown File")])
            self.results_tree.addTopLevelItem(file_item)
            for violation in result.get("violations", []):
                violation_item = QTreeWidgetItem(
                    [
                        "",
                        str(violation.get("line", "")),
                        violation.get("severity", ""),
                        violation.get("message", ""),
                    ]
                )
                file_item.addChild(violation_item)

    @pyqtSlot(str)
    def handle_error(self, error: str):
        """Handle worker errors."""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"An error occurred: {error}")

    @pyqtSlot(object)
    def _on_standards_loaded(self, standards: Optional[List[Dict[str, Any]]]):
        """Callback for when coding standards are loaded."""
        try:
            _ = self.isVisible()
        except RuntimeError:
            return  # Widget is deleted

        self.progress_bar.setVisible(False)
        if standards:
            self.load_standards(standards)
        else:
            QMessageBox.warning(self, "Error", "Failed to load coding standards.")

    @pyqtSlot(object)
    def _on_analysis_complete(self, analysis_results: Optional[Dict[str, Any]]):
        """Callback for when code analysis is complete."""
        try:
            _ = self.isVisible()
        except RuntimeError:
            return  # Widget is deleted

        self.progress_bar.setVisible(False)
        if analysis_results:
            self.display_analysis_results(analysis_results)
        else:
            QMessageBox.warning(
                self, "Analysis Failed", "Code analysis returned no results."
            )
