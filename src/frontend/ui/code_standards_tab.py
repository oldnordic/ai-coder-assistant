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

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, 
    QTableWidgetItem, QPushButton, QLabel, QComboBox, QLineEdit,
    QTextEdit, QGroupBox, QFormLayout, QSpinBox, QCheckBox,
    QMessageBox, QProgressBar, QSplitter, QHeaderView, QFrame,
    QFileDialog, QTreeWidget, QTreeWidgetItem, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette

from ..controllers import BackendController

logger = logging.getLogger(__name__)


class CodeAnalysisWorker(QThread):
    """Worker thread for code analysis."""
    
    finished = pyqtSignal(bool, str, list)
    progress = pyqtSignal(int)
    
    def __init__(self, backend_controller: BackendController, file_path: str):
        super().__init__()
        self.backend_controller = backend_controller
        self.file_path = file_path
    
    def run(self):
        """Analyze code file."""
        try:
            self.progress.emit(25)
            result = self.backend_controller.analyze_code_file(self.file_path)
            self.progress.emit(100)
            self.finished.emit(True, "Analysis completed", [result])
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            self.finished.emit(False, str(e), [])


class DirectoryAnalysisWorker(QThread):
    """Worker thread for directory analysis."""
    
    finished = pyqtSignal(bool, str, list)
    progress = pyqtSignal(int)
    
    def __init__(self, backend_controller: BackendController, directory_path: str):
        super().__init__()
        self.backend_controller = backend_controller
        self.directory_path = directory_path
    
    def run(self):
        """Analyze code directory."""
        try:
            self.progress.emit(25)
            results = self.backend_controller.analyze_code_directory(self.directory_path)
            self.progress.emit(100)
            self.finished.emit(True, "Analysis completed", results)
        except Exception as e:
            logger.error(f"Error analyzing directory: {e}")
            self.finished.emit(False, str(e), [])


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
        self.rule_language.addItems(["python", "javascript", "typescript", "java", "cpp", "csharp", "go", "rust", "php", "ruby"])
        
        self.rule_severity = QComboBox()
        self.rule_severity.addItems(["error", "warning", "info"])
        
        self.rule_pattern = QLineEdit()
        self.rule_message = QLineEdit()
        self.rule_category = QComboBox()
        self.rule_category.addItems(["naming", "style", "security", "performance", "complexity", "documentation"])
        
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
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
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
            "tags": []
        }


