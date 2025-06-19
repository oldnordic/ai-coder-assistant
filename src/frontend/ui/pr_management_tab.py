"""
PR Management Tab

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
PR Management Tab - UI for managing PR automation with JIRA and ServiceNow integration.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QComboBox, QCheckBox, QListWidget,
    QListWidgetItem, QMessageBox, QFormLayout, QSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QFrame, QProgressBar,
    QApplication, QFileDialog, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon

from backend.services.pr_automation import ServiceConfig, PRTemplate, PRRequest, PRResult


class ServiceConfigDialog(QDialog):
    """Dialog for configuring JIRA/ServiceNow services."""
    
    def __init__(self, parent=None, service_config: Optional[ServiceConfig] = None):
        super().__init__(parent)
        self.service_config = service_config
        self.setup_ui()
        if service_config:
            self.load_config(service_config)
    
    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Service Configuration")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Service type selection
        type_group = QGroupBox("Service Type")
        type_layout = QFormLayout(type_group)
        
        self.service_type_combo = QComboBox()
        self.service_type_combo.addItems(["JIRA", "ServiceNow"])
        self.service_type_combo.currentTextChanged.connect(self.on_service_type_changed)
        type_layout.addRow("Service Type:", self.service_type_combo)
        
        layout.addWidget(type_group)
        
        # Service configuration
        self.config_group = QGroupBox("Service Configuration")
        self.config_layout = QFormLayout(self.config_group)
        
        self.name_edit = QLineEdit()
        self.base_url_edit = QLineEdit()
        self.username_edit = QLineEdit()
        self.api_token_edit = QLineEdit()
        self.api_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.project_key_edit = QLineEdit()
        self.enabled_checkbox = QCheckBox("Enabled")
        self.enabled_checkbox.setChecked(True)
        
        self.config_layout.addRow("Service Name:", self.name_edit)
        self.config_layout.addRow("Base URL:", self.base_url_edit)
        self.config_layout.addRow("Username:", self.username_edit)
        self.config_layout.addRow("API Token:", self.api_token_edit)
        self.config_layout.addRow("Project Key (JIRA):", self.project_key_edit)
        self.config_layout.addRow("", self.enabled_checkbox)
        
        layout.addWidget(self.config_group)
        
        # Test connection button
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        layout.addWidget(self.test_button)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.on_service_type_changed("JIRA")
    
    def on_service_type_changed(self, service_type: str):
        """Handle service type change."""
        if service_type == "JIRA":
            self.project_key_edit.setVisible(True)
            self.config_layout.labelForField(self.project_key_edit).setText("Project Key (JIRA):")
        else:
            self.project_key_edit.setVisible(False)
    
    def test_connection(self):
        """Test the service connection."""
        # This would be implemented with actual API calls
        QMessageBox.information(self, "Test Connection", "Connection test would be implemented here.")
    
    def load_config(self, config: ServiceConfig):
        """Load existing configuration."""
        if config.service_type == "jira":
            self.service_type_combo.setCurrentText("JIRA")
        else:
            self.service_type_combo.setCurrentText("ServiceNow")
        
        self.name_edit.setText(config.name)
        self.base_url_edit.setText(config.base_url)
        self.username_edit.setText(config.username)
        self.api_token_edit.setText(config.api_token)
        self.project_key_edit.setText(config.project_key or "")
        self.enabled_checkbox.setChecked(config.is_enabled)
    
    def get_config(self) -> ServiceConfig:
        """Get the configuration from the dialog."""
        service_type = self.service_type_combo.currentText().lower()
        
        return ServiceConfig(
            service_type=service_type,
            name=self.name_edit.text(),
            base_url=self.base_url_edit.text(),
            username=self.username_edit.text(),
            api_token=self.api_token_edit.text(),
            project_key=self.project_key_edit.text() if service_type == "jira" else None,
            is_enabled=self.enabled_checkbox.isChecked()
        )


class PRTemplateDialog(QDialog):
    """Dialog for creating/editing PR templates."""
    
    def __init__(self, parent=None, template: Optional[PRTemplate] = None):
        super().__init__(parent)
        self.template = template
        self.setup_ui()
        if template:
            self.load_template(template)
    
    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("PR Template")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Template configuration
        config_group = QGroupBox("Template Configuration")
        config_layout = QFormLayout(config_group)
        
        self.name_edit = QLineEdit()
        self.branch_prefix_edit = QLineEdit()
        self.branch_prefix_edit.setText("feature/")
        self.auto_assign_checkbox = QCheckBox("Auto Assign")
        self.auto_assign_checkbox.setChecked(True)
        self.is_default_checkbox = QCheckBox("Default Template")
        
        config_layout.addRow("Template Name:", self.name_edit)
        config_layout.addRow("Branch Prefix:", self.branch_prefix_edit)
        config_layout.addRow("", self.auto_assign_checkbox)
        config_layout.addRow("", self.is_default_checkbox)
        
        layout.addWidget(config_group)
        
        # Title template
        title_group = QGroupBox("Title Template")
        title_layout = QVBoxLayout(title_group)
        
        self.title_template_edit = QTextEdit()
        self.title_template_edit.setMaximumHeight(80)
        self.title_template_edit.setPlaceholderText("Available variables: {title}, {jira_ticket}, {servicenow_ticket}")
        title_layout.addWidget(self.title_template_edit)
        
        layout.addWidget(title_group)
        
        # Body template
        body_group = QGroupBox("Body Template")
        body_layout = QVBoxLayout(body_group)
        
        self.body_template_edit = QTextEdit()
        self.body_template_edit.setPlaceholderText("Available variables: {description}, {jira_ticket}, {servicenow_ticket}, {branch_name}, {base_branch}")
        body_layout.addWidget(self.body_template_edit)
        
        layout.addWidget(body_group)
        
        # Labels and reviewers
        extras_group = QGroupBox("Labels & Reviewers")
        extras_layout = QFormLayout(extras_group)
        
        self.labels_edit = QLineEdit()
        self.labels_edit.setPlaceholderText("comma-separated labels")
        self.reviewers_edit = QLineEdit()
        self.reviewers_edit.setPlaceholderText("comma-separated reviewers")
        
        extras_layout.addRow("Labels:", self.labels_edit)
        extras_layout.addRow("Reviewers:", self.reviewers_edit)
        
        layout.addWidget(extras_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_template(self, template: PRTemplate):
        """Load existing template."""
        self.name_edit.setText(template.name)
        self.branch_prefix_edit.setText(template.branch_prefix)
        self.auto_assign_checkbox.setChecked(template.auto_assign)
        self.is_default_checkbox.setChecked(template.is_default)
        self.title_template_edit.setPlainText(template.title_template)
        self.body_template_edit.setPlainText(template.body_template)
        self.labels_edit.setText(",".join(template.labels))
        self.reviewers_edit.setText(",".join(template.reviewers))
    
    def get_template(self) -> PRTemplate:
        """Get the template from the dialog."""
        labels = [label.strip() for label in self.labels_edit.text().split(",") if label.strip()]
        reviewers = [reviewer.strip() for reviewer in self.reviewers_edit.text().split(",") if reviewer.strip()]
        
        return PRTemplate(
            name=self.name_edit.text(),
            title_template=self.title_template_edit.toPlainText(),
            body_template=self.body_template_edit.toPlainText(),
            branch_prefix=self.branch_prefix_edit.text(),
            auto_assign=self.auto_assign_checkbox.isChecked(),
            labels=labels,
            reviewers=reviewers,
            is_default=self.is_default_checkbox.isChecked()
        )


class PRCreationWidget(QWidget):
    """Widget for creating PRs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        
        # PR creation form
        form_group = QGroupBox("Create Pull Request")
        form_layout = QFormLayout(form_group)
        
        self.title_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        
        self.template_combo = QComboBox()
        self.base_branch_edit = QLineEdit()
        self.base_branch_edit.setText("main")
        
        self.auto_create_tickets_checkbox = QCheckBox("Auto-create tickets")
        self.auto_create_tickets_checkbox.setChecked(True)
        
        self.jira_ticket_edit = QLineEdit()
        self.jira_ticket_edit.setPlaceholderText("Leave empty to auto-create")
        self.servicenow_ticket_edit = QLineEdit()
        self.servicenow_ticket_edit.setPlaceholderText("Leave empty to auto-create")
        
        self.labels_edit = QLineEdit()
        self.labels_edit.setPlaceholderText("comma-separated labels")
        self.reviewers_edit = QLineEdit()
        self.reviewers_edit.setPlaceholderText("comma-separated reviewers")
        
        form_layout.addRow("Title:", self.title_edit)
        form_layout.addRow("Description:", self.description_edit)
        form_layout.addRow("Template:", self.template_combo)
        form_layout.addRow("Base Branch:", self.base_branch_edit)
        form_layout.addRow("", self.auto_create_tickets_checkbox)
        form_layout.addRow("JIRA Ticket:", self.jira_ticket_edit)
        form_layout.addRow("ServiceNow Ticket:", self.servicenow_ticket_edit)
        form_layout.addRow("Labels:", self.labels_edit)
        form_layout.addRow("Reviewers:", self.reviewers_edit)
        
        layout.addWidget(form_group)
        
        # Create PR button
        self.create_button = QPushButton("Create Pull Request")
        self.create_button.clicked.connect(self.create_pr)
        layout.addWidget(self.create_button)
        
        # Status
        self.status_label = QLabel("Ready to create PR")
        layout.addWidget(self.status_label)
    
    def set_templates(self, templates: List[PRTemplate]):
        """Set available templates."""
        self.template_combo.clear()
        for template in templates:
            self.template_combo.addItem(template.name)
    
    def create_pr(self):
        """Create a PR."""
        # This would be implemented with actual PR creation
        QMessageBox.information(self, "Create PR", "PR creation would be implemented here.")


