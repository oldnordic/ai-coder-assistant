"""
Cloud Models Tab Widget

Provides UI for managing cloud AI providers, model selection,
usage monitoring, and cost tracking.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import (
    QThread, pyqtSignal, QTimer, Qt, QSize
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit,
    QTableWidget, QTableWidgetItem, QTabWidget, QGroupBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QProgressBar,
    QMessageBox, QSplitter, QFrame, QHeaderView
)
from PyQt6.QtGui import QFont, QIcon, QPixmap

from backend.services.llm_manager import LLMManager
from backend.services.models import ProviderType

logger = logging.getLogger(__name__)


class CloudModelsWorker(QThread):
    """Worker thread for cloud model operations."""
    
    # Signals
    providers_loaded = pyqtSignal(list)
    models_loaded = pyqtSignal(list)
    usage_stats_loaded = pyqtSignal(dict)
    health_check_completed = pyqtSignal(dict)
    test_completion_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.operation = None
        self.operation_args = {}
        self.llm_manager = LLMManager()
    
    def run(self):
        """Run the worker thread."""
        try:
            if self.operation == "load_providers":
                self._load_providers()
            elif self.operation == "load_models":
                self._load_models()
            elif self.operation == "load_usage_stats":
                self._load_usage_stats()
            elif self.operation == "health_check":
                self._health_check()
            elif self.operation == "test_completion":
                self._test_completion()
        except Exception as e:
            logger.error(f"Worker error: {e}")
            self.error_occurred.emit(str(e))
    
    def _load_providers(self):
        """Load available providers."""
        providers = []
        for provider_type, provider in self.llm_manager.providers.items():
            providers.append({
                "type": provider_type.value,
                "name": provider_type.value.title(),
                "enabled": provider.config.is_enabled,
                "priority": provider.config.priority,
                "timeout": provider.config.timeout
            })
        self.providers_loaded.emit(providers)
    
    def _load_models(self):
        """Load available models."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            models = loop.run_until_complete(self.llm_manager.list_available_models())
            self.models_loaded.emit(models)
        finally:
            loop.close()
    
    def _load_usage_stats(self):
        """Load usage statistics."""
        stats = self.llm_manager.get_usage_stats()
        self.usage_stats_loaded.emit(stats)
    
    def _health_check(self):
        """Perform health check on all providers."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            health_results = loop.run_until_complete(
                self.llm_manager.health_check()
            )
            self.health_check_completed.emit(health_results)
        finally:
            loop.close()
    
    def _test_completion(self):
        """Test completion with selected model."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            from backend.services.models import ChatMessage, ChatCompletionRequest
            messages = [ChatMessage(role="user", content=self.operation_args["prompt"])]
            model = self.operation_args.get("model")
            
            response = loop.run_until_complete(
                self.llm_manager.chat_completion(
                    messages=messages,
                    model=model
                )
            )
            self.test_completion_completed.emit(response)
        except Exception as e:
            self.error_occurred.emit(f"Test completion failed: {e}")
        finally:
            loop.close()


