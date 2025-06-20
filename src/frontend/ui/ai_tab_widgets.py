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
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Issue information
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
        layout.addWidget(issue_group)
        
        # AI Analysis
        analysis_group = QGroupBox("AI Analysis")
        analysis_layout = QVBoxLayout(analysis_group)
        
        analysis_text = QTextEdit()
        analysis_text.setPlainText(self.enhancement_result.enhanced_analysis)
        analysis_text.setReadOnly(True)
        analysis_layout.addWidget(analysis_text)
        layout.addWidget(analysis_group)
        
        # Suggestions
        if self.enhancement_result.suggestions:
            suggestions_group = QGroupBox("Suggestions")
            suggestions_layout = QVBoxLayout(suggestions_group)
            
            suggestions_text = QTextEdit()
            suggestions_text.setPlainText("\n".join(f"• {s}" for s in self.enhancement_result.suggestions))
            suggestions_text.setMaximumHeight(150)
            suggestions_text.setReadOnly(True)
            suggestions_layout.addWidget(suggestions_text)
            layout.addWidget(suggestions_group)
        
        # Explanation
        if self.enhancement_result.explanation:
            explanation_group = QGroupBox("Explanation")
            explanation_layout = QVBoxLayout(explanation_group)
            
            explanation_text = QTextEdit()
            explanation_text.setPlainText(self.enhancement_result.explanation)
            explanation_text.setMaximumHeight(100)
            explanation_text.setReadOnly(True)
            explanation_layout.addWidget(explanation_text)
            layout.addWidget(explanation_group)
        
        # Model information
        model_info = QLabel(f"Model: {self.enhancement_result.model_used} | Confidence: {self.enhancement_result.confidence_score:.2f}")
        model_info.setAlignment(Qt.AlignmentFlag.AlignRight)
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
    2. AI Enhancement: On-demand AI analysis of specific issues
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
    w["model_source_selector"].addItem("Own Trained Model")
    w["ollama_model_label"] = QLabel("Ollama Model:")
    w["ollama_model_selector"] = QComboBox()
    w["refresh_models_button"] = QPushButton("Refresh Models")
    w["refresh_models_button"].clicked.connect(main_app_instance.populate_ollama_models)
    ollama_layout = QHBoxLayout()
    ollama_layout.addWidget(w["ollama_model_selector"])
    ollama_layout.addWidget(w["refresh_models_button"])
    w["model_status_label"] = QLabel("Status: Not Loaded")
    w["load_model_button"] = QPushButton("Load Trained Model")
    model_layout.addRow(QLabel("Model Source:"), w["model_source_selector"])
    model_layout.addRow(w["ollama_model_label"], ollama_layout)
    model_layout.addRow(QLabel("Own Model Status:"), w["model_status_label"])
    model_layout.addRow(w["load_model_button"])
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
    w["start_quick_scan_button"] = QPushButton("Run Analysis")
    w["start_quick_scan_button"].setFixedHeight(35)
    w["start_quick_scan_button"].clicked.connect(main_app_instance.start_quick_scan)
    w["stop_scan_button"] = QPushButton("Stop Scan")
    w["stop_scan_button"].setFixedHeight(35)
    w["stop_scan_button"].setEnabled(False)
    w["stop_scan_button"].clicked.connect(main_app_instance.stop_scan)
    scan_buttons_layout = QHBoxLayout()
    scan_buttons_layout.addWidget(w["start_quick_scan_button"])
    scan_buttons_layout.addWidget(w["stop_scan_button"])
    w["scan_progress_bar"] = QProgressBar()
    w["scan_status_label"] = QLabel("Status: Ready for Quick Scan")
    w["scan_status_label"].setAlignment(Qt.AlignmentFlag.AlignCenter)
    scan_layout.addRow(scan_buttons_layout)
    scan_layout.addRow(w["scan_progress_bar"])
    scan_layout.addRow(w["scan_status_label"])
    layout.addWidget(scan_group)

    # --- Results and AI Enhancement Group ---
    results_group = QGroupBox("3. Scan Results & AI Enhancement")
    results_layout = QVBoxLayout(results_group)
    
    # Create results table with the new structure
    w["scan_results_table"] = QTableWidget()
    w["scan_results_table"].setColumnCount(5)
    w["scan_results_table"].setHorizontalHeaderLabels([
        "File", "Line", "Issue", "Severity", "Enhance"
    ])
    
    # Set table properties
    header = w["scan_results_table"].horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # File
    header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Line
    header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Issue
    header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Severity
    header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Enhance
    
    w["scan_results_table"].setMaximumHeight(300)
    w["scan_results_table"].setAlternatingRowColors(True)
    
    # Summary text area
    w["scan_results_text"] = QTextEdit()
    w["scan_results_text"].setReadOnly(True)
    w["scan_results_text"].setPlaceholderText("Quick scan results will appear here...")
    w["scan_results_text"].setMaximumHeight(150)
    
    # Enhancement type selector
    enhancement_layout = QHBoxLayout()
    enhancement_layout.addWidget(QLabel("Enhancement Type:"))
    w["enhancement_type_selector"] = QComboBox()
    w["enhancement_type_selector"].addItems([
        "Code Improvement",
        "Security Analysis", 
        "Performance Optimization",
        "Best Practices",
        "Documentation",
        "Architectural Review"
    ])
    enhancement_layout.addWidget(w["enhancement_type_selector"])
    enhancement_layout.addStretch()
    
    # Buttons
    w["enhance_all_button"] = QPushButton("Enhance All Issues with AI")
    w["enhance_all_button"].setEnabled(False)
    w["enhance_all_button"].clicked.connect(main_app_instance.enhance_all_issues)
    
    w["create_report_button"] = QPushButton("Generate Full Markdown Report")
    w["create_report_button"].setEnabled(False)
    w["create_report_button"].clicked.connect(main_app_instance.start_report_generation)
    
    w["clear_results_button"] = QPushButton("Clear Results")
    w["clear_results_button"].setEnabled(False)
    w["clear_results_button"].clicked.connect(lambda: clear_scan_results(w))
    
    results_layout.addWidget(w["scan_results_table"])
    results_layout.addWidget(w["scan_results_text"])
    results_layout.addLayout(enhancement_layout)
    results_layout.addWidget(w["enhance_all_button"])
    results_layout.addWidget(w["create_report_button"])
    results_layout.addWidget(w["clear_results_button"])
    layout.addWidget(results_group)

    layout.addStretch(1)


