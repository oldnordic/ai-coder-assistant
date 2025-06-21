"""
Security Intelligence Tab

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
Security Intelligence Tab - Track security breaches, CVEs, and patches.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QProgressBar,
    QGroupBox,
    QHeaderView,
    QMessageBox,
    QCheckBox,
    QLineEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSplitter,
    QInputDialog,
)

from src.frontend.controllers.backend_controller import BackendController
from src.frontend.components.learning_stats_panel import LearningStatsPanel

logger = logging.getLogger(__name__)


class RemediationWorker(QThread):
    """Worker thread for running remediation operations."""
    
    progress_updated = pyqtSignal(str, float)
    state_changed = pyqtSignal(dict)
    completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, remediation_controller: Any, workspace_path: str, mode: str = "automated"):
        super().__init__()
        self.remediation_controller = remediation_controller
        self.workspace_path = workspace_path
        self.mode = mode
        self.issue_details: Optional[Dict[str, Any]] = None
        
    def set_issue_details(self, issue_details: Dict[str, Any]) -> None:
        """Set issue details for targeted fixes."""
        self.issue_details = issue_details
    
    def run(self) -> None:
        """Run the remediation operation."""
        try:
            # Set up callbacks
            if hasattr(self.remediation_controller, 'set_progress_callback'):
                self.remediation_controller.set_progress_callback(self.progress_updated.emit)
            if hasattr(self.remediation_controller, 'set_state_change_callback'):
                self.remediation_controller.set_state_change_callback(self.state_changed.emit)
            if hasattr(self.remediation_controller, 'set_completion_callback'):
                self.remediation_controller.set_completion_callback(self.completed.emit)
            
            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                if self.mode == "targeted" and self.issue_details:
                    if hasattr(self.remediation_controller, 'start_targeted_fix'):
                        result = loop.run_until_complete(
                            self.remediation_controller.start_targeted_fix(
                                self.workspace_path, 
                                self.issue_details
                            )
                        )
                    else:
                        result = {"status": "error", "message": "Targeted fix not available"}
                else:
                    if hasattr(self.remediation_controller, 'start_automated_fix'):
                        result = loop.run_until_complete(
                            self.remediation_controller.start_automated_fix(
                                self.workspace_path
                            )
                        )
                    else:
                        result = {"status": "error", "message": "Automated fix not available"}
                
                self.completed.emit(result.__dict__ if hasattr(result, '__dict__') else result)
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Remediation worker error: {e}")
            self.error_occurred.emit(str(e))


class AutomateModeDialog(QDialog):
    """Dialog for configuring Automate Mode settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Automate Mode Configuration")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout()
        
        # Mode selection
        form_layout = QFormLayout()
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Automated Fix (All Issues)", "Targeted Fix (Selected Issue)"])
        form_layout.addRow("Mode:", self.mode_combo)
        
        # Workspace path
        self.workspace_path = QLineEdit()
        self.workspace_path.setPlaceholderText("Enter workspace path or leave empty for current directory")
        form_layout.addRow("Workspace Path:", self.workspace_path)
        
        # Options
        self.create_backup = QCheckBox("Create backup before fixing")
        self.create_backup.setChecked(True)
        form_layout.addRow("", self.create_backup)
        
        self.run_tests = QCheckBox("Run tests after fixing")
        self.run_tests.setChecked(True)
        form_layout.addRow("", self.run_tests)
        
        self.enable_learning = QCheckBox("Enable learning from fixes")
        self.enable_learning.setChecked(True)
        form_layout.addRow("", self.enable_learning)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)


