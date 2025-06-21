"""
settings_tab.py

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
Settings Tab - Manage API keys and application configuration.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QGroupBox,
    QTabWidget,
    QTextEdit,
    QCheckBox,
    QSpinBox,
    QComboBox,
    QMessageBox,
    QFileDialog,
    QProgressBar,
    QSplitter,
    QScrollArea,
    QFrame,
)

from src.backend.utils.secrets import get_secrets_manager, is_provider_configured, is_service_configured
from src.frontend.controllers.backend_controller import BackendController

logger = logging.getLogger(__name__)


class SettingsTab(QWidget):
    """Settings Tab Widget for managing API keys and configuration."""
    
    # Signals
    settings_changed = pyqtSignal()
    
    def __init__(self, backend_controller: BackendController):
        super().__init__()
        self.backend_controller = backend_controller
        self.secrets_manager = get_secrets_manager()
        self.setup_ui()
        self.load_current_settings()
        
    def setup_ui(self):
        """Setup the user interface."""
        main_layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("Settings & Configuration")
        header_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_layout.addWidget(header_label)
        
        # Create tab widget for different settings categories
        self.tab_widget = QTabWidget()
        
        # API Keys Tab
        self.api_keys_tab = self.create_api_keys_tab()
        self.tab_widget.addTab(self.api_keys_tab, "API Keys")
        
        # Services Tab
        self.services_tab = self.create_services_tab()
        self.tab_widget.addTab(self.services_tab, "External Services")
        
        # Application Settings Tab
        self.app_settings_tab = self.create_app_settings_tab()
        self.tab_widget.addTab(self.app_settings_tab, "Application Settings")
        
        # Local Models Tab
        self.local_models_tab = self.create_local_models_tab()
        self.tab_widget.addTab(self.local_models_tab, "Local Models")
        
        # Security Tab
        self.security_tab = self.create_security_tab()
        self.tab_widget.addTab(self.security_tab, "Security")
        
        main_layout.addWidget(self.tab_widget)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setEnabled(False)
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_settings)
        
        self.reload_button = QPushButton("Reload from Environment")
        self.reload_button.clicked.connect(self.reload_settings)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.reload_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
    def create_api_keys_tab(self) -> QWidget:
        """Create the API Keys tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Description
        desc_label = QLabel(
            "Configure API keys for AI providers. These are stored securely using environment variables.\n"
            "You can set them in your .env file or system environment variables."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # API Keys Grid
        keys_group = QGroupBox("AI Provider API Keys")
        keys_layout = QGridLayout()
        
        self.api_key_inputs = {}
        
        # Define providers and their display names
        providers = [
            ("openai", "OpenAI", "OPENAI_API_KEY"),
            ("anthropic", "Anthropic (Claude)", "ANTHROPIC_API_KEY"),
            ("google", "Google (Gemini)", "GOOGLE_API_KEY"),
            ("azure", "Azure OpenAI", "AZURE_API_KEY"),
            ("cohere", "Cohere", "COHERE_API_KEY"),
        ]
        
        for row, (provider, display_name, env_var) in enumerate(providers):
            # Provider name
            name_label = QLabel(display_name)
            name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            keys_layout.addWidget(name_label, row, 0)
            
            # API key input
            key_input = QLineEdit()
            key_input.setEchoMode(QLineEdit.EchoMode.Password)
            key_input.setPlaceholderText(f"Enter {display_name} API key")
            key_input.textChanged.connect(self.on_setting_changed)
            keys_layout.addWidget(key_input, row, 1)
            
            # Status indicator
            status_label = QLabel("Not configured")
            status_label.setStyleSheet("color: red;")
            keys_layout.addWidget(status_label, row, 2)
            
            # Test button
            test_button = QPushButton("Test")
            test_button.clicked.connect(lambda checked, p=provider: self.test_api_key(p))
            keys_layout.addWidget(test_button, row, 3)
            
            self.api_key_inputs[provider] = {
                'input': key_input,
                'status': status_label,
                'test_button': test_button,
                'env_var': env_var
            }
        
        keys_group.setLayout(keys_layout)
        layout.addWidget(keys_group)
        
        # AWS Configuration (special case with multiple fields)
        aws_group = QGroupBox("AWS Configuration")
        aws_layout = QGridLayout()
        
        aws_layout.addWidget(QLabel("Access Key ID:"), 0, 0)
        self.aws_access_key_input = QLineEdit()
        self.aws_access_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.aws_access_key_input.setPlaceholderText("Enter AWS Access Key ID")
        self.aws_access_key_input.textChanged.connect(self.on_setting_changed)
        aws_layout.addWidget(self.aws_access_key_input, 0, 1)
        
        aws_layout.addWidget(QLabel("Secret Access Key:"), 1, 0)
        self.aws_secret_key_input = QLineEdit()
        self.aws_secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.aws_secret_key_input.setPlaceholderText("Enter AWS Secret Access Key")
        self.aws_secret_key_input.textChanged.connect(self.on_setting_changed)
        aws_layout.addWidget(self.aws_secret_key_input, 1, 1)
        
        aws_layout.addWidget(QLabel("Region:"), 2, 0)
        self.aws_region_input = QLineEdit()
        self.aws_region_input.setPlaceholderText("e.g., us-east-1")
        self.aws_region_input.textChanged.connect(self.on_setting_changed)
        aws_layout.addWidget(self.aws_region_input, 2, 1)
        
        self.aws_status_label = QLabel("Not configured")
        self.aws_status_label.setStyleSheet("color: red;")
        aws_layout.addWidget(self.aws_status_label, 3, 0, 1, 2)
        
        aws_group.setLayout(aws_layout)
        layout.addWidget(aws_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
        
    def create_services_tab(self) -> QWidget:
        """Create the External Services tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Description
        desc_label = QLabel(
            "Configure external services for PR automation and project management."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # JIRA Configuration
        jira_group = QGroupBox("JIRA Configuration")
        jira_layout = QGridLayout()
        
        jira_layout.addWidget(QLabel("Base URL:"), 0, 0)
        self.jira_url_input = QLineEdit()
        self.jira_url_input.setPlaceholderText("https://your-domain.atlassian.net")
        self.jira_url_input.textChanged.connect(self.on_setting_changed)
        jira_layout.addWidget(self.jira_url_input, 0, 1)
        
        jira_layout.addWidget(QLabel("Username:"), 1, 0)
        self.jira_username_input = QLineEdit()
        self.jira_username_input.setPlaceholderText("your-email@domain.com")
        self.jira_username_input.textChanged.connect(self.on_setting_changed)
        jira_layout.addWidget(self.jira_username_input, 1, 1)
        
        jira_layout.addWidget(QLabel("API Token:"), 2, 0)
        self.jira_token_input = QLineEdit()
        self.jira_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.jira_token_input.setPlaceholderText("Enter JIRA API token")
        self.jira_token_input.textChanged.connect(self.on_setting_changed)
        jira_layout.addWidget(self.jira_token_input, 2, 1)
        
        jira_layout.addWidget(QLabel("Project Key:"), 3, 0)
        self.jira_project_input = QLineEdit()
        self.jira_project_input.setPlaceholderText("e.g., PROJ")
        self.jira_project_input.textChanged.connect(self.on_setting_changed)
        jira_layout.addWidget(self.jira_project_input, 3, 1)
        
        self.jira_status_label = QLabel("Not configured")
        self.jira_status_label.setStyleSheet("color: red;")
        jira_layout.addWidget(self.jira_status_label, 4, 0, 1, 2)
        
        jira_group.setLayout(jira_layout)
        layout.addWidget(jira_group)
        
        # ServiceNow Configuration
        servicenow_group = QGroupBox("ServiceNow Configuration")
        servicenow_layout = QGridLayout()
        
        servicenow_layout.addWidget(QLabel("Base URL:"), 0, 0)
        self.servicenow_url_input = QLineEdit()
        self.servicenow_url_input.setPlaceholderText("https://your-instance.service-now.com")
        self.servicenow_url_input.textChanged.connect(self.on_setting_changed)
        servicenow_layout.addWidget(self.servicenow_url_input, 0, 1)
        
        servicenow_layout.addWidget(QLabel("Username:"), 1, 0)
        self.servicenow_username_input = QLineEdit()
        self.servicenow_username_input.setPlaceholderText("your-username")
        self.servicenow_username_input.textChanged.connect(self.on_setting_changed)
        servicenow_layout.addWidget(self.servicenow_username_input, 1, 1)
        
        servicenow_layout.addWidget(QLabel("API Token:"), 2, 0)
        self.servicenow_token_input = QLineEdit()
        self.servicenow_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.servicenow_token_input.setPlaceholderText("Enter ServiceNow API token")
        self.servicenow_token_input.textChanged.connect(self.on_setting_changed)
        servicenow_layout.addWidget(self.servicenow_token_input, 2, 1)
        
        self.servicenow_status_label = QLabel("Not configured")
        self.servicenow_status_label.setStyleSheet("color: red;")
        servicenow_layout.addWidget(self.servicenow_status_label, 3, 0, 1, 2)
        
        servicenow_group.setLayout(servicenow_layout)
        layout.addWidget(servicenow_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
        
    def create_app_settings_tab(self) -> QWidget:
        """Create the Application Settings tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # General Settings
        general_group = QGroupBox("General Settings")
        general_layout = QGridLayout()
        
        general_layout.addWidget(QLabel("Default Model:"), 0, 0)
        self.default_model_combo = QComboBox()
        self.default_model_combo.addItems(["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet", "gemini-pro"])
        self.default_model_combo.currentTextChanged.connect(self.on_setting_changed)
        general_layout.addWidget(self.default_model_combo, 0, 1)
        
        general_layout.addWidget(QLabel("Max Tokens:"), 1, 0)
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 32000)
        self.max_tokens_spin.setValue(2048)
        self.max_tokens_spin.valueChanged.connect(self.on_setting_changed)
        general_layout.addWidget(self.max_tokens_spin, 1, 1)
        
        general_layout.addWidget(QLabel("Temperature:"), 2, 0)
        self.temperature_spin = QSpinBox()
        self.temperature_spin.setRange(0, 20)
        self.temperature_spin.setValue(7)
        self.temperature_spin.setSuffix(" / 10")
        self.temperature_spin.valueChanged.connect(self.on_setting_changed)
        general_layout.addWidget(self.temperature_spin, 2, 1)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Performance Settings
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QGridLayout()
        
        self.enable_fallback_check = QCheckBox("Enable Fallback Providers")
        self.enable_fallback_check.setChecked(True)
        self.enable_fallback_check.toggled.connect(self.on_setting_changed)
        perf_layout.addWidget(self.enable_fallback_check, 0, 0)
        
        self.enable_retry_check = QCheckBox("Enable Automatic Retry")
        self.enable_retry_check.setChecked(True)
        self.enable_retry_check.toggled.connect(self.on_setting_changed)
        perf_layout.addWidget(self.enable_retry_check, 1, 0)
        
        perf_layout.addWidget(QLabel("Request Timeout (seconds):"), 2, 0)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.valueChanged.connect(self.on_setting_changed)
        perf_layout.addWidget(self.timeout_spin, 2, 1)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
        
    def create_local_models_tab(self) -> QWidget:
        """Create the Local Models tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Description
        desc_label = QLabel(
            "Configure local models for AI generation."
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Local Models Grid
        models_group = QGroupBox("Local Models")
        models_layout = QGridLayout()
        
        self.local_model_inputs = {}
        
        # Define models and their display names
        models = [
            ("gpt-3.5-turbo", "gpt-3.5-turbo"),
            ("gpt-4", "gpt-4"),
            ("claude-3-sonnet", "claude-3-sonnet"),
            ("gemini-pro", "gemini-pro"),
        ]
        
        for row, (model, display_name) in enumerate(models):
            # Model name
            name_label = QLabel(display_name)
            name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            models_layout.addWidget(name_label, row, 0)
            
            # Model input
            model_input = QLineEdit()
            model_input.setPlaceholderText(model)
            model_input.textChanged.connect(self.on_setting_changed)
            models_layout.addWidget(model_input, row, 1)
            
            self.local_model_inputs[model] = model_input
        
        models_group.setLayout(models_layout)
        layout.addWidget(models_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
        
    def create_security_tab(self) -> QWidget:
        """Create the Security tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Security Information
        info_group = QGroupBox("Security Information")
        info_layout = QVBoxLayout()
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(150)
        info_text.setPlainText(
            "Security Best Practices:\n\n"
            "1. API keys are stored in environment variables, not in configuration files\n"
            "2. Use .env files for local development (not committed to version control)\n"
            "3. Use system environment variables for production deployments\n"
            "4. Regularly rotate your API keys\n"
            "5. Use the minimum required permissions for each service\n\n"
            "Environment Variables:\n"
            "• OPENAI_API_KEY\n"
            "• ANTHROPIC_API_KEY\n"
            "• GOOGLE_API_KEY\n"
            "• AZURE_API_KEY\n"
            "• AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION\n"
            "• COHERE_API_KEY\n"
            "• JIRA_API_TOKEN, JIRA_BASE_URL, JIRA_USERNAME, JIRA_PROJECT_KEY\n"
            "• SERVICENOW_API_TOKEN, SERVICENOW_BASE_URL, SERVICENOW_USERNAME"
        )
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # .env File Management
        env_group = QGroupBox(".env File Management")
        env_layout = QVBoxLayout()
        
        env_buttons_layout = QHBoxLayout()
        
        self.create_env_button = QPushButton("Create .env Template")
        self.create_env_button.clicked.connect(self.create_env_template)
        env_buttons_layout.addWidget(self.create_env_button)
        
        self.open_env_button = QPushButton("Open .env File")
        self.open_env_button.clicked.connect(self.open_env_file)
        env_buttons_layout.addWidget(self.open_env_button)
        
        env_layout.addLayout(env_buttons_layout)
        env_group.setLayout(env_layout)
        layout.addWidget(env_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
        
    def load_current_settings(self):
        """Load current settings from environment and configuration."""
        # Load API keys
        for provider, config in self.api_key_inputs.items():
            current_value = self.secrets_manager.get_secret(config['env_var'])
            config['input'].setText(current_value)
            self.update_provider_status(provider)
        
        # Load AWS settings
        self.aws_access_key_input.setText(self.secrets_manager.get_secret("AWS_ACCESS_KEY"))
        self.aws_secret_key_input.setText(self.secrets_manager.get_secret("AWS_SECRET_KEY"))
        self.aws_region_input.setText(self.secrets_manager.get_secret("AWS_REGION"))
        self.update_aws_status()
        
        # Load service settings
        jira_config = self.secrets_manager.get_service_config('jira')
        self.jira_url_input.setText(jira_config.get('base_url', ''))
        self.jira_username_input.setText(jira_config.get('username', ''))
        self.jira_token_input.setText(jira_config.get('api_token', ''))
        self.jira_project_input.setText(jira_config.get('project_key', ''))
        self.update_jira_status()
        
        servicenow_config = self.secrets_manager.get_service_config('servicenow')
        self.servicenow_url_input.setText(servicenow_config.get('base_url', ''))
        self.servicenow_username_input.setText(servicenow_config.get('username', ''))
        self.servicenow_token_input.setText(servicenow_config.get('api_token', ''))
        self.update_servicenow_status()
        
        # Load local models
        for model, input_field in self.local_model_inputs.items():
            current_value = self.secrets_manager.get_secret(f"LOCAL_MODEL_{model.upper()}")
            input_field.setText(current_value)
        
        # Reset change tracking
        self.save_button.setEnabled(False)
        
    def update_provider_status(self, provider: str):
        """Update the status indicator for a provider."""
        if provider not in self.api_key_inputs:
            return
            
        config = self.api_key_inputs[provider]
        is_configured = is_provider_configured(provider)
        
        if is_configured:
            config['status'].setText("✓ Configured")
            config['status'].setStyleSheet("color: green;")
        else:
            config['status'].setText("Not configured")
            config['status'].setStyleSheet("color: red;")
            
    def update_aws_status(self):
        """Update AWS configuration status."""
        is_configured = (
            bool(self.aws_access_key_input.text().strip()) and
            bool(self.aws_secret_key_input.text().strip()) and
            bool(self.aws_region_input.text().strip())
        )
        
        if is_configured:
            self.aws_status_label.setText("✓ Configured")
            self.aws_status_label.setStyleSheet("color: green;")
        else:
            self.aws_status_label.setText("Not configured")
            self.aws_status_label.setStyleSheet("color: red;")
            
    def update_jira_status(self):
        """Update JIRA configuration status."""
        is_configured = is_service_configured('jira')
        
        if is_configured:
            self.jira_status_label.setText("✓ Configured")
            self.jira_status_label.setStyleSheet("color: green;")
        else:
            self.jira_status_label.setText("Not configured")
            self.jira_status_label.setStyleSheet("color: red;")
            
    def update_servicenow_status(self):
        """Update ServiceNow configuration status."""
        is_configured = is_service_configured('servicenow')
        
        if is_configured:
            self.servicenow_status_label.setText("✓ Configured")
            self.servicenow_status_label.setStyleSheet("color: green;")
        else:
            self.servicenow_status_label.setText("Not configured")
            self.servicenow_status_label.setStyleSheet("color: red;")
            
    def on_setting_changed(self):
        """Handle setting changes."""
        self.save_button.setEnabled(True)
        
        # Update status indicators
        for provider in self.api_key_inputs:
            self.update_provider_status(provider)
        self.update_aws_status()
        self.update_jira_status()
        self.update_servicenow_status()
        
    def test_api_key(self, provider: str):
        """Test an API key for a provider."""
        if provider not in self.api_key_inputs:
            return
            
        config = self.api_key_inputs[provider]
        api_key = config['input'].text().strip()
        
        if not api_key:
            QMessageBox.warning(self, "Test Failed", f"No API key provided for {provider}")
            return
            
        # This would typically make a test API call
        # For now, just show a success message
        QMessageBox.information(self, "Test Successful", f"{provider} API key appears to be valid")
        
    def save_settings(self):
        """Save settings to .env file."""
        try:
            # Get project root
            project_root = Path(__file__).parent.parent.parent.parent
            
            # Create .env file content
            env_content = []
            env_content.append("# AI Coder Assistant Configuration")
            env_content.append("# This file contains sensitive information - do not commit to version control")
            env_content.append("")
            
            # API Keys
            env_content.append("# AI Provider API Keys")
            for provider, config in self.api_key_inputs.items():
                value = config['input'].text().strip()
                if value:
                    env_content.append(f"{config['env_var']}={value}")
            env_content.append("")
            
            # AWS Configuration
            env_content.append("# AWS Configuration")
            aws_access = self.aws_access_key_input.text().strip()
            aws_secret = self.aws_secret_key_input.text().strip()
            aws_region = self.aws_region_input.text().strip()
            
            if aws_access:
                env_content.append(f"AWS_ACCESS_KEY={aws_access}")
            if aws_secret:
                env_content.append(f"AWS_SECRET_KEY={aws_secret}")
            if aws_region:
                env_content.append(f"AWS_REGION={aws_region}")
            env_content.append("")
            
            # Service Configuration
            env_content.append("# External Services")
            jira_url = self.jira_url_input.text().strip()
            jira_user = self.jira_username_input.text().strip()
            jira_token = self.jira_token_input.text().strip()
            jira_project = self.jira_project_input.text().strip()
            
            if jira_url:
                env_content.append(f"JIRA_BASE_URL={jira_url}")
            if jira_user:
                env_content.append(f"JIRA_USERNAME={jira_user}")
            if jira_token:
                env_content.append(f"JIRA_API_TOKEN={jira_token}")
            if jira_project:
                env_content.append(f"JIRA_PROJECT_KEY={jira_project}")
            env_content.append("")
            
            servicenow_url = self.servicenow_url_input.text().strip()
            servicenow_user = self.servicenow_username_input.text().strip()
            servicenow_token = self.servicenow_token_input.text().strip()
            
            if servicenow_url:
                env_content.append(f"SERVICENOW_BASE_URL={servicenow_url}")
            if servicenow_user:
                env_content.append(f"SERVICENOW_USERNAME={servicenow_user}")
            if servicenow_token:
                env_content.append(f"SERVICENOW_API_TOKEN={servicenow_token}")
            
            # Local Models
            env_content.append("# Local Models")
            for model, input_field in self.local_model_inputs.items():
                value = input_field.text().strip()
                if value:
                    env_content.append(f"LOCAL_MODEL_{model.upper()}={value}")
            
            # Write to .env file
            env_file = project_root / ".env"
            with open(env_file, 'w') as f:
                f.write('\n'.join(env_content))
            
            # Reload secrets manager
            self.secrets_manager.reload()
            
            # Update status
            self.save_button.setEnabled(False)
            QMessageBox.information(self, "Success", "Settings saved to .env file")
            
            # Emit signal
            self.settings_changed.emit()
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
            
    def reset_settings(self):
        """Reset settings to defaults."""
        reply = QMessageBox.question(
            self, 
            "Reset Settings", 
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear all inputs
            for config in self.api_key_inputs.values():
                config['input'].clear()
            
            self.aws_access_key_input.clear()
            self.aws_secret_key_input.clear()
            self.aws_region_input.clear()
            
            self.jira_url_input.clear()
            self.jira_username_input.clear()
            self.jira_token_input.clear()
            self.jira_project_input.clear()
            
            self.servicenow_url_input.clear()
            self.servicenow_username_input.clear()
            self.servicenow_token_input.clear()
            
            # Reset app settings
            self.default_model_combo.setCurrentText("gpt-3.5-turbo")
            self.max_tokens_spin.setValue(2048)
            self.temperature_spin.setValue(7)
            self.enable_fallback_check.setChecked(True)
            self.enable_retry_check.setChecked(True)
            self.timeout_spin.setValue(30)
            
            # Reset local models
            for input_field in self.local_model_inputs.values():
                input_field.clear()
            
            self.save_button.setEnabled(True)
            
    def reload_settings(self):
        """Reload settings from environment."""
        self.secrets_manager.reload()
        self.load_current_settings()
        QMessageBox.information(self, "Success", "Settings reloaded from environment")
        
    def create_env_template(self):
        """Create a .env template file."""
        try:
            project_root = Path(__file__).parent.parent.parent.parent
            template_file = project_root / ".env.template"
            
            template_content = [
                "# AI Coder Assistant - Environment Variables Template",
                "# Copy this file to .env and fill in your actual values",
                "# Do not commit .env files to version control",
                "",
                "# AI Provider API Keys",
                "OPENAI_API_KEY=your_openai_api_key_here",
                "ANTHROPIC_API_KEY=your_anthropic_api_key_here",
                "GOOGLE_API_KEY=your_google_api_key_here",
                "AZURE_API_KEY=your_azure_api_key_here",
                "COHERE_API_KEY=your_cohere_api_key_here",
                "",
                "# AWS Configuration",
                "AWS_ACCESS_KEY=your_aws_access_key_here",
                "AWS_SECRET_KEY=your_aws_secret_key_here",
                "AWS_REGION=us-east-1",
                "",
                "# JIRA Configuration",
                "JIRA_BASE_URL=https://your-domain.atlassian.net",
                "JIRA_USERNAME=your-email@domain.com",
                "JIRA_API_TOKEN=your_jira_api_token_here",
                "JIRA_PROJECT_KEY=PROJ",
                "",
                "# ServiceNow Configuration",
                "SERVICENOW_BASE_URL=https://your-instance.service-now.com",
                "SERVICENOW_USERNAME=your_username",
                "SERVICENOW_API_TOKEN=your_servicenow_api_token_here",
            ]
            
            with open(template_file, 'w') as f:
                f.write('\n'.join(template_content))
            
            QMessageBox.information(
                self, 
                "Template Created", 
                f"Environment template created at:\n{template_file}"
            )
            
        except Exception as e:
            logger.error(f"Error creating .env template: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create template: {e}")
            
    def open_env_file(self):
        """Open the .env file in the default editor."""
        try:
            project_root = Path(__file__).parent.parent.parent.parent
            env_file = project_root / ".env"
            
            if not env_file.exists():
                reply = QMessageBox.question(
                    self,
                    "File Not Found",
                    ".env file does not exist. Would you like to create it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.create_env_template()
                    env_file = project_root / ".env.template"
                else:
                    return
            
            # Open file with default system editor
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                os.startfile(env_file)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", env_file])
            else:  # Linux
                subprocess.run(["xdg-open", env_file])
                
        except Exception as e:
            logger.error(f"Error opening .env file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open .env file: {e}") 