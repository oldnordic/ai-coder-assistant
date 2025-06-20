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

from typing import List, Dict, Any, Optional, Callable
import concurrent.futures

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QComboBox, QLineEdit, QFileDialog, QMessageBox,
    QGroupBox, QCheckBox, QListWidget, QProgressBar, QTabWidget, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QFont


# Constants for splitter sizes
SPLITTER_LEFT_SIZE = 400
SPLITTER_RIGHT_SIZE = 600

def pr_creation_backend(
    scan_files: List[str], 
    config: Dict[str, Any], 
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    log_message_callback: Optional[Callable[[str], None]] = None,
    cancellation_callback: Optional[Callable[[], bool]] = None
) -> Optional[Dict[str, Any]]:
    import time
    steps = [
        ("Loading scan results...", 1),
        ("Integrating scan results...", 2),
        ("Getting AI recommendations...", 3),
        ("Creating PR...", 4),
        ("PR created successfully!", 5),
    ]
    total = len(steps)
    for i, (msg, step) in enumerate(steps, 1):
        if cancellation_callback and cancellation_callback():
            if log_message_callback:
                log_message_callback("PR creation cancelled.")
            return None
        if progress_callback:
            progress_callback(i, total, msg)
        if log_message_callback:
            log_message_callback(msg)
        time.sleep(0.5)  # Simulate work
        
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
    return result

class PRCreationTab(QWidget):
    """Main PR creation tab widget."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.scan_files: List[str] = []
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the PR creation UI."""
        main_layout = QVBoxLayout(self)
        
        title = QLabel("AI-Powered PR Creation and Review")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_layout.addWidget(title)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        left_panel = self.create_configuration_panel()
        splitter.addWidget(left_panel)
        
        right_panel = self.create_preview_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([SPLITTER_LEFT_SIZE, SPLITTER_RIGHT_SIZE])
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        bottom_panel = self.create_actions_panel()
        main_layout.addWidget(bottom_panel)
    
    def create_configuration_panel(self) -> QWidget:
        """Create the configuration panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
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
        self.preview_tabs = QTabWidget()
        self.pr_preview_edit = QTextEdit()
        self.pr_preview_edit.setPlaceholderText("PR preview will appear here...")
        self.preview_tabs.addTab(self.pr_preview_edit, "PR Preview")
        self.log_output_edit = QTextEdit()
        self.log_output_edit.setReadOnly(True)
        self.preview_tabs.addTab(self.log_output_edit, "Log Output")
        layout.addWidget(self.preview_tabs)
        return panel
    
    def create_actions_panel(self) -> QWidget:
        """Create the actions panel."""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.addStretch()
        self.preview_pr_btn = QPushButton("Preview PR")
        self.create_pr_btn = QPushButton("Create PR")
        layout.addWidget(self.preview_pr_btn)
        layout.addWidget(self.create_pr_btn)
        layout.addStretch()
        return panel
    
    def setup_connections(self):
        """Setup signal-slot connections."""
        self.add_scan_files_btn.clicked.connect(self.add_scan_files)
        self.clear_scan_files_btn.clicked.connect(self.clear_scan_files)
        self.preview_pr_btn.clicked.connect(self.preview_pr)
        self.create_pr_btn.clicked.connect(self.create_pr)

    def add_scan_files(self):
        """Add scan result files."""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Scan Files", "", "JSON Files (*.json)")
        if files:
            self.scan_files_list.addItems(files)

    def clear_scan_files(self):
        self.scan_files_list.clear()

    def get_config(self) -> Dict[str, Any]:
        return {
            "dry_run": self.dry_run_check.isChecked(),
        }

    def preview_pr(self):
        if not self.get_scan_files():
            QMessageBox.warning(self, "No Scan Files", "Please add scan files first.")
            return
        
        config = self.get_config()
        config['dry_run'] = True
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        future = self.executor.submit(
            pr_creation_backend,
            self.get_scan_files(),
            config,
            callback=self.show_preview,
            error_callback=self.show_error
        )
        future.add_done_callback(self._on_preview_complete)

    def create_pr(self):
        if not self.get_scan_files():
            QMessageBox.warning(self, "No Scan Files", "Please add scan files first.")
            return

        config = self.get_config()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        future = self.executor.submit(
            pr_creation_backend,
            self.get_scan_files(),
            config,
            callback=self.show_pr_result,
            error_callback=self.show_error
        )
        future.add_done_callback(self._on_pr_creation_complete)

    def _on_preview_complete(self, future):
        def update_ui():
            try:
                result = future.result()
                self.show_preview(result)
            except Exception as e:
                self.show_error(f"Preview failed: {e}")
        QTimer.singleShot(0, update_ui)

    def _on_pr_creation_complete(self, future):
        def update_ui():
            try:
                result = future.result()
                self.show_pr_result(result)
            except Exception as e:
                self.show_error(f"PR creation failed: {e}")
        QTimer.singleShot(0, update_ui)

    def show_preview(self, result: Optional[Dict[str, Any]]):
        self.progress_bar.setVisible(False)
        if result and result.get('success'):
            self.pr_preview_edit.setText(result.get('description', 'Preview not available.'))
            self.log_output_edit.append("PR preview generated successfully.")
        else:
            self.show_error("Failed to generate PR preview.")

    def show_pr_result(self, result: Optional[Dict[str, Any]]):
        self.progress_bar.setVisible(False)
        if result and result.get('success'):
            QMessageBox.information(self, "PR Created", f"PR created successfully!\nURL: {result.get('pr_url', 'N/A')}")
            self.pr_preview_edit.setText(result.get('description', ''))
        else:
            self.show_error(f"Failed to create PR: {result.get('error', 'Unknown error') if result else 'Worker cancelled or failed'}")

    def show_error(self, error: str):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Worker Error", error)
        self.log_output_edit.append(f"ERROR: {error}")

    def get_scan_files(self) -> List[str]:
        return [self.scan_files_list.item(i).text() for i in range(self.scan_files_list.count())]

    @pyqtSlot(str, int, int, str)
    def update_progress(self, worker_id: str, current: int, total: int, message: str):
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        self.log_output_edit.append(f"Progress: {message}")

    @pyqtSlot(object)
    def on_pr_fetch_complete(self, pr_data):
        try:
            _ = self.isVisible()
        except RuntimeError:
            return # Widget is deleted

        self.progress_bar.hide()
        if pr_data:
            self.pr_details_text.setPlainText(pr_data)
        else:
            QMessageBox.warning(self, "Error", "Failed to fetch PR details.")

    @pyqtSlot(object)
    def on_summary_complete(self, summary_data):
        try:
            _ = self.isVisible()
        except RuntimeError:
            return # Widget is deleted
            
        self.progress_bar.hide()
        if summary_data and "summary" in summary_data:
            self.summary_text.setPlainText(summary_data["summary"])
        else:
            QMessageBox.warning(self, "Error", "Failed to generate summary.")

def setup_pr_tab(parent_widget: QWidget, main_window: QWidget) -> QWidget:
    """Setup the PR creation tab."""
    tab = PRCreationTab(parent_widget)
    # Global signal connections are now managed within the tab itself.
    return tab 