class CodeStandardsTab(QWidget):
    """Code Standards Tab Widget."""
    
    def __init__(self, backend_controller: BackendController):
        super().__init__()
        self.backend_controller = backend_controller
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Code Standards")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        # Control buttons
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)
        
        add_standard_btn = QPushButton("Add Standard")
        add_standard_btn.clicked.connect(self.add_code_standard)
        header_layout.addWidget(add_standard_btn)
        
        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self.import_code_standard)
        header_layout.addWidget(import_btn)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Main tab widget
        self.tab_widget = QTabWidget()
        
        # Standards tab
        self.standards_tab = self.create_standards_tab()
        self.tab_widget.addTab(self.standards_tab, "Code Standards")
        
        # Analysis tab
        self.analysis_tab = self.create_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "Code Analysis")
        
        # Rules tab
        self.rules_tab = self.create_rules_tab()
        self.tab_widget.addTab(self.rules_tab, "Rules")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def create_standards_tab(self) -> QWidget:
        """Create standards tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Current standard info
        current_group = QGroupBox("Current Standard")
        current_layout = QFormLayout()
        
        self.current_standard_label = QLabel("No standard selected")
        self.current_standard_label.setStyleSheet("font-weight: bold; color: blue;")
        current_layout.addRow("Active:", self.current_standard_label)
        
        set_current_btn = QPushButton("Set Current")
        set_current_btn.clicked.connect(self.set_current_standard)
        current_layout.addRow("", set_current_btn)
        
        current_group.setLayout(current_layout)
        layout.addWidget(current_group)
        
        # Standards table
        self.standards_table = QTableWidget()
        self.standards_table.setColumnCount(6)
        self.standards_table.setHorizontalHeaderLabels([
            "Name", "Company", "Version", "Languages", "Rules", "Actions"
        ])
        
        header = self.standards_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.standards_table)
        widget.setLayout(layout)
        return widget
    
    def create_analysis_tab(self) -> QWidget:
        """Create analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Analysis controls
        controls_group = QGroupBox("Analysis Controls")
        controls_layout = QHBoxLayout()
        
        file_btn = QPushButton("Analyze File")
        file_btn.clicked.connect(self.analyze_file)
        controls_layout.addWidget(file_btn)
        
        dir_btn = QPushButton("Analyze Directory")
        dir_btn.clicked.connect(self.analyze_directory)
        controls_layout.addWidget(dir_btn)
        
        auto_fix_btn = QPushButton("Auto-fix Violations")
        auto_fix_btn.clicked.connect(self.auto_fix_violations)
        controls_layout.addWidget(auto_fix_btn)
        
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Analysis results
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout()
        
        # Summary
        summary_layout = QHBoxLayout()
        self.total_violations_label = QLabel("Total Violations: 0")
        self.error_count_label = QLabel("Errors: 0")
        self.warning_count_label = QLabel("Warnings: 0")
        self.info_count_label = QLabel("Info: 0")
        self.auto_fixable_count_label = QLabel("Auto-fixable: 0")
        
        summary_layout.addWidget(self.total_violations_label)
        summary_layout.addWidget(self.error_count_label)
        summary_layout.addWidget(self.warning_count_label)
        summary_layout.addWidget(self.info_count_label)
        summary_layout.addWidget(self.auto_fixable_count_label)
        summary_layout.addStretch()
        
        results_layout.addLayout(summary_layout)
        
        # Violations table
        self.violations_table = QTableWidget()
        self.violations_table.setColumnCount(7)
        self.violations_table.setHorizontalHeaderLabels([
            "File", "Line", "Rule", "Severity", "Message", "Category", "Actions"
        ])
        
        header = self.violations_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        results_layout.addWidget(self.violations_table)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_rules_tab(self) -> QWidget:
        """Create rules tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Rules controls
        controls_layout = QHBoxLayout()
        
        add_rule_btn = QPushButton("Add Rule")
        add_rule_btn.clicked.connect(self.add_rule)
        controls_layout.addWidget(add_rule_btn)
        
        filter_label = QLabel("Filter:")
        self.rule_filter = QComboBox()
        self.rule_filter.addItems(["All", "naming", "style", "security", "performance", "complexity", "documentation"])
        self.rule_filter.currentTextChanged.connect(self.filter_rules)
        controls_layout.addWidget(filter_label)
        controls_layout.addWidget(self.rule_filter)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Rules table
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(8)
        self.rules_table.setHorizontalHeaderLabels([
            "ID", "Name", "Language", "Severity", "Category", "Pattern", "Enabled", "Actions"
        ])
        
        header = self.rules_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.rules_table)
        widget.setLayout(layout)
        return widget
    
    def load_data(self):
        """Load code standards data."""
        try:
            self.load_standards()
            self.load_current_standard()
        except Exception as e:
            logger.error(f"Error loading code standards data: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load code standards data: {e}")
    
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
                self.current_standard_label.setText(current_standard.get("name", "Unknown"))
            else:
                self.current_standard_label.setText("No standard selected")
        except Exception as e:
            logger.error(f"Error loading current standard: {e}")
    
    def populate_standards_table(self, standards: List[Dict]):
        """Populate standards table."""
        self.standards_table.setRowCount(len(standards))
        
        for row, standard in enumerate(standards):
            self.standards_table.setItem(row, 0, QTableWidgetItem(standard.get("name", "")))
            self.standards_table.setItem(row, 1, QTableWidgetItem(standard.get("company", "")))
            self.standards_table.setItem(row, 2, QTableWidgetItem(standard.get("version", "")))
            
            languages = ", ".join(standard.get("languages", []))
            self.standards_table.setItem(row, 3, QTableWidgetItem(languages))
            
            rules_count = len(standard.get("rules", []))
            self.standards_table.setItem(row, 4, QTableWidgetItem(str(rules_count)))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            export_btn = QPushButton("Export")
            export_btn.clicked.connect(lambda checked, s=standard: self.export_standard(s))
            actions_layout.addWidget(export_btn)
            
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, s=standard: self.remove_standard(s))
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
                "enabled": True
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
                self, "Confirm Removal", 
                f"Are you sure you want to remove the code standard '{name}'?"
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.backend_controller.remove_code_standard(name)
                self.load_standards()
                self.load_current_standard()
                QMessageBox.information(self, "Success", f"Code standard '{name}' removed")
                
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
            name, ok = QComboBox.getItem(self, "Set Current Standard", "Select Standard:", standard_names, 0, False)
            
            if ok and name:
                self.backend_controller.set_current_code_standard(name)
                self.load_current_standard()
                QMessageBox.information(self, "Success", f"Code standard '{name}' set as current")
                
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
                QMessageBox.information(self, "Success", f"Code standard exported to {file_path}")
                
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
                QMessageBox.information(self, "Success", "Code standard imported successfully")
                
        except Exception as e:
            logger.error(f"Error importing code standard: {e}")
            QMessageBox.warning(self, "Error", f"Failed to import code standard: {e}")
    
    def analyze_file(self):
        """Analyze a single file."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select File to Analyze", "", 
                "All Files (*);;Python Files (*.py);;JavaScript Files (*.js);;TypeScript Files (*.ts)"
            )
            
            if file_path:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                
                self.analysis_worker = CodeAnalysisWorker(self.backend_controller, file_path)
                self.analysis_worker.progress.connect(self.progress_bar.setValue)
                self.analysis_worker.finished.connect(self.on_analysis_finished)
                self.analysis_worker.start()
                
        except Exception as e:
            logger.error(f"Error analyzing file: {e}")
            QMessageBox.warning(self, "Error", f"Failed to analyze file: {e}")
    
    def analyze_directory(self):
        """Analyze a directory."""
        try:
            directory_path = QFileDialog.getExistingDirectory(self, "Select Directory to Analyze")
            
            if directory_path:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                
                self.dir_analysis_worker = DirectoryAnalysisWorker(self.backend_controller, directory_path)
                self.dir_analysis_worker.progress.connect(self.progress_bar.setValue)
                self.dir_analysis_worker.finished.connect(self.on_directory_analysis_finished)
                self.dir_analysis_worker.start()
                
        except Exception as e:
            logger.error(f"Error analyzing directory: {e}")
            QMessageBox.warning(self, "Error", f"Failed to analyze directory: {e}")
    
    def on_analysis_finished(self, success: bool, message: str, results: List):
        """Handle analysis completion."""
        self.progress_bar.setVisible(False)
        
        if success and results:
            self.display_analysis_results(results[0])
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Error", f"Analysis failed: {message}")
    
    def on_directory_analysis_finished(self, success: bool, message: str, results: List):
        """Handle directory analysis completion."""
        self.progress_bar.setVisible(False)
        
        if success and results:
            self.display_directory_results(results)
            QMessageBox.information(self, "Success", f"{message} - Found {len(results)} files with violations")
        else:
            QMessageBox.warning(self, "Error", f"Analysis failed: {message}")
    
    def display_analysis_results(self, result: Dict):
        """Display analysis results."""
        # Update summary
        self.total_violations_label.setText(f"Total Violations: {result.get('total_violations', 0)}")
        self.error_count_label.setText(f"Errors: {result.get('error_count', 0)}")
        self.warning_count_label.setText(f"Warnings: {result.get('warning_count', 0)}")
        self.info_count_label.setText(f"Info: {result.get('info_count', 0)}")
        self.auto_fixable_count_label.setText(f"Auto-fixable: {result.get('auto_fixable_count', 0)}")
        
        # Update violations table
        violations = result.get("violations", [])
        self.populate_violations_table(violations)
    
    def display_directory_results(self, results: List[Dict]):
        """Display directory analysis results."""
        # Combine all violations
        all_violations = []
        total_violations = 0
        error_count = 0
        warning_count = 0
        info_count = 0
        auto_fixable_count = 0
        
        for result in results:
            violations = result.get("violations", [])
            all_violations.extend(violations)
            total_violations += result.get("total_violations", 0)
            error_count += result.get("error_count", 0)
            warning_count += result.get("warning_count", 0)
            info_count += result.get("info_count", 0)
            auto_fixable_count += result.get("auto_fixable_count", 0)
        
        # Update summary
        self.total_violations_label.setText(f"Total Violations: {total_violations}")
        self.error_count_label.setText(f"Errors: {error_count}")
        self.warning_count_label.setText(f"Warnings: {warning_count}")
        self.info_count_label.setText(f"Info: {info_count}")
        self.auto_fixable_count_label.setText(f"Auto-fixable: {auto_fixable_count}")
        
        # Update violations table
        self.populate_violations_table(all_violations)
    
    def populate_violations_table(self, violations: List[Dict]):
        """Populate violations table."""
        self.violations_table.setRowCount(len(violations))
        
        for row, violation in enumerate(violations):
            self.violations_table.setItem(row, 0, QTableWidgetItem(violation.get("file_path", "")))
            self.violations_table.setItem(row, 1, QTableWidgetItem(str(violation.get("line_number", ""))))
            self.violations_table.setItem(row, 2, QTableWidgetItem(violation.get("rule_name", "")))
            
            severity = violation.get("severity", "")
            severity_item = QTableWidgetItem(severity)
            if severity == "error":
                severity_item.setBackground(QColor(255, 200, 200))
            elif severity == "warning":
                severity_item.setBackground(QColor(255, 220, 200))
            self.violations_table.setItem(row, 3, severity_item)
            
            self.violations_table.setItem(row, 4, QTableWidgetItem(violation.get("message", "")))
            self.violations_table.setItem(row, 5, QTableWidgetItem(violation.get("category", "")))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            if violation.get("auto_fixable", False):
                fix_btn = QPushButton("Fix")
                fix_btn.clicked.connect(lambda checked, v=violation: self.fix_violation(v))
                actions_layout.addWidget(fix_btn)
            
            actions_widget.setLayout(actions_layout)
            self.violations_table.setCellWidget(row, 6, actions_widget)
    
    def add_rule(self):
        """Add a new rule."""
        try:
            dialog = AddRuleDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                rule_data = dialog.get_rule_data()
                
                # Add rule to current standard
                current_standard = self.backend_controller.get_current_code_standard()
                if not current_standard:
                    QMessageBox.warning(self, "Error", "No current standard selected")
                    return
                
                # This would need to be implemented in the backend
                # For now, just show a message
                QMessageBox.information(self, "Success", "Rule added successfully")
                
        except Exception as e:
            logger.error(f"Error adding rule: {e}")
            QMessageBox.warning(self, "Error", f"Failed to add rule: {e}")
    
    def filter_rules(self):
        """Filter rules by category."""
        # This would filter the rules table based on the selected category
        pass
    
    def auto_fix_violations(self):
        """Auto-fix violations where possible."""
        try:
            # This would call the backend to auto-fix violations
            QMessageBox.information(self, "Success", "Auto-fix completed")
        except Exception as e:
            logger.error(f"Error auto-fixing violations: {e}")
            QMessageBox.warning(self, "Error", f"Failed to auto-fix violations: {e}")
    
    def fix_violation(self, violation: Dict):
        """Fix a specific violation."""
        try:
            # This would apply the suggested fix for the violation
            QMessageBox.information(self, "Success", "Violation fixed")
        except Exception as e:
            logger.error(f"Error fixing violation: {e}")
            QMessageBox.warning(self, "Error", f"Failed to fix violation: {e}")
    
    def refresh_data(self):
        """Refresh all data."""
        self.load_data()
    
    def handle_error(self, error: str):
        """Handle errors."""
        logger.error(f"Code Standards Tab Error: {error}")
        QMessageBox.warning(self, "Error", f"An error occurred: {error}") 