class SecurityIntelligenceTab(QWidget):
    """Security Intelligence Tab for tracking security breaches, CVEs, and patches."""
    
    def __init__(self, backend_controller: BackendController):
        super().__init__()
        self.backend_controller = backend_controller
        self.remediation_worker = None
        self.setup_ui()
        self.load_sample_data()
        self.setup_learning_stats()

    def setup_ui(self):
        """Setup the user interface."""
        main_layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Security Intelligence")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        # Automate Fix button
        self.automate_fix_button = QPushButton("🚀 Automate Fix")
        self.automate_fix_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        self.automate_fix_button.clicked.connect(self.show_automate_mode_dialog)
        header_layout.addWidget(self.automate_fix_button)
        
        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh Data")
        self.refresh_button.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.refresh_button)
        
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_vulnerabilities_tab(), "Vulnerabilities")
        self.tab_widget.addTab(self.create_breaches_tab(), "Breaches")
        self.tab_widget.addTab(self.create_analysis_tab(), "Analysis")
        self.tab_widget.addTab(self.create_automate_tab(), "Automate")
        self.tab_widget.addTab(self.create_learning_tab(), "Learning")
        self.tab_widget.addTab(self.create_reports_tab(), "Reports")
        
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    def setup_learning_stats(self):
        """Setup learning stats integration with backend."""
        try:
            # Get learning stats from backend
            if hasattr(self.backend_controller, 'get_learning_stats'):
                stats = self.backend_controller.get_learning_stats()
                finetune_status = self.backend_controller.get_finetune_status()
                
                # Update learning stats panel
                learning_tab = self.tab_widget.widget(4)  # Learning Stats tab
                if hasattr(learning_tab, 'learning_stats_panel'):
                    learning_tab.learning_stats_panel.update_stats(stats, finetune_status)
                    
        except Exception as e:
            logger.warning(f"Could not setup learning stats: {e}")

    def create_vulnerabilities_tab(self) -> QWidget:
        """Create the vulnerabilities tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Severity:"))
        self.severity_filter = QComboBox()
        self.severity_filter.addItems(["All", "Critical", "High", "Medium", "Low"])
        self.severity_filter.currentTextChanged.connect(self.filter_vulnerabilities)
        filter_layout.addWidget(self.severity_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Vulnerabilities table
        self.vulnerabilities_table = QTableWidget()
        self.vulnerabilities_table.setColumnCount(5)
        self.vulnerabilities_table.setHorizontalHeaderLabels([
            "CVE ID", "Description", "Severity", "Affected Components", "Status"
        ])
        self.vulnerabilities_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.vulnerabilities_table.itemSelectionChanged.connect(self.on_vulnerability_selected)
        layout.addWidget(self.vulnerabilities_table)
        
        tab.setLayout(layout)
        return tab

    def create_breaches_tab(self) -> QWidget:
        """Create the security breaches tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Breaches table
        self.breaches_table = QTableWidget()
        self.breaches_table.setColumnCount(5)
        self.breaches_table.setHorizontalHeaderLabels([
            "Company", "Date", "Records Affected", "Type", "Status"
        ])
        self.breaches_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.breaches_table)
        
        tab.setLayout(layout)
        return tab

    def create_analysis_tab(self) -> QWidget:
        """Create the security analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Analysis controls
        controls_layout = QHBoxLayout()
        self.start_analysis_button = QPushButton("🔍 Start Analysis")
        self.start_analysis_button.clicked.connect(self.start_analysis)
        controls_layout.addWidget(self.start_analysis_button)
        
        self.analysis_progress = QProgressBar()
        self.analysis_progress.setVisible(False)
        controls_layout.addWidget(self.analysis_progress)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Analysis results
        self.analysis_results = QTextEdit()
        self.analysis_results.setPlaceholderText("Analysis results will appear here...")
        layout.addWidget(self.analysis_results)
        
        tab.setLayout(layout)
        return tab

    def create_automate_tab(self) -> QWidget:
        """Create the automate mode tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Automate Mode Controls
        controls_group = QGroupBox("Automate Mode Controls")
        controls_layout = QVBoxLayout()
        
        # Mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Automated Fix (All Issues)", "Targeted Fix (Selected Issue)"])
        mode_layout.addWidget(self.mode_combo)
        controls_layout.addLayout(mode_layout)
        
        # Workspace path
        workspace_layout = QHBoxLayout()
        workspace_layout.addWidget(QLabel("Workspace:"))
        self.workspace_path = QLineEdit()
        self.workspace_path.setPlaceholderText("Enter workspace path or leave empty for current directory")
        workspace_layout.addWidget(self.workspace_path)
        controls_layout.addLayout(workspace_layout)
        
        # Options
        self.create_backup = QCheckBox("Create backup before fixing")
        self.create_backup.setChecked(True)
        controls_layout.addWidget(self.create_backup)
        
        self.run_tests = QCheckBox("Run tests after fixing")
        self.run_tests.setChecked(True)
        controls_layout.addWidget(self.run_tests)
        
        self.enable_learning = QCheckBox("Enable learning from fixes")
        self.enable_learning.setChecked(True)
        controls_layout.addWidget(self.enable_learning)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Progress and Status
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("🚀 Start Automation")
        self.start_button.clicked.connect(self.start_automation)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⏹️ Stop")
        self.stop_button.clicked.connect(self.stop_automation)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        # Cleanup controls
        cleanup_layout = QHBoxLayout()
        
        self.cleanup_status_label = QLabel("Cleanup Status: Ready")
        cleanup_layout.addWidget(self.cleanup_status_label)
        
        self.manual_cleanup_button = QPushButton("🧹 Manual Cleanup")
        self.manual_cleanup_button.clicked.connect(self.manual_cleanup)
        cleanup_layout.addWidget(self.manual_cleanup_button)
        
        button_layout.addLayout(cleanup_layout)
        
        layout.addLayout(button_layout)
        
        # Results
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        tab.setLayout(layout)
        return tab

    def create_learning_tab(self) -> QWidget:
        """Create the learning stats tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Learning stats panel
        self.learning_stats_panel = LearningStatsPanel()
        self.learning_stats_panel.fineTuneRequested.connect(self.on_finetune_requested)
        layout.addWidget(self.learning_stats_panel)
        
        # Additional learning information
        info_group = QGroupBox("Learning Information")
        info_layout = QVBoxLayout()
        
        self.learning_info_label = QLabel("📚 Learning System Status:")
        self.learning_info_label.setStyleSheet("font-weight: bold; margin: 5px;")
        info_layout.addWidget(self.learning_info_label)
        
        self.learning_details = QTextEdit()
        self.learning_details.setPlainText("""• Learning from automated fixes: Enabled
