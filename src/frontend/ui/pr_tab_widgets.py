"""
pr_tab_widgets.py

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
PR Creation Tab Widgets
Provides GUI components for AI-powered PR creation and review.
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QLineEdit, QFileDialog, QMessageBox,
    QGroupBox, QCheckBox, QSpinBox, QListWidget, QListWidgetItem,
    QProgressBar, QTabWidget, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QTextCursor

# TODO: The following imports are commented out because the modules do not exist in the current codebase.
# from ..pr.pr_creator import PRCreator
# from ..pr.ai_advisor import AIAdvisor, PriorityStrategy
# from ..pr.scan_integrator import ScanIntegrator
# from ..pr.pr_templates import PRType
from backend.utils.constants import WAIT_TIMEOUT_SHORT_MS, SPLITTER_LEFT_SIZE, SPLITTER_RIGHT_SIZE


class PRCreationWorker(QThread):
    """Worker thread for PR creation to avoid blocking the UI."""
    
    progress_updated = pyqtSignal(int, int, str)
    pr_created = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, scan_files: List[str], config: Dict[str, Any]):
        super().__init__()
        self.scan_files = scan_files
        self.config = config
    
    def run(self):
        try:
            # Simulate PR creation process
            self.progress_updated.emit(1, 5, "Loading scan results...")
            self.msleep(WAIT_TIMEOUT_SHORT_MS)
            
            self.progress_updated.emit(2, 5, "Integrating scan results...")
            self.msleep(WAIT_TIMEOUT_SHORT_MS)
            
            self.progress_updated.emit(3, 5, "Getting AI recommendations...")
            self.msleep(WAIT_TIMEOUT_SHORT_MS)
            
            self.progress_updated.emit(4, 5, "Creating PR...")
            self.msleep(WAIT_TIMEOUT_SHORT_MS)
            
            self.progress_updated.emit(5, 5, "PR created successfully!")
            
            # Return mock result
            result = {
                'success': True,
                'title': 'AI-Powered Code Quality Improvements',
                'description': 'This PR addresses code quality issues identified by AI analysis.',
                'branch_name': 'ai-code-quality-fix',
                'commit_hash': 'abc123',
                'pr_url': 'https://github.com/example/pull/123',
                'files_changed': ['src/main.py', 'src/core/analyzer.py'],
                'status': 'ready',
                'issues': [
                    {'issue_type': 'code_smell', 'severity': 'medium'},
                    {'issue_type': 'security_vulnerability', 'severity': 'high'}
                ],
                'priority_order': ['security_vulnerability', 'code_smell'],
                'estimated_time': '2 hours',
                'risk_impact': 'Low risk, improves code quality',
                'review_notes': 'Please review the AI-generated fixes for accuracy.'
            }
            
            self.pr_created.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class PRCreationTab(QWidget):
    """Main PR creation tab widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scan_files = []
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the PR creation UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("AI-Powered PR Creation and Review")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Configuration
        left_panel = self.create_configuration_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Preview and Results
        right_panel = self.create_preview_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([SPLITTER_LEFT_SIZE, SPLITTER_RIGHT_SIZE])
        
        # Bottom panel - Actions
        bottom_panel = self.create_actions_panel()
        layout.addWidget(bottom_panel)
    
    def create_configuration_panel(self) -> QWidget:
        """Create the configuration panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Scan Results Selection
        scan_group = QGroupBox("Scan Results")
        scan_layout = QVBoxLayout(scan_group)
        
        self.scan_files_list = QListWidget()
        scan_layout.addWidget(self.scan_files_list)
        
        scan_buttons_layout = QHBoxLayout()
        self.add_scan_files_btn = QPushButton("Add Scan Files")
        self.clear_scan_files_btn = QPushButton("Clear All")
        scan_buttons_layout.addWidget(self.add_scan_files_btn)
        scan_buttons_layout.addWidget(self.clear_scan_files_btn)
        scan_layout.addLayout(scan_buttons_layout)
        
        layout.addWidget(scan_group)
        
        # PR Configuration
        config_group = QGroupBox("PR Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # Repository path
        repo_layout = QHBoxLayout()
        repo_layout.addWidget(QLabel("Repository Path:"))
        self.repo_path_edit = QLineEdit(".")
        self.browse_repo_btn = QPushButton("Browse")
        repo_layout.addWidget(self.repo_path_edit)
        repo_layout.addWidget(self.browse_repo_btn)
        config_layout.addLayout(repo_layout)
        
        # Base branch
        branch_layout = QHBoxLayout()
        branch_layout.addWidget(QLabel("Base Branch:"))
        self.base_branch_edit = QLineEdit("main")
        branch_layout.addWidget(self.base_branch_edit)
        config_layout.addLayout(branch_layout)
        
        # PR Type
        pr_type_layout = QHBoxLayout()
        pr_type_layout.addWidget(QLabel("PR Type:"))
        self.pr_type_combo = QComboBox()
        self.pr_type_combo.addItems([
            "security_fix", "code_quality", "performance", 
            "compliance", "refactoring", "bug_fix"
        ])
        pr_type_layout.addWidget(self.pr_type_combo)
        config_layout.addLayout(pr_type_layout)
        
        # Priority Strategy
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("Priority Strategy:"))
        self.priority_strategy_combo = QComboBox()
        self.priority_strategy_combo.addItems([
            "severity_first", "easy_win_first", "balanced", "impact_first"
        ])
        priority_layout.addWidget(self.priority_strategy_combo)
        config_layout.addLayout(priority_layout)
        
        # Template Standard
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Template Standard:"))
        self.template_standard_combo = QComboBox()
        self.template_standard_combo.addItems([
            "conventional_commits", "github_standard", "enterprise", "open_source"
        ])
        template_layout.addWidget(self.template_standard_combo)
        config_layout.addLayout(template_layout)
        
        layout.addWidget(config_group)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.deduplicate_check = QCheckBox("Deduplicate Issues")
        self.deduplicate_check.setChecked(True)
        options_layout.addWidget(self.deduplicate_check)
        
        self.auto_commit_check = QCheckBox("Auto Commit Changes")
        self.auto_commit_check.setChecked(True)
        options_layout.addWidget(self.auto_commit_check)
        
        self.auto_push_check = QCheckBox("Auto Push Branch")
        options_layout.addWidget(self.auto_push_check)
        
        self.create_pr_check = QCheckBox("Create GitHub PR")
        options_layout.addWidget(self.create_pr_check)
        
        self.dry_run_check = QCheckBox("Dry Run (Preview Only)")
        options_layout.addWidget(self.dry_run_check)
        
        layout.addWidget(options_group)
        
        return panel
    
    def create_preview_panel(self) -> QWidget:
        """Create the preview panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Create tab widget for different previews
        self.preview_tabs = QTabWidget()
        
        # PR Preview Tab
        self.pr_preview_edit = QTextEdit()
        self.pr_preview_edit.setPlaceholderText("PR preview will appear here...")
        self.preview_tabs.addTab(self.pr_preview_edit, "PR Preview")
        
        # Issues Summary Tab
        self.issues_summary_edit = QTextEdit()
        self.issues_summary_edit.setPlaceholderText("Issues summary will appear here...")
        self.preview_tabs.addTab(self.issues_summary_edit, "Issues Summary")
        
        # AI Recommendations Tab
        self.ai_recommendations_edit = QTextEdit()
        self.ai_recommendations_edit.setPlaceholderText("AI recommendations will appear here...")
        self.preview_tabs.addTab(self.ai_recommendations_edit, "AI Recommendations")
        
        layout.addWidget(self.preview_tabs)
        
        return panel
    
    def create_actions_panel(self) -> QWidget:
        """Create the actions panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(panel)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Action buttons
        self.preview_btn = QPushButton("Preview PR")
        self.create_pr_btn = QPushButton("Create PR")
        self.export_config_btn = QPushButton("Export Config")
        self.import_config_btn = QPushButton("Import Config")
        
        layout.addWidget(self.preview_btn)
        layout.addWidget(self.create_pr_btn)
        layout.addWidget(self.export_config_btn)
        layout.addWidget(self.import_config_btn)
        
        return panel
    
    def setup_connections(self):
        """Setup signal connections."""
        self.add_scan_files_btn.clicked.connect(self.add_scan_files)
        self.clear_scan_files_btn.clicked.connect(self.clear_scan_files)
        self.browse_repo_btn.clicked.connect(self.browse_repository)
        self.preview_btn.clicked.connect(self.preview_pr)
        self.create_pr_btn.clicked.connect(self.create_pr)
        self.export_config_btn.clicked.connect(self.export_config)
        self.import_config_btn.clicked.connect(self.import_config)
    
    def add_scan_files(self):
        """Add scan result files."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Scan Result Files", "", 
            "JSON Files (*.json);;All Files (*)"
        )
        
        for file_path in files:
            if file_path not in self.scan_files:
                self.scan_files.append(file_path)
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                self.scan_files_list.addItem(item)
    
    def clear_scan_files(self):
        """Clear all scan files."""
        self.scan_files.clear()
        self.scan_files_list.clear()
    
    def browse_repository(self):
        """Browse for repository path."""
        path = QFileDialog.getExistingDirectory(self, "Select Repository Path")
        if path:
            self.repo_path_edit.setText(path)
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return {
            'scan_result_files': self.scan_files,
            'repository_path': self.repo_path_edit.text(),
            'base_branch': self.base_branch_edit.text(),
            'pr_type': self.pr_type_combo.currentText(),
            'priority_strategy': self.priority_strategy_combo.currentText(),
            'template_standard': self.template_standard_combo.currentText(),
            'deduplicate': self.deduplicate_check.isChecked(),
            'auto_commit': self.auto_commit_check.isChecked(),
            'auto_push': self.auto_push_check.isChecked(),
            'create_pr': self.create_pr_check.isChecked(),
            'dry_run': self.dry_run_check.isChecked()
        }
    
    def preview_pr(self):
        """Preview the PR without creating it."""
        if not self.scan_files:
            QMessageBox.warning(self, "Warning", "Please add scan result files first.")
            return
        
        try:
            config = self.get_config()
            config['dry_run'] = True
            
            # Create worker for preview
            self.worker = PRCreationWorker(self.scan_files, config)
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.pr_created.connect(self.show_preview)
            self.worker.error_occurred.connect(self.show_error)
            
            self.progress_bar.setVisible(True)
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error previewing PR: {e}")
    
    def create_pr(self):
        """Create the PR."""
        if not self.scan_files:
            QMessageBox.warning(self, "Warning", "Please add scan result files first.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm PR Creation", 
            "Are you sure you want to create a PR? This will make changes to your repository.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                config = self.get_config()
                
                # Create worker for PR creation
                self.worker = PRCreationWorker(self.scan_files, config)
                self.worker.progress_updated.connect(self.update_progress)
                self.worker.pr_created.connect(self.show_pr_result)
                self.worker.error_occurred.connect(self.show_error)
                
                self.progress_bar.setVisible(True)
                self.worker.start()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error creating PR: {e}")
    
    @pyqtSlot(int, int, str)
    def update_progress(self, current: int, total: int, message: str):
        """Update progress bar."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"{message} ({current}/{total})")
    
    @pyqtSlot(dict)
    def show_preview(self, result: Dict[str, Any]):
        """Show PR preview."""
        self.progress_bar.setVisible(False)
        
        # Show PR preview
        pr_text = f"""# PR Preview

## Title
{result.get('title', 'N/A')}

## Description
{result.get('description', 'N/A')}

## Branch
{result.get('branch_name', 'N/A')}

## Files Changed
{result.get('files_changed', [])}

## Status
{result.get('status', 'N/A')}
"""
        self.pr_preview_edit.setPlainText(pr_text)
        
        # Show issues summary
        issues_text = f"""# Issues Summary

Total Issues: {len(result.get('issues', []))}

## Issues by Type
{self.format_issues_by_type(result.get('issues', []))}

## Issues by Severity
{self.format_issues_by_severity(result.get('issues', []))}
"""
        self.issues_summary_edit.setPlainText(issues_text)
        
        # Show AI recommendations
        ai_text = f"""# AI Recommendations

## Priority Order
{result.get('priority_order', [])}

## Estimated Time
{result.get('estimated_time', 'N/A')}

## Risk Impact
{result.get('risk_impact', 'N/A')}

## Review Notes
{result.get('review_notes', 'N/A')}
"""
        self.ai_recommendations_edit.setPlainText(ai_text)
        
        QMessageBox.information(self, "Preview Complete", "PR preview generated successfully!")
    
    @pyqtSlot(dict)
    def show_pr_result(self, result: Dict[str, Any]):
        """Show PR creation result."""
        self.progress_bar.setVisible(False)
        
        if result.get('success', False):
            message = f"""PR created successfully!

Branch: {result.get('branch_name', 'N/A')}
Commit: {result.get('commit_hash', 'N/A')}
PR URL: {result.get('pr_url', 'N/A')}
"""
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", f"Failed to create PR: {result.get('error_message', 'Unknown error')}")
    
    @pyqtSlot(str)
    def show_error(self, error: str):
        """Show error message."""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"An error occurred: {error}")
    
    def format_issues_by_type(self, issues: List[Dict]) -> str:
        """Format issues by type."""
        type_counts = {}
        for issue in issues:
            issue_type = issue.get('issue_type', 'unknown')
            type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        
        result = []
        for issue_type, count in sorted(type_counts.items()):
            result.append(f"- {issue_type}: {count}")
        
        return '\n'.join(result)
    
    def format_issues_by_severity(self, issues: List[Dict]) -> str:
        """Format issues by severity."""
        severity_counts = {}
        for issue in issues:
            severity = issue.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        result = []
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity in severity_counts:
                result.append(f"- {severity}: {severity_counts[severity]}")
        
        return '\n'.join(result)
    
    def export_config(self):
        """Export current configuration."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Configuration", "", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                config = self.get_config()
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=2)
                QMessageBox.information(self, "Success", "Configuration exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export configuration: {e}")
    
    def import_config(self):
        """Import configuration."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Configuration", "", "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                
                # Apply configuration
                self.apply_config(config)
                QMessageBox.information(self, "Success", "Configuration imported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import configuration: {e}")
    
    def apply_config(self, config: Dict[str, Any]):
        """Apply configuration to UI."""
        self.repo_path_edit.setText(config.get('repository_path', '.'))
        self.base_branch_edit.setText(config.get('base_branch', 'main'))
        
        # Set combo box values
        pr_type = config.get('pr_type', 'code_quality')
        index = self.pr_type_combo.findText(pr_type)
        if index >= 0:
            self.pr_type_combo.setCurrentIndex(index)
        
        priority_strategy = config.get('priority_strategy', 'balanced')
        index = self.priority_strategy_combo.findText(priority_strategy)
        if index >= 0:
            self.priority_strategy_combo.setCurrentIndex(index)
        
        template_standard = config.get('template_standard', 'github_standard')
        index = self.template_standard_combo.findText(template_standard)
        if index >= 0:
            self.template_standard_combo.setCurrentIndex(index)
        
        # Set checkboxes
        self.deduplicate_check.setChecked(config.get('deduplicate', True))
        self.auto_commit_check.setChecked(config.get('auto_commit', True))
        self.auto_push_check.setChecked(config.get('auto_push', False))
        self.create_pr_check.setChecked(config.get('create_pr', False))
        self.dry_run_check.setChecked(config.get('dry_run', False))
        
        # Load scan files
        scan_files = config.get('scan_result_files', [])
        self.scan_files = scan_files
        self.scan_files_list.clear()
        for file_path in scan_files:
            if os.path.exists(file_path):
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                self.scan_files_list.addItem(item)


def setup_pr_tab(parent_widget: QWidget, main_window) -> QWidget:
    """Setup the PR creation tab."""
    pr_tab = PRCreationTab(parent_widget)
    return pr_tab 