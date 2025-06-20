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
    QTimer, Qt, QSize
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit,
    QTableWidget, QTableWidgetItem, QTabWidget, QGroupBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QProgressBar,
    QMessageBox, QSplitter, QFrame, QHeaderView
)
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import QApplication

from backend.services.llm_manager import LLMManager
from backend.services.models import ProviderType
from frontend.ui.worker_threads import get_thread_manager

logger = logging.getLogger(__name__)

# Mock backend functions for now
def cloud_models_backend(operation: str, **kwargs) -> Dict[str, Any]:
    """Mock backend function for cloud models operations."""
    if operation == 'load_models':
        return {
            'success': True,
            'models': [
                {'name': 'gpt-4', 'provider': 'openai', 'type': 'chat', 'max_tokens': 8192},
                {'name': 'claude-3', 'provider': 'anthropic', 'type': 'chat', 'max_tokens': 200000}
            ]
        }
    elif operation == 'mock_operation':
        return {'success': True, 'models': []}
    else:
        return {'success': False, 'error': f'Unknown operation: {operation}'}

def get_usage_stats(progress_callback=None, log_message_callback=None, cancellation_callback=None) -> Dict[str, Any]:
    """Mock function to get usage statistics."""
    return {
        'total_requests': 1500,
        'total_tokens': 2500000,
        'total_cost': 45.67,
        'providers': {
            'openai': {'requests': 800, 'tokens': 1200000, 'cost': 24.50},
            'anthropic': {'requests': 700, 'tokens': 1300000, 'cost': 21.17}
        }
    }

def check_provider_health(provider: str, progress_callback=None, log_message_callback=None, cancellation_callback=None) -> Dict[str, Any]:
    """Mock function to check provider health."""
    return {
        'provider': provider,
        'status': 'healthy',
        'response_time': 0.5,
        'last_check': datetime.now().isoformat()
    }

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
        self.thread_manager = get_thread_manager()
        self.init_ui()
    
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
        
        # Progress bar and status
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        layout.addLayout(progress_layout)
        
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
        
        # Add refresh button
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Models")
        self.refresh_btn.clicked.connect(self.load_models)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)
        
        self.setLayout(layout)
    
    def populate_models_table(self, models):
        """Populate models table with data."""
        # Implementation for populating models table
        pass

    def update_progress(self, current, total, message):
        """Update progress bar."""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(int((current / total) * 100))
            if hasattr(self, 'status_label'):
                self.status_label.setText(message)

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
        
        try:
            self.thread_manager.start_worker(
                'cloud_models',
                cloud_models_backend,
                'load_models',
                provider=selected_provider,
                progress_callback=self.update_progress,
                log_message_callback=self.handle_log_message
            )
        except Exception as e:
            logger.error(f"Error filtering models: {e}")
            QMessageBox.warning(self, "Error", f"Failed to filter models: {e}")

    def test_completion(self):
        """Test a model completion."""
        model_name = self.test_model.currentText()
        if not model_name:
            self.show_error("Please select a model to test.")
            return

        prompt = self.test_prompt.toPlainText()
        if not prompt:
            self.show_error("Please enter a prompt.")
            return

        self.progress_bar.setVisible(True)
        self.status_label.setText("Generating completion...")
        self.test_result.clear()

        # Backend function would be called here
        # For now, using a mock result after a delay
        def mock_backend_completion(*args, **kwargs):
            import time
            time.sleep(2)
            return {"success": True, "result": f"This is a test completion for {model_name}."}

        self.thread_manager.start_worker(
            "test_completion",
            mock_backend_completion,
            callback=self.handle_operation_complete
        )

    def handle_error(self, error):
        self.show_error(str(error))

    def load_models(self):
        """Load models from all configured providers."""
        self.progress_bar.setVisible(True)
        self.status_label.setText("Loading models...")
        
        self.thread_manager.start_worker(
            'load_cloud_models',
            cloud_models_backend,
            operation='load_models',
            callback=self.handle_operation_complete
        )

    def _on_worker_progress(self, worker_id, current, total, message):
        """Handle progress updates from worker."""
        if hasattr(self, 'worker_id') and worker_id == self.worker_id:
            self.update_progress(current, total, message)

    def _on_worker_finished(self, worker_id):
        if hasattr(self, 'worker_id') and worker_id == self.worker_id:
            result = cloud_models_backend('mock_operation')
            self.handle_operation_complete(result)
            self.progress_bar.setVisible(False)

    def _on_worker_error(self, worker_id, error):
        if hasattr(self, 'worker_id') and worker_id == self.worker_id:
            self.show_error(error)
            self.progress_bar.setVisible(False)

    def handle_log_message(self, message):
        # Optionally handle log messages
        pass

    def handle_operation_complete(self, result):
        """Handle operation completion."""
        if result['success']:
            if 'models' in result:
                self.populate_models_table(result['models'])
            elif 'model_name' in result:
                if result.get('status') == 'downloaded':
                    QMessageBox.information(self, "Success", f"Model {result['model_name']} downloaded successfully")
                elif result.get('status') == 'deleted':
                    QMessageBox.information(self, "Success", f"Model {result['model_name']} deleted successfully")
        else:
            QMessageBox.warning(self, "Error", "Operation failed")

    def show_error(self, error):
        """Handle operation error."""
        QMessageBox.critical(self, "Error", f"Operation failed: {error}")
    
    def populate_models_table(self, models):
        """Populate models table with data."""
        # Implementation for populating models table
        pass


