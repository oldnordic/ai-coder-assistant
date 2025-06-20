"""
Ollama Manager Tab Widget

Provides UI for managing multiple Ollama instances (local and remote),
including configuration, health monitoring, and model management.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QDialog, QFormLayout, QLineEdit, QCheckBox, QSpinBox, QDialogButtonBox, QLabel, QMessageBox, QProgressBar, QHeaderView
)
from PyQt6.QtCore import pyqtSlot, QTimer
from PyQt6.QtGui import QFont
from backend.services.llm_manager import LLMManager
from backend.services.models import ProviderConfig, ProviderType
import asyncio
import logging
from typing import List, Dict, Any, Optional
import concurrent.futures
from src.backend.utils.constants import (
    DEFAULT_TIMEOUT, DEFAULT_MAX_WORKERS
)

logger = logging.getLogger(__name__)

class OllamaInstanceDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None, config: Optional[ProviderConfig] = None):
        super().__init__(parent)
        self.setWindowTitle("Ollama Instance Configuration")
        self.config = config
        self.init_ui()
        if config:
            self.load_config(config)

    def init_ui(self):
        layout = QFormLayout()
        self.name_edit = QLineEdit()
        self.url_edit = QLineEdit()
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.ssl_check = QCheckBox("Verify SSL")
        self.ssl_check.setChecked(True)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(DEFAULT_TIMEOUT)
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 10)
        self.priority_spin.setValue(DEFAULT_MAX_WORKERS)
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(True)
        layout.addRow("Instance Name", self.name_edit)
        layout.addRow("Base URL", self.url_edit)
        layout.addRow("Auth Token", self.token_edit)
        layout.addRow("SSL Verification", self.ssl_check)
        layout.addRow("Timeout (s)", self.timeout_spin)
        layout.addRow("Priority", self.priority_spin)
        layout.addRow("Enabled", self.enabled_check)
        self.setLayout(layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

    def load_config(self, config: ProviderConfig):
        self.name_edit.setText(config.instance_name or "")
        self.url_edit.setText(config.base_url or "")
        self.token_edit.setText(config.api_key or "")
        self.ssl_check.setChecked(config.verify_ssl)
        self.timeout_spin.setValue(config.timeout)
        self.priority_spin.setValue(config.priority)
        self.enabled_check.setChecked(config.is_enabled)

    def get_config(self) -> ProviderConfig:
        return ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            api_key=self.token_edit.text().strip(),
            base_url=self.url_edit.text().strip(),
            timeout=self.timeout_spin.value(),
            priority=self.priority_spin.value(),
            is_enabled=self.enabled_check.isChecked(),
            instance_name=self.name_edit.text().strip(),
            verify_ssl=self.ssl_check.isChecked(),
        )

# Mock backend functions for now
def ollama_backend(operation: str, **kwargs) -> Dict[str, Any]:
    """Mock backend function for Ollama operations."""
    if operation == 'list_models':
        return {
            'success': True,
            'models': ['llama2', 'codellama', 'mistral', 'neural-chat']
        }
    elif operation == 'pull_model':
        model_name = kwargs.get('operation_args', {}).get('model_name', 'unknown')
        return {
            'success': True,
            'model_name': model_name,
            'status': 'downloaded'
        }
    elif operation == 'delete_model':
        model_name = kwargs.get('operation_args', {}).get('model_name', 'unknown')
        return {
            'success': True,
            'model_name': model_name,
            'status': 'deleted'
        }
    elif operation == 'mock_operation':
        return {'success': True, 'models': []}
    else:
        return {'success': False, 'error': f'Unknown operation: {operation}'}

class OllamaManagerTab(QWidget):
    """Ollama Manager Tab Widget."""
    
    def __init__(self, llm_manager: LLMManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.llm_manager = llm_manager
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Ollama Model Manager")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_models)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Models table
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(5)
        self.models_table.setHorizontalHeaderLabels([
            "Name", "Size", "Status", "Instance", "Actions"
        ])
        
        header = self.models_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.models_table)

    def handle_error(self, error):
        QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", str(error)))

    def load_data(self):
        """Load Ollama models data by running it in a worker thread."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        def fetch_models():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.llm_manager.list_ollama_models())
            loop.close()
            return result
        self.executor.submit(fetch_models).add_done_callback(self._on_models_loaded)

    def refresh_models(self):
        """Refresh the list of available models."""
        self.load_data()

    @pyqtSlot(object)
    def _on_models_loaded(self, future):
        def update_ui():
            try:
                result = future.result()
                self.populate_models_table(result)
                self.test_btn.setEnabled(True)
            except Exception as e:
                self.handle_error(f"Loading models failed: {e}")
                self.test_btn.setEnabled(True)
        QTimer.singleShot(0, update_ui)

    def populate_models_table(self, models: List[Any]):
        """Populate models table with data."""
        self.models_table.setRowCount(0) # Clear table before populating
        self.models_table.setRowCount(len(models))
        for i, model_data in enumerate(models):
            # Handle both ModelConfig objects and dictionaries
            if hasattr(model_data, 'name'):
                # ModelConfig object
                model_name = model_data.name
                size_bytes = getattr(model_data, 'context_length', 0)
                size_gb = f"{size_bytes / (1024**3):.2f} GB" if size_bytes > 0 else "N/A"
            else:
                # Dictionary fallback
                model_name = model_data.get('name', 'N/A')
                size_bytes = model_data.get('size', 0)
                size_gb = f"{size_bytes / (1024**3):.2f} GB" if size_bytes > 0 else "N/A"

            # Name
            name_item = QTableWidgetItem(model_name)
            self.models_table.setItem(i, 0, name_item)

            # Size
            size_item = QTableWidgetItem(size_gb)
            self.models_table.setItem(i, 1, size_item)

            # Status
            status_item = QTableWidgetItem("Available")
            self.models_table.setItem(i, 2, status_item)
            
            # Instance (assuming 'local' for now, can be enhanced)
            instance_item = QTableWidgetItem("Local")
            self.models_table.setItem(i, 3, instance_item)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, m=model_name: self.delete_model(m))
            actions_layout.addWidget(delete_btn)

            export_btn = QPushButton("Export")
            # Assuming export_model is defined elsewhere
            export_btn.clicked.connect(lambda checked, m=model_name: self.export_model(m))
            actions_layout.addWidget(export_btn)
            
            self.models_table.setCellWidget(i, 4, actions_widget)
    
    def delete_model(self, model_name: str):
        """Delete a model from Ollama."""
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the model '{model_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
            
        if reply == QMessageBox.StandardButton.Yes:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            logger.info(f"Starting deletion for model: {model_name}")
            self.executor.submit(self.llm_manager.delete_model, model_name).add_done_callback(self._on_delete_complete)

    @pyqtSlot(object)
    def _on_delete_complete(self, future):
        def update_ui():
            try:
                result = future.result()
                self.handle_delete_result(result)
            except Exception as e:
                self.handle_error(f"Delete failed: {e}")
        QTimer.singleShot(0, update_ui)

    def export_model(self, model_name: str):
        """Export a model from Ollama."""
        # This can also be moved to a worker thread if it's a long-running task
        QMessageBox.information(self, "Export", f"Exporting model: {model_name}")