def clear_scan_results(widgets: Dict[str, Any]):
    """Clear the scan results table and text."""
    widgets["scan_results_table"].setRowCount(0)
    widgets["scan_results_text"].clear()
    widgets["enhance_all_button"].setEnabled(False)
    widgets["create_report_button"].setEnabled(False)
    widgets["clear_results_button"].setEnabled(False)
    widgets["scan_status_label"].setText("Status: Ready for Quick Scan")


def populate_scan_results_table(widgets: Dict[str, Any], issues: List[Dict[str, Any]]):
    """Populate the scan results table with issues."""
    table = widgets["scan_results_table"]
    table.setRowCount(len(issues))
    
    for row, issue in enumerate(issues):
        # File
        table.setItem(row, 0, QTableWidgetItem(issue.get("file", "")))
        
        # Line
        table.setItem(row, 1, QTableWidgetItem(str(issue.get("line", 0))))
        
        # Issue description
        issue_text = issue.get("issue", "")
        if len(issue_text) > 100:
            issue_text = issue_text[:97] + "..."
        table.setItem(row, 2, QTableWidgetItem(issue_text))
        
        # Severity
        severity_item = QTableWidgetItem(issue.get("severity", "medium"))
        severity = issue.get("severity", "medium").lower()
        if severity == "high":
            severity_item.setBackground(Qt.GlobalColor.red)
        elif severity == "medium":
            severity_item.setBackground(Qt.GlobalColor.yellow)
        elif severity == "low":
            severity_item.setBackground(Qt.GlobalColor.green)
        table.setItem(row, 3, severity_item)
        
        # AI Enhance button
        enhance_button = QPushButton("Enhance")
        # Store the table reference in the issue data for the callback
        issue["_table"] = table
        enhance_button.clicked.connect(lambda checked, row=row, issue=issue: enhance_single_issue(row, issue))
        table.setCellWidget(row, 4, enhance_button)
    
    # Enable post-scan buttons
    widgets["enhance_all_button"].setEnabled(True)
    widgets["create_report_button"].setEnabled(True)
    widgets["clear_results_button"].setEnabled(True)


def enhance_single_issue(row: int, issue_data: Dict[str, Any]):
    """Enhance a single issue with AI analysis."""
    try:
        # Get the main app instance from the table's parent widget
        table = issue_data.get("_table")
        if table:
            main_app = table.parent().parent().parent().parent()
            
            # Get enhancement type from selector
            enhancement_type_map = {
                "Code Improvement": "code_improvement",
                "Security Analysis": "security_analysis",
                "Performance Optimization": "performance_optimization", 
                "Best Practices": "best_practices",
                "Documentation": "documentation",
                "Architectural Review": "architectural_review"
            }
            
            enhancement_type = main_app.widgets["ai_tab"]["enhancement_type_selector"].currentText()
            enhancement_type_key = enhancement_type_map.get(enhancement_type, "code_improvement")
            
            # Start AI enhancement
            main_app.enhance_issue_with_ai(issue_data, enhancement_type_key)
            
    except Exception as e:
        logger.error(f"Error enhancing single issue: {e}")
        QMessageBox.warning(None, "Error", f"Failed to enhance issue: {e}")


def update_scan_summary(widgets: Dict[str, Any], issues: List[Dict[str, Any]]):
    """Update the scan summary text."""
    if not issues:
        widgets["scan_results_text"].setPlainText("No issues found in the quick scan.")
        return
    
    # Count issues by severity
    severity_counts = {}
    type_counts = {}
    
    for issue in issues:
        severity = issue.get("severity", "unknown")
        issue_type = issue.get("type", "unknown")
        
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
    
    # Create summary text
    summary = f"Quick Scan Complete!\n\n"
    summary += f"Total Issues Found: {len(issues)}\n\n"
    
    summary += "Issues by Severity:\n"
    for severity, count in sorted(severity_counts.items()):
        summary += f"  {severity.title()}: {count}\n"
    
    summary += "\nIssues by Type:\n"
    for issue_type, count in sorted(type_counts.items()):
        summary += f"  {issue_type.title()}: {count}\n"
    
    summary += "\nClick 'Enhance' buttons to get AI-powered analysis of specific issues."
    
    widgets["scan_results_text"].setPlainText(summary)