class PRManagementTab(QWidget):
    """Main PR management tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup the tab UI."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Services tab
        self.services_tab = self.create_services_tab()
        self.tab_widget.addTab(self.services_tab, "Services")
        
        # Templates tab
        self.templates_tab = self.create_templates_tab()
        self.tab_widget.addTab(self.templates_tab, "PR Templates")
        
        # Create PR tab
        self.create_pr_tab = self.create_pr_creation_tab()
        self.tab_widget.addTab(self.create_pr_tab, "Create PR")
        
        layout.addWidget(self.tab_widget)
    
    def create_services_tab(self) -> QWidget:
        """Create the services configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Services list
        services_group = QGroupBox("Configured Services")
        services_layout = QVBoxLayout(services_group)
        
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(5)
        self.services_table.setHorizontalHeaderLabels(["Name", "Type", "URL", "Status", "Actions"])
        self.services_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        services_layout.addWidget(self.services_table)
        
        # Service buttons
        buttons_layout = QHBoxLayout()
        
        self.add_service_button = QPushButton("Add Service")
        self.add_service_button.clicked.connect(self.add_service)
        
        self.edit_service_button = QPushButton("Edit Service")
        self.edit_service_button.clicked.connect(self.edit_service)
        
        self.remove_service_button = QPushButton("Remove Service")
        self.remove_service_button.clicked.connect(self.remove_service)
        
        self.test_service_button = QPushButton("Test Connection")
        self.test_service_button.clicked.connect(self.test_service)
        
        buttons_layout.addWidget(self.add_service_button)
        buttons_layout.addWidget(self.edit_service_button)
        buttons_layout.addWidget(self.remove_service_button)
        buttons_layout.addWidget(self.test_service_button)
        buttons_layout.addStretch()
        
        services_layout.addLayout(buttons_layout)
        layout.addWidget(services_group)
        
        return widget
    
    def create_templates_tab(self) -> QWidget:
        """Create the PR templates tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Templates list
        templates_group = QGroupBox("PR Templates")
        templates_layout = QVBoxLayout(templates_group)
        
        self.templates_list = QListWidget()
        templates_layout.addWidget(self.templates_list)
        
        # Template buttons
        buttons_layout = QHBoxLayout()
        
        self.add_template_button = QPushButton("Add Template")
        self.add_template_button.clicked.connect(self.add_template)
        
        self.edit_template_button = QPushButton("Edit Template")
        self.edit_template_button.clicked.connect(self.edit_template)
        
        self.remove_template_button = QPushButton("Remove Template")
        self.remove_template_button.clicked.connect(self.remove_template)
        
        self.set_default_button = QPushButton("Set as Default")
        self.set_default_button.clicked.connect(self.set_default_template)
        
        buttons_layout.addWidget(self.add_template_button)
        buttons_layout.addWidget(self.edit_template_button)
        buttons_layout.addWidget(self.remove_template_button)
        buttons_layout.addWidget(self.set_default_button)
        buttons_layout.addStretch()
        
        templates_layout.addLayout(buttons_layout)
        layout.addWidget(templates_group)
        
        return widget
    
    def create_pr_creation_tab(self) -> QWidget:
        """Create the PR creation tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Repository selection
        repo_group = QGroupBox("Repository")
        repo_layout = QHBoxLayout(repo_group)
        
        self.repo_path_edit = QLineEdit()
        self.repo_path_edit.setPlaceholderText("Path to git repository")
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_repository)
        
        repo_layout.addWidget(self.repo_path_edit)
        repo_layout.addWidget(self.browse_button)
        
        layout.addWidget(repo_group)
        
        # PR creation widget
        self.pr_creation_widget = PRCreationWidget()
        layout.addWidget(self.pr_creation_widget)
        
        return widget
    
    def load_data(self):
        """Load services and templates data."""
        # This would load from the backend
        self.refresh_services()
        self.refresh_templates()
    
    def refresh_services(self):
        """Refresh the services table."""
        # This would load from the backend
        self.services_table.setRowCount(0)
        # Add sample data for now
        self.add_service_row("JIRA-Prod", "JIRA", "https://company.atlassian.net", "Connected")
        self.add_service_row("ServiceNow-Dev", "ServiceNow", "https://company.service-now.com", "Disconnected")
    
    def add_service_row(self, name: str, service_type: str, url: str, status: str):
        """Add a row to the services table."""
        row = self.services_table.rowCount()
        self.services_table.insertRow(row)
        
        self.services_table.setItem(row, 0, QTableWidgetItem(name))
        self.services_table.setItem(row, 1, QTableWidgetItem(service_type))
        self.services_table.setItem(row, 2, QTableWidgetItem(url))
        self.services_table.setItem(row, 3, QTableWidgetItem(status))
        
        # Add action buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        
        test_btn = QPushButton("Test")
        test_btn.clicked.connect(lambda: self.test_service_by_name(name))
        actions_layout.addWidget(test_btn)
        
        self.services_table.setCellWidget(row, 4, actions_widget)
    
    def refresh_templates(self):
        """Refresh the templates list."""
        # This would load from the backend
        self.templates_list.clear()
        # Add sample data for now
        self.templates_list.addItem("Feature Template")
        self.templates_list.addItem("Bug Fix Template")
        self.templates_list.addItem("Hotfix Template")
    
    def add_service(self):
        """Add a new service."""
        dialog = ServiceConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            # This would save to the backend
            self.refresh_services()
    
    def edit_service(self):
        """Edit the selected service."""
        current_row = self.services_table.currentRow()
        if current_row >= 0:
            service_name = self.services_table.item(current_row, 0).text()
            # This would load the service config and show dialog
            QMessageBox.information(self, "Edit Service", f"Edit service: {service_name}")
    
    def remove_service(self):
        """Remove the selected service."""
        current_row = self.services_table.currentRow()
        if current_row >= 0:
            service_name = self.services_table.item(current_row, 0).text()
            reply = QMessageBox.question(self, "Remove Service", 
                                       f"Are you sure you want to remove {service_name}?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                # This would remove from the backend
                self.refresh_services()
    
    def test_service(self):
        """Test the selected service."""
        current_row = self.services_table.currentRow()
        if current_row >= 0:
            service_name = self.services_table.item(current_row, 0).text()
            self.test_service_by_name(service_name)
    
    def test_service_by_name(self, service_name: str):
        """Test a service by name."""
        # This would test the service connection
        QMessageBox.information(self, "Test Connection", f"Testing connection to {service_name}")
    
    def add_template(self):
        """Add a new PR template."""
        dialog = PRTemplateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            template = dialog.get_template()
            # This would save to the backend
            self.refresh_templates()
    
    def edit_template(self):
        """Edit the selected template."""
        current_item = self.templates_list.currentItem()
        if current_item:
            template_name = current_item.text()
            # This would load the template and show dialog
            QMessageBox.information(self, "Edit Template", f"Edit template: {template_name}")
    
    def remove_template(self):
        """Remove the selected template."""
        current_item = self.templates_list.currentItem()
        if current_item:
            template_name = current_item.text()
            reply = QMessageBox.question(self, "Remove Template", 
                                       f"Are you sure you want to remove {template_name}?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                # This would remove from the backend
                self.refresh_templates()
    
    def set_default_template(self):
        """Set the selected template as default."""
        current_item = self.templates_list.currentItem()
        if current_item:
            template_name = current_item.text()
            # This would set as default in the backend
            QMessageBox.information(self, "Set Default", f"Set {template_name} as default template")
    
    def browse_repository(self):
        """Browse for a git repository."""
        directory = QFileDialog.getExistingDirectory(self, "Select Git Repository")
        if directory:
            self.repo_path_edit.setText(directory) 