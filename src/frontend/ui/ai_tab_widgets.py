"""
ai_tab_widgets.py

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
import logging
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QSplitter,
    QFrame,
)

logger = logging.getLogger(__name__)


class AIEnhancementDialog(QDialog):
    """Dialog for displaying AI enhancement results."""
    
    def __init__(self, issue_data: Dict[str, Any], enhancement_result: Any, parent=None):
        super().__init__(parent)
        self.issue_data = issue_data
        self.enhancement_result = enhancement_result
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("AI Enhancement Analysis")
        self.setModal(True)
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # Create splitter for better layout
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top section - Issue information
        issue_group = QGroupBox("Original Issue")
        issue_layout = QVBoxLayout(issue_group)
        
        issue_info = f"""
File: {self.issue_data.get('file', 'Unknown')}
Line: {self.issue_data.get('line', 0)}
Severity: {self.issue_data.get('severity', 'Unknown')}
Type: {self.issue_data.get('type', 'Unknown')}

Issue: {self.issue_data.get('issue', 'No description')}

Code Snippet:
{self.issue_data.get('code_snippet', 'No code available')}
"""
        
        issue_text = QTextEdit()
        issue_text.setPlainText(issue_info)
        issue_text.setMaximumHeight(200)
        issue_text.setReadOnly(True)
        issue_layout.addWidget(issue_text)
        splitter.addWidget(issue_group)
        
        # Middle section - AI Analysis
        analysis_group = QGroupBox("AI Analysis")
        analysis_layout = QVBoxLayout(analysis_group)
        
        analysis_text = QTextEdit()
        analysis_text.setPlainText(self.enhancement_result.enhanced_analysis)
        analysis_text.setReadOnly(True)
        analysis_layout.addWidget(analysis_text)
        splitter.addWidget(analysis_group)
        
        # Bottom section - Suggestions and Details
        details_group = QGroupBox("Suggestions & Details")
        details_layout = QVBoxLayout(details_group)
        
        # Suggestions
        if self.enhancement_result.suggestions:
            suggestions_label = QLabel("Suggestions:")
            suggestions_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            details_layout.addWidget(suggestions_label)
            
            suggestions_text = QTextEdit()
            suggestions_text.setPlainText("\n".join(f"• {s}" for s in self.enhancement_result.suggestions))
            suggestions_text.setMaximumHeight(120)
            suggestions_text.setReadOnly(True)
            details_layout.addWidget(suggestions_text)
        
        # Code Changes
        if self.enhancement_result.code_changes:
            changes_label = QLabel("Proposed Code Changes:")
            changes_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            details_layout.addWidget(changes_label)
            
            changes_text = QTextEdit()
            changes_content = []
            for change in self.enhancement_result.code_changes:
                changes_content.append(f"Line {change.get('line', 'N/A')}:")
                changes_content.append(f"Type: {change.get('type', 'N/A')}")
                if change.get('old_code'):
                    changes_content.append(f"Old: {change['old_code']}")
                if change.get('new_code'):
                    changes_content.append(f"New: {change['new_code']}")
                if change.get('explanation'):
                    changes_content.append(f"Reason: {change['explanation']}")
                changes_content.append("")
            
            changes_text.setPlainText("\n".join(changes_content))
            changes_text.setMaximumHeight(150)
            changes_text.setReadOnly(True)
            details_layout.addWidget(changes_text)
        
        # Security and Performance implications
        if self.enhancement_result.security_implications:
            security_label = QLabel("Security Implications:")
            security_label.setStyleSheet("font-weight: bold; color: #d32f2f; margin-top: 10px;")
            details_layout.addWidget(security_label)
            
            security_text = QTextEdit()
            security_text.setPlainText(self.enhancement_result.security_implications)
            security_text.setMaximumHeight(80)
            security_text.setReadOnly(True)
            details_layout.addWidget(security_text)
        
        if self.enhancement_result.performance_impact:
            perf_label = QLabel("Performance Impact:")
            perf_label.setStyleSheet("font-weight: bold; color: #1976d2; margin-top: 10px;")
            details_layout.addWidget(perf_label)
            
            perf_text = QTextEdit()
            perf_text.setPlainText(self.enhancement_result.performance_impact)
            perf_text.setMaximumHeight(80)
            perf_text.setReadOnly(True)
            details_layout.addWidget(perf_text)
        
        # Explanation
        if self.enhancement_result.explanation:
            explanation_label = QLabel("Explanation:")
            explanation_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            details_layout.addWidget(explanation_label)
            
            explanation_text = QTextEdit()
            explanation_text.setPlainText(self.enhancement_result.explanation)
            explanation_text.setMaximumHeight(100)
            explanation_text.setReadOnly(True)
            details_layout.addWidget(explanation_text)
        
        splitter.addWidget(details_group)
        layout.addWidget(splitter)
        
        # Model information and confidence
        model_info = QLabel(
            f"Model: {self.enhancement_result.model_used} | "
            f"Confidence: {self.enhancement_result.confidence_score:.2f} | "
            f"Processing Time: {self.enhancement_result.processing_time:.2f}s"
        )
        model_info.setAlignment(Qt.AlignmentFlag.AlignRight)
        model_info.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(model_info)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)


def setup_ai_tab(parent_widget: QWidget, main_app_instance: Any) -> None:
    """
    Sets up the UI components for the AI code analysis tab.
    
    This implements the two-stage analysis approach:
    1. Quick Scan: Immediate local analysis using static rules
    2. AI Enhancement: On-demand AI analysis of specific issues using specialized local models
    """
    # Initialize widget dictionary for AI tab
    if not hasattr(main_app_instance, "widgets"):
        main_app_instance.widgets = {}
    main_app_instance.widgets["ai_tab"] = {}
    w = main_app_instance.widgets["ai_tab"]

    layout = QVBoxLayout(parent_widget)

    # --- Model Selection Group ---
    model_group = QGroupBox("1. AI Model Configuration")
    model_layout = QFormLayout(model_group)

    w["model_source_selector"] = QComboBox()
    w["model_source_selector"].addItem("Ollama")
    w["model_source_selector"].addItem("Fine-tuned Local Model")
    w["model_source_selector"].currentTextChanged.connect(main_app_instance.on_model_source_changed)
    
    w["ollama_model_label"] = QLabel("Ollama Model:")
    w["ollama_model_selector"] = QComboBox()
    w["refresh_models_button"] = QPushButton("Refresh Models")
    w["refresh_models_button"].clicked.connect(main_app_instance.populate_ollama_models)
    
    ollama_layout = QHBoxLayout()
    ollama_layout.addWidget(w["ollama_model_selector"])
    ollama_layout.addWidget(w["refresh_models_button"])
    
    w["model_status_label"] = QLabel("Status: Not Loaded")
    w["load_model_button"] = QPushButton("Load Fine-tuned Model")
    w["load_model_button"].clicked.connect(main_app_instance.load_fine_tuned_model)
    
    # Model info display
    w["model_info_label"] = QLabel("No model information available")
    w["model_info_label"].setStyleSheet("color: #666; font-size: 11px;")
    
    model_layout.addRow(QLabel("Model Source:"), w["model_source_selector"])
    model_layout.addRow(w["ollama_model_label"], ollama_layout)
    model_layout.addRow(QLabel("Model Status:"), w["model_status_label"])
    model_layout.addRow(w["load_model_button"])
    model_layout.addRow(QLabel("Model Info:"), w["model_info_label"])
    layout.addWidget(model_group)

    # --- Quick Scan Configuration Group ---
    scan_group = QGroupBox("2. Quick Scan Configuration")
    scan_layout = QFormLayout(scan_group)
    w["project_dir_edit"] = QLineEdit()
    w["project_dir_edit"].setText(os.getcwd())
    w["project_dir_edit"].setPlaceholderText("Select a project folder to scan...")
    w["browse_button"] = QPushButton("Browse...")
    w["browse_button"].clicked.connect(main_app_instance.select_scan_directory)
    scan_dir_layout = QHBoxLayout()
    scan_dir_layout.addWidget(w["project_dir_edit"])
    scan_dir_layout.addWidget(w["browse_button"])
    w["include_patterns_edit"] = QLineEdit()
    w["include_patterns_edit"].setText("*.py,*.js,*.ts,*.java,*.cpp,*.c,*.h,*.hpp")
    w["exclude_patterns_edit"] = QLineEdit()
    w["exclude_patterns_edit"].setText(
        "__pycache__/*,node_modules/*,.git/*,*.pyc,*.log"
    )
    scan_layout.addRow(QLabel("Project Directory:"), scan_dir_layout)
    scan_layout.addRow(QLabel("Include Patterns:"), w["include_patterns_edit"])
    scan_layout.addRow(QLabel("Exclude Patterns:"), w["exclude_patterns_edit"])
    w["start_quick_scan_button"] = QPushButton("Run Quick Scan")
    w["start_quick_scan_button"].setFixedHeight(35)
    w["start_quick_scan_button"].clicked.connect(main_app_instance.start_quick_scan)
    w["stop_scan_button"] = QPushButton("Stop Scan")
    w["stop_scan_button"].setFixedHeight(35)
    w["stop_scan_button"].setEnabled(False)
    w["stop_scan_button"].clicked.connect(main_app_instance.stop_scan)
    
    scan_buttons_layout = QHBoxLayout()
    scan_buttons_layout.addWidget(w["start_quick_scan_button"])
    scan_buttons_layout.addWidget(w["stop_scan_button"])
    scan_layout.addRow(scan_buttons_layout)
    layout.addWidget(scan_group)

    # --- Scan Results Group ---
    results_group = QGroupBox("3. Scan Results & AI Enhancement")
    results_layout = QVBoxLayout(results_group)
    
    # Status and progress
    w["scan_status_label"] = QLabel("Ready to scan")
    w["scan_progress_bar"] = QProgressBar()
    w["scan_progress_bar"].setVisible(False)
    
    status_layout = QHBoxLayout()
    status_layout.addWidget(w["scan_status_label"])
    status_layout.addWidget(w["scan_progress_bar"])
    results_layout.addLayout(status_layout)
    
    # Results table
    w["results_table"] = QTableWidget()
    w["results_table"].setColumnCount(6)
    w["results_table"].setHorizontalHeaderLabels([
        "File", "Line", "Type", "Severity", "Issue", "Actions"
    ])
    w["results_table"].horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    w["results_table"].horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
    results_layout.addWidget(w["results_table"])
    
    # Summary and actions
    w["summary_label"] = QLabel("No issues found")
    w["summary_label"].setStyleSheet("font-weight: bold; color: #666;")
    
    w["enhance_all_button"] = QPushButton("Enhance All Issues with AI")
    w["enhance_all_button"].setEnabled(False)
    w["enhance_all_button"].clicked.connect(main_app_instance.enhance_all_issues)
    
    w["export_results_button"] = QPushButton("Export Results")
    w["export_results_button"].setEnabled(False)
    w["export_results_button"].clicked.connect(main_app_instance.export_scan_results)
    
    actions_layout = QHBoxLayout()
    actions_layout.addWidget(w["summary_label"])
    actions_layout.addStretch()
    actions_layout.addWidget(w["enhance_all_button"])
    actions_layout.addWidget(w["export_results_button"])
    results_layout.addLayout(actions_layout)
    
    layout.addWidget(results_group)

    # Connect table signals
    w["results_table"].cellDoubleClicked.connect(main_app_instance.on_issue_double_clicked)
    
    # Initial model source change
    main_app_instance.on_model_source_changed(w["model_source_selector"].currentText())


def clear_scan_results(widgets: Dict[str, Any]):
    """Clear the scan results table and reset status."""
    widgets["results_table"].setRowCount(0)
    widgets["summary_label"].setText("No issues found")
    widgets["enhance_all_button"].setEnabled(False)
    widgets["export_results_button"].setEnabled(False)
    widgets["scan_status_label"].setText("Ready to scan")


def populate_scan_results_table(widgets: Dict[str, Any], issues: List[Dict[str, Any]]):
    """Populate the scan results table with issues."""
    table = widgets["results_table"]
    table.setRowCount(len(issues))
    
    for row, issue in enumerate(issues):
        # File column
        file_item = QTableWidgetItem(issue.get("file", ""))
        file_item.setData(Qt.ItemDataRole.UserRole, issue)
        table.setItem(row, 0, file_item)
        
        # Line column
        line_item = QTableWidgetItem(str(issue.get("line", "")))
        table.setItem(row, 1, line_item)
        
        # Type column
        type_item = QTableWidgetItem(issue.get("type", ""))
        table.setItem(row, 2, type_item)
        
        # Severity column
        severity_item = QTableWidgetItem(issue.get("severity", ""))
        severity_item.setData(Qt.ItemDataRole.UserRole, issue.get("severity", ""))
        table.setItem(row, 3, severity_item)
        
        # Issue column
        issue_item = QTableWidgetItem(issue.get("issue", ""))
        table.setItem(row, 4, issue_item)
        
        # Actions column
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(2, 2, 2, 2)
        
        enhance_button = QPushButton("AI Enhance")
        enhance_button.setFixedSize(80, 25)
        enhance_button.clicked.connect(lambda checked, r=row: enhance_single_issue(r, issue))
        
        actions_layout.addWidget(enhance_button)
        actions_layout.addStretch()
        table.setCellWidget(row, 5, actions_widget)
    
    # Update summary
    update_scan_summary(widgets, issues)
    
    # Enable action buttons
    widgets["enhance_all_button"].setEnabled(len(issues) > 0)
    widgets["export_results_button"].setEnabled(len(issues) > 0)


def enhance_single_issue(row: int, issue_data: Dict[str, Any]):
    """Enhance a single issue with AI analysis."""
    # This will be connected to the main app's enhancement method
    # The actual implementation will be in the main window
    pass


def update_scan_summary(widgets: Dict[str, Any], issues: List[Dict[str, Any]]):
    """Update the scan summary label."""
    if not issues:
        widgets["summary_label"].setText("No issues found")
        return
    
    total_issues = len(issues)
    high_severity = sum(1 for issue in issues if issue.get("severity") == "High")
    medium_severity = sum(1 for issue in issues if issue.get("severity") == "Medium")
    low_severity = sum(1 for issue in issues if issue.get("severity") == "Low")
    
    summary_text = f"Found {total_issues} issues: {high_severity} High, {medium_severity} Medium, {low_severity} Low"
    widgets["summary_label"].setText(summary_text)