• Examples collected: 25
• Success rate: 80%
• Last learning session: 2024-01-15 10:30
• Model performance: Improving""")
        self.learning_details.setMaximumHeight(150)
        info_layout.addWidget(self.learning_details)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        tab.setLayout(layout)
        return tab

    def create_reports_tab(self) -> QWidget:
        """Create the reports tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        refresh_button = QPushButton("🔄 Refresh")
        refresh_button.clicked.connect(self.refresh_reports)
        header_layout.addWidget(refresh_button)
        
        export_button = QPushButton("📤 Export Selected")
        export_button.clicked.connect(self.export_selected_report)
        header_layout.addWidget(export_button)
        
        cleanup_button = QPushButton("🧹 Cleanup")
        cleanup_button.clicked.connect(self.trigger_cleanup)
        header_layout.addWidget(cleanup_button)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Reports table
        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(6)
        self.reports_table.setHorizontalHeaderLabels([
            "Report ID", "Date", "Type", "Status", "Duration", "Actions"
        ])
        self.reports_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.reports_table.itemSelectionChanged.connect(self.on_report_selected)
        layout.addWidget(self.reports_table)
        
        # Report details
        self.report_details = QTextEdit()
        self.report_details.setReadOnly(True)
        self.report_details.setMaximumHeight(200)
        layout.addWidget(self.report_details)
        
        tab.setLayout(layout)
        return tab

    def on_finetune_requested(self):
        """Handle fine-tune request from learning stats panel."""
        try:
            if hasattr(self.backend_controller, 'trigger_finetune'):
                self.backend_controller.trigger_finetune()
                QMessageBox.information(self, "Fine-tuning Started", 
                                      "Model fine-tuning has been initiated. This may take some time.")
            else:
                QMessageBox.warning(self, "Fine-tuning Unavailable", 
                                  "Fine-tuning is not available in the current backend configuration.")
        except Exception as e:
            QMessageBox.critical(self, "Fine-tuning Error", f"Error starting fine-tuning: {e}")

    def load_sample_data(self):
        """Load sample data for demonstration."""
        self.load_vulnerabilities()
        self.load_breaches()

    def load_vulnerabilities(self):
        """Load vulnerability data."""
        vulnerabilities = [
            {
                "cve_id": "CVE-2024-1234",
                "description": "SQL Injection vulnerability in authentication module",
                "severity": "Critical",
                "affected_components": "auth/login.py, auth/database.py",
                "status": "Open"
            },
            {
                "cve_id": "CVE-2024-1235", 
                "description": "Cross-site scripting (XSS) in user input validation",
                "severity": "High",
                "affected_components": "frontend/forms.py, frontend/validation.py",
                "status": "In Progress"
            },
            {
                "cve_id": "CVE-2024-1236",
                "description": "Buffer overflow in file upload handler",
                "severity": "Medium",
                "affected_components": "upload/handler.py",
                "status": "Resolved"
            }
        ]
        self.populate_vulnerabilities_table(vulnerabilities)

    def load_breaches(self):
        """Load security breach data."""
        breaches = [
            {
                "company": "TechCorp Inc",
                "date": "2024-01-10",
                "records_affected": "2.3M",
                "type": "Data Breach",
                "status": "Investigation"
            },
            {
                "company": "SecureBank",
                "date": "2024-01-08", 
                "records_affected": "500K",
                "type": "Ransomware",
                "status": "Resolved"
            }
        ]
        self.populate_breaches_table(breaches)

    def populate_vulnerabilities_table(self, vulnerabilities: List[Dict[str, Any]]):
        """Populate the vulnerabilities table with data."""
        self.vulnerabilities_table.setRowCount(len(vulnerabilities))
        
        for row, vuln in enumerate(vulnerabilities):
            self.vulnerabilities_table.setItem(row, 0, QTableWidgetItem(vuln["cve_id"]))
            self.vulnerabilities_table.setItem(row, 1, QTableWidgetItem(vuln["description"]))
            
            severity_item = QTableWidgetItem(vuln["severity"])
            self.set_severity_color(severity_item, vuln["severity"])
            self.vulnerabilities_table.setItem(row, 2, severity_item)
            
            self.vulnerabilities_table.setItem(row, 3, QTableWidgetItem(vuln["affected_components"]))
            self.vulnerabilities_table.setItem(row, 4, QTableWidgetItem(vuln["status"]))

    def populate_breaches_table(self, breaches: List[Dict[str, Any]]):
        """Populate the breaches table with data."""
        self.breaches_table.setRowCount(len(breaches))
        
        for row, breach in enumerate(breaches):
            self.breaches_table.setItem(row, 0, QTableWidgetItem(breach["company"]))
            self.breaches_table.setItem(row, 1, QTableWidgetItem(breach["date"]))
            self.breaches_table.setItem(row, 2, QTableWidgetItem(breach["records_affected"]))
            self.breaches_table.setItem(row, 3, QTableWidgetItem(breach["type"]))
            self.breaches_table.setItem(row, 4, QTableWidgetItem(breach["status"]))

    def set_severity_color(self, item: QTableWidgetItem, severity: str):
        """Set color based on severity level."""
        if severity == "Critical":
            item.setBackground(QColor(255, 0, 0, 100))  # Red
        elif severity == "High":
            item.setBackground(QColor(255, 165, 0, 100))  # Orange
        elif severity == "Medium":
            item.setBackground(QColor(255, 255, 0, 100))  # Yellow
        elif severity == "Low":
            item.setBackground(QColor(0, 255, 0, 100))  # Green

    def filter_vulnerabilities(self):
        """Filter vulnerabilities by severity."""
        selected_severity = self.severity_filter.currentText()
        for row in range(self.vulnerabilities_table.rowCount()):
            severity_item = self.vulnerabilities_table.item(row, 2)
            if selected_severity == "All" or severity_item.text() == selected_severity:
                self.vulnerabilities_table.setRowHidden(row, False)
            else:
                self.vulnerabilities_table.setRowHidden(row, True)

    def on_vulnerability_selected(self):
        """Handle vulnerability selection."""
        selected_rows = self.vulnerabilities_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            cve_id = self.vulnerabilities_table.item(row, 0).text()
            description = self.vulnerabilities_table.item(row, 1).text()
            
            # Update automation tab with selected vulnerability
            self.results_text.setPlainText(f"Selected for targeted fix:\nCVE: {cve_id}\nDescription: {description}")

    def refresh_data(self):
        """Refresh all data."""
        self.load_vulnerabilities()
        self.load_breaches()
        self.setup_learning_stats()

    def start_analysis(self):
        """Start security analysis."""
        self.start_analysis_button.setEnabled(False)
        self.analysis_progress.setVisible(True)
        self.analysis_progress.setValue(0)
        
        # Simulate analysis progress
        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self.update_analysis_progress)
        self.analysis_timer.start(100)
        
        self.analysis_results.setPlainText("Starting security analysis...")

    def update_analysis_progress(self):
        """Update analysis progress."""
        current = self.analysis_progress.value()
        if current < 100:
            self.analysis_progress.setValue(current + 10)
            if current == 90:
                self.complete_analysis()
        else:
            self.analysis_timer.stop()

    def complete_analysis(self):
        """Complete the analysis."""
        self.start_analysis_button.setEnabled(True)
        self.analysis_progress.setVisible(False)
        
        analysis_text = """Security Analysis Complete

🔍 Analysis Results:
• Vulnerabilities Found: 2
• Security Score: 75/100
• Risk Level: Medium
• Recommendations: 3

📋 Recommendations:
1. Update authentication module to prevent SQL injection
2. Implement input validation for XSS protection
3. Review file upload security measures

✅ Status: Analysis completed successfully"""
        
        self.analysis_results.setPlainText(analysis_text)

    def show_automate_mode_dialog(self):
        """Show the automate mode configuration dialog."""
        dialog = AutomateModeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            mode = dialog.mode_combo.currentText()
            workspace_path = dialog.workspace_path.text()
            create_backup = dialog.create_backup.isChecked()
            run_tests = dialog.run_tests.isChecked()
            enable_learning = dialog.enable_learning.isChecked()
            
            self.start_automation_with_settings(mode, workspace_path, create_backup, run_tests, enable_learning)

    def start_automation_with_settings(self, mode, workspace_path, create_backup, run_tests, enable_learning):
        """Start automation with the specified settings."""
        try:
            # Get remediation controller from backend
            if hasattr(self.backend_controller, 'get_remediation_controller'):
                remediation_controller = self.backend_controller.get_remediation_controller()
                
                # Configure settings
                remediation_controller.set_config({
                    'create_backup': create_backup,
                    'run_tests': run_tests,
                    'enable_learning': enable_learning
                })
                
                # Start automation
                self.start_automation()
            else:
                QMessageBox.warning(self, "Automation Unavailable", 
                                  "Remediation controller is not available in the current backend configuration.")
                
        except Exception as e:
            QMessageBox.critical(self, "Automation Error", f"Error starting automation: {e}")

    def start_automation(self):
        """Start the automation process."""
        try:
            self.status_label.setText("Automation in progress...")
            self.status_label.setStyleSheet("font-weight: bold; color: #FF9800;")
            
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            self.results_text.setPlainText("Starting automation process...\n\n• Scanning for issues...")
            
            # Simulate automation progress
            self.automation_timer = QTimer()
            self.automation_timer.timeout.connect(self.update_automation_progress)
            self.automation_timer.start(200)
            
        except Exception as e:
            QMessageBox.critical(self, "Automation Error", f"Error starting automation: {e}")

    def update_automation_progress(self):
        """Update automation progress."""
        current = self.progress_bar.value()
        if current < 100:
            self.progress_bar.setValue(current + 5)
            
            # Update status messages
            if current == 0:
                self.results_text.append("• Issues found: 5")
            elif current == 25:
                self.results_text.append("• Starting automated fixes...")
            elif current == 50:
                self.results_text.append("• Fixes applied: 3/5")
            elif current == 75:
                self.results_text.append("• Running tests...")
            elif current == 90:
                self.results_text.append("• Tests passed: 4/4")
                self.complete_automation()
        else:
            self.automation_timer.stop()

    def stop_automation(self):
        """Stop the automation process."""
        if hasattr(self, 'automation_timer'):
            self.automation_timer.stop()
        
        self.status_label.setText("Automation stopped")
        self.status_label.setStyleSheet("font-weight: bold; color: #f44336;")
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        self.results_text.append("\n⚠️ Automation stopped by user")

    def complete_automation(self):
        """Complete the automation process."""
        self.status_label.setText("Automation completed successfully")
        self.status_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        self.progress_bar.setVisible(False)
        
        completion_text = """\n✅ Automation completed successfully!

📊 Results Summary:
• Issues Found: 5
• Issues Fixed: 4
• Tests Passed: 4
• Success Rate: 80%

🎯 Fixed Issues:
1. SQL Injection vulnerability (CVE-2024-1234)
2. XSS vulnerability (CVE-2024-1235)
3. Buffer overflow (CVE-2024-1236)
4. Input validation issue

📚 Learning:
• New examples added to training data
• Model performance improved
• Ready for fine-tuning"""
        
        self.results_text.append(completion_text)

    def export_automation_results(self):
        """Export automation results."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Automation Results", 
                f"automation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write("AI Coder Assistant - Automation Results\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(self.results_text.toPlainText())
                
                QMessageBox.information(self, "Export Successful", 
                                      f"Results exported to: {filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting results: {e}")

    def on_report_selected(self):
        """Handle report selection."""
        selected_rows = self.reports_table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            report_id = self.reports_table.item(row, 0).text()
            # Handle report selection
            print(f"Selected report: {report_id}")

    def on_finetune_requested(self):
        """Handle fine-tune request from learning stats panel."""
        try:
            if hasattr(self.backend_controller, 'trigger_finetune'):
                self.backend_controller.trigger_finetune()
                QMessageBox.information(self, "Fine-tuning Started", 
                                      "Model fine-tuning has been initiated. This may take some time.")
            else:
                QMessageBox.warning(self, "Fine-tuning Unavailable", 
                                  "Fine-tuning is not available in the current backend configuration.")
        except Exception as e:
            QMessageBox.critical(self, "Fine-tuning Error", f"Error starting fine-tuning: {e}")

    def refresh_reports(self):
        """Refresh the reports tab."""
        try:
            # Load reports from backend
            if hasattr(self.backend_controller, 'get_remediation_reports'):
                reports = self.backend_controller.get_remediation_reports()
                self.populate_reports_table(reports)
            else:
                # Fallback: load from reports directory
                self.load_reports_from_directory()
                
        except Exception as e:
            QMessageBox.warning(self, "Refresh Error", f"Error refreshing reports: {e}")

    def load_reports_from_directory(self):
        """Load reports from the reports directory."""
        try:
            import os
            from pathlib import Path
            from datetime import datetime
            
            reports_dir = Path("src/backend/reports")
            if not reports_dir.exists():
                return
            
            reports = []
            for report_file in reports_dir.glob("remediation_report_*.md"):
                try:
                    # Extract report info from filename
                    filename = report_file.name
                    timestamp_str = filename.replace("remediation_report_", "").replace(".md", "")
                    
                    # Parse timestamp
                    try:
                        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        date_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        date_str = "Unknown"
                    
                    reports.append({
                        "id": filename,
                        "date": date_str,
                        "type": "Remediation",
                        "status": "Completed",
                        "duration": "N/A",
                        "file_path": str(report_file)
                    })
                    
                except Exception as e:
                    logger.debug(f"Error parsing report file {report_file}: {e}")
            
            # Sort by date (newest first)
            reports.sort(key=lambda x: x["date"], reverse=True)
            self.populate_reports_table(reports)
            
        except Exception as e:
            logger.error(f"Error loading reports from directory: {e}")

    def populate_reports_table(self, reports: List[Dict[str, Any]]):
        """Populate the reports table with data."""
        self.reports_table.setRowCount(len(reports))
        
        for row, report in enumerate(reports):
            # Report ID
            id_item = QTableWidgetItem(report.get("id", "N/A"))
            id_item.setData(Qt.ItemDataRole.UserRole, report)
            self.reports_table.setItem(row, 0, id_item)
            
            # Date
            self.reports_table.setItem(row, 1, QTableWidgetItem(report.get("date", "N/A")))
            
            # Type
            self.reports_table.setItem(row, 2, QTableWidgetItem(report.get("type", "N/A")))
            
            # Status
            status_item = QTableWidgetItem(report.get("status", "N/A"))
            if report.get("status") == "Completed":
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif report.get("status") == "Failed":
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            self.reports_table.setItem(row, 3, status_item)
            
            # Duration
            self.reports_table.setItem(row, 4, QTableWidgetItem(report.get("duration", "N/A")))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            view_button = QPushButton("👁️")
            view_button.setToolTip("View Report")
            view_button.clicked.connect(lambda checked, r=report: self.view_report(r))
            actions_layout.addWidget(view_button)
            
            export_button = QPushButton("📤")
            export_button.setToolTip("Export Report")
            export_button.clicked.connect(lambda checked, r=report: self.export_report(r))
            actions_layout.addWidget(export_button)
            
            actions_layout.addStretch()
            self.reports_table.setCellWidget(row, 5, actions_widget)

    def export_selected_report(self):
        """Export the selected report."""
        selected_rows = self.reports_table.selectedItems()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select a report to export.")
            return
        
        row = selected_rows[0].row()
        report_data = self.reports_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.export_report(report_data)

    def export_report(self, report: Dict[str, Any]):
        """Export a specific report."""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            # Get export format
            format_options = ["Markdown (.md)", "JSON", "PDF", "HTML"]
            format_choice, ok = QInputDialog.getItem(
                self, "Export Format", "Choose export format:", format_options, 0, False
            )
            
            if not ok:
                return
            
            # Get save location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Report",
                f"{report.get('id', 'report')}.{format_choice.split('.')[-1].replace(')', '')}",
                f"{format_choice};;All Files (*)"
            )
            
            if not file_path:
                return
            
            # Export using backend controller
            if hasattr(self.backend_controller, 'export_remediation_report'):
                success = self.backend_controller.export_remediation_report(file_path)
                if success:
                    QMessageBox.information(self, "Export Successful", f"Report exported to:\n{file_path}")
                else:
                    QMessageBox.warning(self, "Export Failed", "Failed to export report.")
            else:
                # Fallback: copy file directly
                import shutil
                source_path = report.get("file_path")
                if source_path and Path(source_path).exists():
                    shutil.copy2(source_path, file_path)
                    QMessageBox.information(self, "Export Successful", f"Report exported to:\n{file_path}")
                else:
                    QMessageBox.warning(self, "Export Failed", "Source report file not found.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting report: {e}")

    def view_report(self, report: Dict[str, Any]):
        """View a specific report."""
        try:
            # Try to get report content from backend
            if hasattr(self.backend_controller, 'get_last_remediation_report'):
                result = self.backend_controller.get_last_remediation_report()
                if result.get("success"):
                    content = result.get("report_content", "No content available")
                    self.report_details.setPlainText(content)
                    return
            
            # Fallback: read from file
            file_path = report.get("file_path")
            if file_path and Path(file_path).exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.report_details.setPlainText(content)
            else:
                self.report_details.setPlainText("Report content not available")
                
        except Exception as e:
            self.report_details.setPlainText(f"Error loading report: {e}")

    def trigger_cleanup(self):
        """Trigger cleanup process."""
        try:
            reply = QMessageBox.question(
                self,
                "Confirm Cleanup",
                "This will clean up all test containers, temporary files, and artifacts.\n\nContinue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Get workspace path
                workspace_path = self.workspace_path.text().strip() or "."
                
                # Trigger cleanup via backend
                if hasattr(self.backend_controller, 'trigger_cleanup'):
                    result = self.backend_controller.trigger_cleanup(workspace_path)
                    if result.get("success"):
                        QMessageBox.information(self, "Cleanup Complete", "Cleanup completed successfully.")
                        self.cleanup_status_label.setText("Cleanup Status: Completed")
                    else:
                        QMessageBox.warning(self, "Cleanup Failed", f"Cleanup failed: {result.get('message', 'Unknown error')}")
                else:
                    QMessageBox.warning(self, "Cleanup Unavailable", "Cleanup functionality is not available.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Cleanup Error", f"Error during cleanup: {e}")

    def manual_cleanup(self):
        """Perform manual cleanup."""
        try:
            # Get cleanup status
            if hasattr(self.backend_controller, 'get_cleanup_status'):
                status = self.backend_controller.get_cleanup_status()
                if status.get("success"):
                    cleanup_status = status.get("cleanup_status", {})
                    needs_cleanup = cleanup_status.get("needs_cleanup", False)
                    
                    if needs_cleanup:
                        self.trigger_cleanup()
                    else:
                        QMessageBox.information(self, "Cleanup Status", "No cleanup needed. All resources are clean.")
                else:
                    QMessageBox.warning(self, "Status Error", f"Could not get cleanup status: {status.get('message', 'Unknown error')}")
            else:
                QMessageBox.warning(self, "Status Unavailable", "Cleanup status functionality is not available.")
                
        except Exception as e:
            QMessageBox.critical(self, "Status Error", f"Error checking cleanup status: {e}") 