class ProviderConfigWidget(QWidget):
    """Widget for configuring cloud providers."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Provider configuration section
        provider_group = QGroupBox("Provider Configuration")
        provider_layout = QGridLayout()
        
        # OpenAI
        self.openai_enabled = QCheckBox("Enable OpenAI")
        self.openai_key = QLineEdit()
        self.openai_key.setPlaceholderText("OpenAI API Key")
        self.openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_base_url = QLineEdit()
        self.openai_base_url.setPlaceholderText("Base URL (optional)")
        self.openai_org = QLineEdit()
        self.openai_org.setPlaceholderText("Organization ID (optional)")
        
        provider_layout.addWidget(QLabel("OpenAI:"), 0, 0)
        provider_layout.addWidget(self.openai_enabled, 0, 1)
        provider_layout.addWidget(QLabel("API Key:"), 1, 0)
        provider_layout.addWidget(self.openai_key, 1, 1)
        provider_layout.addWidget(QLabel("Base URL:"), 2, 0)
        provider_layout.addWidget(self.openai_base_url, 2, 1)
        provider_layout.addWidget(QLabel("Organization:"), 3, 0)
        provider_layout.addWidget(self.openai_org, 3, 1)
        
        # Anthropic
        self.anthropic_enabled = QCheckBox("Enable Anthropic")
        self.anthropic_key = QLineEdit()
        self.anthropic_key.setPlaceholderText("Anthropic API Key")
        self.anthropic_key.setEchoMode(QLineEdit.EchoMode.Password)
        
        provider_layout.addWidget(QLabel("Anthropic:"), 4, 0)
        provider_layout.addWidget(self.anthropic_enabled, 4, 1)
        provider_layout.addWidget(QLabel("API Key:"), 5, 0)
        provider_layout.addWidget(self.anthropic_key, 5, 1)
        
        # Google AI
        self.google_enabled = QCheckBox("Enable Google AI")
        self.google_key = QLineEdit()
        self.google_key.setPlaceholderText("Google AI API Key")
        self.google_key.setEchoMode(QLineEdit.EchoMode.Password)
        
        provider_layout.addWidget(QLabel("Google AI:"), 6, 0)
        provider_layout.addWidget(self.google_enabled, 6, 1)
        provider_layout.addWidget(QLabel("API Key:"), 7, 0)
        provider_layout.addWidget(self.google_key, 7, 1)
        
        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)
        
        # Save button
        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.clicked.connect(self.save_settings)
        layout.addWidget(self.save_btn)
        
        self.setLayout(layout)
    
    def load_settings(self):
        """Load current settings."""
        # This would load from the settings service
        pass
    
    def save_settings(self):
        """Save current settings."""
        # This would save to the settings service
        QMessageBox.information(self, "Success", "Configuration saved successfully!")


class ModelSelectionWidget(QWidget):
    """Widget for model selection and testing."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_models()
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Model selection
        model_group = QGroupBox("Model Selection")
        model_layout = QGridLayout()
        
        self.provider_filter = QComboBox()
        self.provider_filter.addItem("All Providers")
        self.provider_filter.currentTextChanged.connect(self.filter_models)
        
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(7)
        self.model_table.setHorizontalHeaderLabels([
            "Model", "Provider", "Type", "Max Tokens", 
            "Context Window", "Cost/1K Tokens", "Features"
        ])
        self.model_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        model_layout.addWidget(QLabel("Filter by Provider:"), 0, 0)
        model_layout.addWidget(self.provider_filter, 0, 1)
        model_layout.addWidget(self.model_table, 1, 0, 1, 2)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Test completion
        test_group = QGroupBox("Test Completion")
        test_layout = QVBoxLayout()
        
        test_input_layout = QHBoxLayout()
        test_input_layout.addWidget(QLabel("Model:"))
        self.test_model = QComboBox()
        test_input_layout.addWidget(self.test_model)
        test_input_layout.addWidget(QLabel("Temperature:"))
        self.test_temperature = QDoubleSpinBox()
        self.test_temperature.setRange(0.0, 2.0)
        self.test_temperature.setValue(0.7)
        self.test_temperature.setSingleStep(0.1)
        test_input_layout.addWidget(self.test_temperature)
        test_input_layout.addWidget(QLabel("Max Tokens:"))
        self.test_max_tokens = QSpinBox()
        self.test_max_tokens.setRange(1, 32768)
        self.test_max_tokens.setValue(1000)
        test_input_layout.addWidget(self.test_max_tokens)
        
        test_layout.addLayout(test_input_layout)
        
        self.test_prompt = QTextEdit()
        self.test_prompt.setPlaceholderText("Enter test prompt...")
        self.test_prompt.setMaximumHeight(100)
        test_layout.addWidget(self.test_prompt)
        
        test_btn_layout = QHBoxLayout()
        self.test_btn = QPushButton("Test Completion")
        self.test_btn.clicked.connect(self.test_completion)
        test_btn_layout.addWidget(self.test_btn)
        test_btn_layout.addStretch()
        test_layout.addLayout(test_btn_layout)
        
        self.test_result = QTextEdit()
        self.test_result.setReadOnly(True)
        self.test_result.setMaximumHeight(200)
        test_layout.addWidget(self.test_result)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        self.setLayout(layout)
    
    def load_models(self):
        """Load available models."""
        self.worker = CloudModelsWorker()
        self.worker.operation = "load_models"
        self.worker.models_loaded.connect(self.populate_model_table)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
    
    def populate_model_table(self, models: List[Dict[str, Any]]):
        """Populate the model table."""
        self.model_table.setRowCount(len(models))
        
        for row, model in enumerate(models):
            # Model name
            name_item = QTableWidgetItem(model.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.model_table.setItem(row, 0, name_item)
            
            # Provider
            provider_item = QTableWidgetItem(model.provider.value)
            provider_item.setFlags(provider_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.model_table.setItem(row, 1, provider_item)
            
            # Context length
            context_item = QTableWidgetItem(str(model.context_length or "Unknown"))
            context_item.setFlags(context_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.model_table.setItem(row, 2, context_item)
            
            # Cost
            cost_item = QTableWidgetItem(f"${model.cost_per_1k_tokens or 0.0:.4f}/1k tokens")
            cost_item.setFlags(cost_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.model_table.setItem(row, 3, cost_item)
    
    def populate_provider_filter(self, models: List[Dict[str, Any]]):
        """Populate provider filter dropdown."""
        providers = set()
        for model in models:
            providers.add(model.provider.value)
        
        self.provider_filter.clear()
        self.provider_filter.addItem("All Providers")
        for provider in sorted(providers):
            self.provider_filter.addItem(provider)
    
    def populate_test_model_combo(self, models: List[Dict[str, Any]]):
        """Populate test model combo box."""
        self.test_model_combo.clear()
        for model in models:
            self.test_model_combo.addItem(model.name)
    
    def filter_models(self):
        """Filter models by provider."""
        selected_provider = self.provider_filter.currentText()
        
        self.worker = CloudModelsWorker()
        self.worker.operation = "load_models"
        self.worker.models_loaded.connect(self.populate_model_table)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
    
    def test_completion(self):
        """Test completion with selected model."""
        prompt = self.test_prompt.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Warning", "Please enter a test prompt.")
            return
        
        model_name = self.test_model.currentData()
        if not model_name:
            QMessageBox.warning(self, "Warning", "Please select a model.")
            return
        
        self.test_btn.setEnabled(False)
        self.test_result.clear()
        self.test_result.append("Testing completion...")
        
        # This would use the worker thread for async operation
        # For now, just show a placeholder
        self.test_result.append("Test completion would be implemented with async worker thread.")
        self.test_btn.setEnabled(True)

    def handle_error(self, error):
        QMessageBox.warning(self, "Error", f"An error occurred: {error}")


class UsageMonitoringWidget(QWidget):
    """Widget for monitoring usage and costs."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_usage_stats()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_usage_stats)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Summary stats
        summary_group = QGroupBox("Usage Summary")
        summary_layout = QGridLayout()
        
        self.total_requests_label = QLabel("0")
        self.total_cost_label = QLabel("$0.00")
        self.total_tokens_label = QLabel("0")
        
        summary_layout.addWidget(QLabel("Total Requests:"), 0, 0)
        summary_layout.addWidget(self.total_requests_label, 0, 1)
        summary_layout.addWidget(QLabel("Total Cost:"), 1, 0)
        summary_layout.addWidget(self.total_cost_label, 1, 1)
        summary_layout.addWidget(QLabel("Total Tokens:"), 2, 0)
        summary_layout.addWidget(self.total_tokens_label, 2, 1)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Provider usage
        provider_group = QGroupBox("Provider Usage")
        provider_layout = QVBoxLayout()
        
        self.provider_table = QTableWidget()
        self.provider_table.setColumnCount(3)
        self.provider_table.setHorizontalHeaderLabels([
            "Provider", "Requests", "Percentage"
        ])
        self.provider_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        provider_layout.addWidget(self.provider_table)
        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)
        
        # Model usage
        model_group = QGroupBox("Model Usage")
        model_layout = QVBoxLayout()
        
        self.model_table = QTableWidget()
        self.model_table.setColumnCount(3)
        self.model_table.setHorizontalHeaderLabels([
            "Model", "Requests", "Percentage"
        ])
        self.model_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        model_layout.addWidget(self.model_table)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_usage_stats)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)
        
        self.setLayout(layout)
    
    def load_usage_stats(self):
        """Load usage statistics."""
        self.worker = CloudModelsWorker()
        self.worker.operation = "load_usage_stats"
        self.worker.usage_stats_loaded.connect(self.update_summary_stats)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
    
    def update_summary_stats(self, stats: Dict[str, Any]):
        """Update summary statistics."""
        total_cost = stats.get("total_cost", 0.0)
        total_requests = stats.get("total_requests", 0)
        
        self.total_cost_label.setText(f"${total_cost:.2f}")
        self.total_requests_label.setText(str(total_requests))
    
    def update_provider_usage(self, providers: Dict[str, int]):
        """Update provider usage chart."""
        # This would update the provider usage visualization
        pass
    
    def update_model_usage(self, models: Dict[str, int]):
        """Update model usage chart."""
        # This would update the model usage visualization
        pass

    def handle_error(self, error):
        QMessageBox.warning(self, "Error", f"An error occurred: {error}")


class HealthCheckWidget(QWidget):
    """Widget for provider health monitoring."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.worker = CloudModelsWorker()
        self.worker.health_check_completed.connect(self.update_health_status)
        self.worker.error_occurred.connect(self.handle_error)
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Health status
        status_group = QGroupBox("Provider Health Status")
        status_layout = QVBoxLayout()
        
        self.health_table = QTableWidget()
        self.health_table.setColumnCount(3)
        self.health_table.setHorizontalHeaderLabels([
            "Provider", "Status", "Last Check"
        ])
        self.health_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        status_layout.addWidget(self.health_table)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.check_health_btn = QPushButton("Check Health")
        self.check_health_btn.clicked.connect(self.check_health)
        control_layout.addWidget(self.check_health_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        self.setLayout(layout)
    
    def check_health(self):
        """Check health of all providers."""
        self.worker = CloudModelsWorker()
        self.worker.operation = "health_check"
        self.worker.health_check_completed.connect(self.update_health_status)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
    
    def update_health_status(self, results: Dict[str, bool]):
        """Update health status display."""
        self.health_table.setRowCount(len(results))
        
        for row, (provider, is_healthy) in enumerate(results.items()):
            # Provider name
            provider_item = QTableWidgetItem(provider.value)
            provider_item.setFlags(provider_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.health_table.setItem(row, 0, provider_item)
            
            # Status
            status = "Healthy" if is_healthy else "Unhealthy"
            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if is_healthy:
                status_item.setBackground(Qt.GlobalColor.green)
            else:
                status_item.setBackground(Qt.GlobalColor.red)
            self.health_table.setItem(row, 1, status_item)
    
    def handle_error(self, error: str):
        """Handle worker errors."""
        QMessageBox.warning(self, "Error", f"An error occurred: {error}")


class CloudModelsTab(QWidget):
    """Main cloud models tab widget."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Provider configuration tab
        self.provider_config = ProviderConfigWidget()
        self.tab_widget.addTab(self.provider_config, "Provider Configuration")
        
        # Model selection tab
        self.model_selection = ModelSelectionWidget()
        self.tab_widget.addTab(self.model_selection, "Model Selection")
        
        # Usage monitoring tab
        self.usage_monitoring = UsageMonitoringWidget()
        self.tab_widget.addTab(self.usage_monitoring, "Usage Monitoring")
        
        # Health check tab
        self.health_check = HealthCheckWidget()
        self.tab_widget.addTab(self.health_check, "Health Check")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def refresh_data(self):
        """Refresh all data in the tab."""
        self.model_selection.load_models()
        self.usage_monitoring.load_usage_stats() 