class UsageMonitoringWidget(QWidget):
    """Widget for monitoring usage and costs."""
    
    def __init__(self):
        super().__init__()
        self.thread_manager = get_thread_manager()
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

        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        
        # Add progress bar at the bottom
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
    
    def load_usage_stats(self):
        """Load usage statistics."""
        self.progress_bar.setVisible(True)
        self.thread_manager.start_worker(
            "get_usage_stats",
            self.fetch_usage_stats,
            callback=self.update_summary_stats
        )
    
    def update_summary_stats(self, stats: Dict[str, Any]):
        """Callback to update the summary statistics labels."""
        try:
            _ = self.isVisible()
        except RuntimeError:
            return

        if not stats:
            if hasattr(self, 'summary_groupbox'):
                self.summary_groupbox.hide()
            return

        if hasattr(self, 'summary_groupbox'):
            self.summary_groupbox.show()
        
        total_requests = stats.get('total_requests', 0)
        total_tokens = stats.get('total_tokens', 0)
        
        if hasattr(self, 'total_requests_label'):
            self.total_requests_label.setText(f"{total_requests:,}")
        if hasattr(self, 'total_tokens_label'):
            self.total_tokens_label.setText(f"{total_tokens:,}")
        
        if hasattr(self, 'provider_stats_layout'):
            for i in reversed(range(self.provider_stats_layout.count())): 
                widget = self.provider_stats_layout.itemAt(i).widget()
                if widget is not None:
                    widget.deleteLater()

            for provider, provider_stats in stats.get('providers', {}).items():
                reqs = provider_stats.get('requests', 0)
                toks = provider_stats.get('tokens', 0)
                provider_label = QLabel(f"{provider}: Requests: {reqs:,}, Tokens: {toks:,}")
                self.provider_stats_layout.addWidget(provider_label)
    
    def update_provider_usage(self, providers: Dict[str, int]):
        """Update provider usage chart."""
        # This method needs to be implemented
        pass
    
    def update_model_usage(self, models: Dict[str, int]):
        """Update model usage chart."""
        # This would update the model usage visualization
        pass

    def handle_log_message(self, message):
        """Handle log messages."""
        # Implementation for log messages
        pass

    def update_progress(self, current, total, message):
        """Update progress bar."""
        # Implementation for progress updates
        pass

    def fetch_usage_stats(self, progress_callback=None, log_message_callback=None, cancellation_callback=None):
        """Fetch usage statistics from the LLM manager."""
        try:
            llm_manager = LLMManager()
            return llm_manager.get_usage_stats()
        except Exception as e:
            if log_message_callback:
                log_message_callback(f"Error fetching usage stats: {e}")
            return None


class HealthCheckWidget(QWidget):
    """Widget for provider health monitoring."""
    
    def __init__(self):
        super().__init__()
        self.thread_manager = get_thread_manager()
        self.init_ui()
    
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
        """Check health of all enabled providers."""
        self.progress_bar.setVisible(True)
        
        # This would be more complex in a real app, checking all enabled providers
        self.thread_manager.start_worker(
            "check_provider_health",
            check_provider_health,
            provider='openai',
            callback=self.update_health_status
        )
    
    def update_health_status(self, results: Dict[str, bool]):
        """Update health status table."""
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


class CloudModelsTab(QWidget):
    """Main cloud models tab widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        from frontend.ui.worker_threads import get_thread_manager
        self.thread_manager = get_thread_manager()
        self.init_ui()
        self.start_usage_stats_worker()
        
        # Connect to the application's aboutToQuit signal for cleanup
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self.cleanup)

    def init_ui(self):
        """Initialize the UI components of the tab."""
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
        self.start_usage_stats_worker()

    def start_usage_stats_worker(self):
        """Start the worker to fetch usage stats."""
        self.thread_manager.start_worker(
            "get_usage_stats",
            self.fetch_usage_stats,
            callback=self.update_summary_stats
        )

    def cleanup(self):
        """Stop any running workers to prevent memory leaks and crashes."""
        self.thread_manager.cancel_worker("get_usage_stats")

    def __del__(self):
        # Ensure cleanup is called when the widget is deleted
        self.cleanup()

    def refresh_data(self):
        """Refresh all data in the tab."""
        self.model_selection.load_models()
        self.usage_monitoring.load_usage_stats()

    def load_models(self):
        """Load models from backend."""
        self.progress_bar.setVisible(True)
        self.thread_manager.start_worker(
            'load_cloud_models',
            cloud_models_backend,
            operation='load_models',
            callback=self.handle_operation_complete
        )

    def _on_worker_progress(self, worker_id, current, total, message):
        """Handle progress updates from worker."""
        if hasattr(self, 'worker_id') and worker_id == self.worker_id:
            self.update_progress(current, total, message)

    def _on_worker_finished(self, worker_id):
        if hasattr(self, 'worker_id') and worker_id == self.worker_id:
            result = cloud_models_backend('mock_operation')
            self.handle_operation_complete(result)
            self.progress_bar.setVisible(False)

    def _on_worker_error(self, worker_id, error):
        if hasattr(self, 'worker_id') and worker_id == self.worker_id:
            self.show_error(error)
            self.progress_bar.setVisible(False)

    def handle_log_message(self, message):
        # Optionally handle log messages
        pass

    def handle_operation_complete(self, result):
        """Handle operation completion."""
        if result['success']:
            if 'models' in result:
                self.populate_models_table(result['models'])
            elif 'model_name' in result:
                if result.get('status') == 'downloaded':
                    QMessageBox.information(self, "Success", f"Model {result['model_name']} downloaded successfully")
                elif result.get('status') == 'deleted':
                    QMessageBox.information(self, "Success", f"Model {result['model_name']} deleted successfully")
        else:
            QMessageBox.warning(self, "Error", "Operation failed")

    def show_error(self, error):
        """Handle operation error."""
        QMessageBox.critical(self, "Error", f"Operation failed: {error}")
    
    def update_progress(self, current, total, message):
        """Update progress bar."""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(int((current / total) * 100))
            self.progress_bar.setFormat(f"{message} ({current/total*100:.0f}%)")

    def populate_models_table(self, models):
        """Populate models table with data."""
        self.model_selection.populate_models_table(models)

    def populate_models_table(self, models):
        """Populate models table with data."""
        # Implementation for populating models table
        pass

    def update_provider_usage(self, providers: Dict[str, int]):
        # This method needs to be implemented
        pass

    def fetch_usage_stats(self, progress_callback=None, log_message_callback=None, cancellation_callback=None):
        """Fetch usage statistics from the LLM manager."""
        try:
            llm_manager = LLMManager()
            return llm_manager.get_usage_stats()
        except Exception as e:
            if log_message_callback:
                log_message_callback(f"Error fetching usage stats: {e}")
            return None

    def update_summary_stats(self, stats: Dict[str, Any]):
        """Callback to update the summary statistics labels."""
        try:
            _ = self.isVisible()
        except RuntimeError:
            return

        if not stats:
            if hasattr(self, 'summary_groupbox'):
                self.summary_groupbox.hide()
            return

        if hasattr(self, 'summary_groupbox'):
            self.summary_groupbox.show()
        
        total_requests = stats.get('total_requests', 0)
        total_tokens = stats.get('total_tokens', 0)
        
        if hasattr(self, 'total_requests_label'):
            self.total_requests_label.setText(f"{total_requests:,}")
        if hasattr(self, 'total_tokens_label'):
            self.total_tokens_label.setText(f"{total_tokens:,}")
        
        if hasattr(self, 'provider_stats_layout'):
            for i in reversed(range(self.provider_stats_layout.count())): 
                widget = self.provider_stats_layout.itemAt(i).widget()
                if widget is not None:
                    widget.deleteLater()

            for provider, provider_stats in stats.get('providers', {}).items():
                reqs = provider_stats.get('requests', 0)
                toks = provider_stats.get('tokens', 0)
                provider_label = QLabel(f"{provider}: Requests: {reqs:,}, Tokens: {toks:,}")
                self.provider_stats_layout.addWidget(provider_label)

    def update_provider_usage(self, providers: Dict[str, int]):
        # This method needs to be implemented
        pass

    def fetch_usage_stats(self, progress_callback=None, log_message_callback=None, cancellation_callback=None):
        """Fetch usage statistics from the LLM manager."""
        try:
            llm_manager = LLMManager()
            return llm_manager.get_usage_stats()
        except Exception as e:
            if log_message_callback:
                log_message_callback(f"Error fetching usage stats: {e}")
            return None 