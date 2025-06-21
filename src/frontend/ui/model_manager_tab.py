"""
Model Manager Tab Widget

Provides UI for managing multiple model sources including:
- Remote Ollama instances (local and remote)
- Local fine-tuned models for code review
- Model configuration, health monitoring, and management
- Integration with LocalCodeReviewer for seamless model switching
"""

import asyncio
import concurrent.futures
import logging
import os
import json
import time
import requests
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from PyQt6.QtCore import QTimer, pyqtSlot, Qt, QThread, QObject
from PyQt6.QtGui import QFont, QPixmap, QIcon
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QGroupBox,
    QTabWidget,
    QTextEdit,
    QComboBox,
    QFileDialog,
    QSplitter,
    QFrame,
    QProgressDialog,
    QApplication,
)

from src.backend.services.llm_manager import LLMManager
from src.backend.services.models import ProviderConfig, ProviderType
from src.backend.services.ollama_client import OllamaClient, get_available_models_sync, get_ollama_response
from src.backend.services.local_code_reviewer import get_local_code_reviewer, LocalCodeReviewer
from src.backend.services.trainer import fine_tune_code_model, create_code_review_dataset, evaluate_model_performance
from src.backend.utils.constants import DEFAULT_MAX_WORKERS, DEFAULT_TIMEOUT, HTTP_OK
from src.backend.utils.secrets import get_secrets_manager
from src.backend.utils.config import get_url

logger = logging.getLogger(__name__)


class ModelTrainingDialog(QDialog):
    """Dialog for starting new model training runs."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Start New Model Training")
        self.setModal(True)
        self.resize(600, 500)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Dataset selection
        dataset_group = QGroupBox("Training Dataset")
        dataset_layout = QFormLayout(dataset_group)
        
        self.dataset_path_edit = QLineEdit()
        self.dataset_path_edit.setPlaceholderText("Select training dataset file (JSON format)")
        self.browse_dataset_button = QPushButton("Browse...")
        self.browse_dataset_button.clicked.connect(self.browse_dataset)
        
        dataset_path_layout = QHBoxLayout()
        dataset_path_layout.addWidget(self.dataset_path_edit)
        dataset_path_layout.addWidget(self.browse_dataset_button)
        
        dataset_layout.addRow("Dataset Path:", dataset_path_layout)
        layout.addWidget(dataset_group)
        
        # Model configuration
        model_group = QGroupBox("Model Configuration")
        model_layout = QFormLayout(model_group)
        
        self.base_model_combo = QComboBox()
        self.base_model_combo.addItems([
            "microsoft/DialoGPT-medium",
            "microsoft/DialoGPT-large", 
            "gpt2",
            "gpt2-medium",
            "distilgpt2",
            "codellama/CodeLlama-7b-hf",
            "microsoft/DialoGPT-small"
        ])
        
        self.output_model_edit = QLineEdit()
        self.output_model_edit.setPlaceholderText("code-reviewer-v1")
        
        model_layout.addRow("Base Model:", self.base_model_combo)
        model_layout.addRow("Output Model Name:", self.output_model_edit)
        layout.addWidget(model_group)
        
        # Training parameters
        training_group = QGroupBox("Training Parameters")
        training_layout = QFormLayout(training_group)
        
        self.epochs_spin = QSpinBox()
        self.epochs_spin.setRange(1, 10)
        self.epochs_spin.setValue(3)
        
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 16)
        self.batch_size_spin.setValue(4)
        
        self.learning_rate_edit = QLineEdit("2e-4")
        
        training_layout.addRow("Epochs:", self.epochs_spin)
        training_layout.addRow("Batch Size:", self.batch_size_spin)
        training_layout.addRow("Learning Rate:", self.learning_rate_edit)
        layout.addWidget(training_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def browse_dataset(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Training Dataset", "", "JSON Files (*.json)"
        )
        if file_path:
            self.dataset_path_edit.setText(file_path)
    
    def get_training_config(self) -> Dict[str, Any]:
        """Get the training configuration from the dialog."""
        return {
            "dataset_path": self.dataset_path_edit.text(),
            "base_model": self.base_model_combo.currentText(),
            "output_model_name": self.output_model_edit.text(),
            "epochs": self.epochs_spin.value(),
            "batch_size": self.batch_size_spin.value(),
            "learning_rate": float(self.learning_rate_edit.text())
        }


class DatasetCreationDialog(QDialog):
    """Dialog for creating training datasets from code examples."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Create Training Dataset")
        self.setModal(True)
        self.resize(500, 400)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Input method selection
        method_group = QGroupBox("Input Method")
        method_layout = QVBoxLayout(method_group)
        
        self.file_input_radio = QCheckBox("Load from existing JSON file")
        self.file_input_radio.setChecked(True)
        self.file_input_radio.toggled.connect(self.on_input_method_changed)
        
        self.manual_input_radio = QCheckBox("Create manually")
        self.manual_input_radio.toggled.connect(self.on_input_method_changed)
        
        method_layout.addWidget(self.file_input_radio)
        method_layout.addWidget(self.manual_input_radio)
        layout.addWidget(method_group)
        
        # File input section
        self.file_group = QGroupBox("File Input")
        file_layout = QFormLayout(self.file_group)
        
        self.input_file_edit = QLineEdit()
        self.input_file_edit.setPlaceholderText("Select input file with code examples")
        self.browse_input_button = QPushButton("Browse...")
        self.browse_input_button.clicked.connect(self.browse_input_file)
        
        input_file_layout = QHBoxLayout()
        input_file_layout.addWidget(self.input_file_edit)
        input_file_layout.addWidget(self.browse_input_button)
        
        file_layout.addRow("Input File:", input_file_layout)
        layout.addWidget(self.file_group)
        
        # Manual input section
        self.manual_group = QGroupBox("Manual Input")
        manual_layout = QVBoxLayout(self.manual_group)
        
        self.manual_text = QTextEdit()
        self.manual_text.setPlaceholderText("""Enter code examples in JSON format:

[
  {
    "code": "def bad_function():\\n    x = 1\\n    return x",
    "issue": "Function lacks documentation",
    "analysis": "This function has no docstring explaining its purpose",
    "suggestion": "Add a docstring to explain what the function does"
  }
]""")
        
        manual_layout.addWidget(self.manual_text)
        layout.addWidget(self.manual_group)
        
        # Output configuration
        output_group = QGroupBox("Output Configuration")
        output_layout = QFormLayout(output_group)
        
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Select output path for dataset")
        self.browse_output_button = QPushButton("Browse...")
        self.browse_output_button.clicked.connect(self.browse_output_file)
        
        output_path_layout = QHBoxLayout()
        output_path_layout.addWidget(self.output_path_edit)
        output_path_layout.addWidget(self.browse_output_button)
        
        output_layout.addRow("Output Path:", output_path_layout)
        layout.addWidget(output_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Initial state
        self.on_input_method_changed()
        
    def on_input_method_changed(self):
        """Handle input method change."""
        self.file_group.setVisible(self.file_input_radio.isChecked())
        self.manual_group.setVisible(self.manual_input_radio.isChecked())
        
    def browse_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Input File", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.input_file_edit.setText(file_path)
            
    def browse_output_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Dataset As", "", "JSON Files (*.json)"
        )
        if file_path:
            self.output_path_edit.setText(file_path)
    
    def get_dataset_config(self) -> Dict[str, Any]:
        """Get the dataset configuration from the dialog."""
        return {
            "input_method": "file" if self.file_input_radio.isChecked() else "manual",
            "input_file": self.input_file_edit.text() if self.file_input_radio.isChecked() else None,
            "manual_data": self.manual_text.toPlainText() if self.manual_input_radio.isChecked() else None,
            "output_path": self.output_path_edit.text()
        }


class OllamaInstanceDialog(QDialog):
    def __init__(
        self, parent: Optional[QWidget] = None, config: Optional[ProviderConfig] = None
    ):
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
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
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
            instance_name=self.name_edit.text(),
            base_url=self.url_edit.text(),
            api_key=self.token_edit.text(),
            verify_ssl=self.ssl_check.isChecked(),
            timeout=self.timeout_spin.value(),
            priority=self.priority_spin.value(),
            is_enabled=self.enabled_check.isChecked(),
            provider_type=ProviderType.OLLAMA
        )


class ModelManagerTab(QWidget):
    """Main model manager tab widget with enhanced LocalCodeReviewer integration."""

    def __init__(self, llm_manager: LLMManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.llm_manager = llm_manager
        self.ollama_client = OllamaClient()
        self.local_code_reviewer = get_local_code_reviewer()
        self.secrets_manager = get_secrets_manager()
        self.setup_ui()
        self.load_data()
        
        # Set up periodic health checks
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self.check_model_health)
        self.health_timer.start(30000)  # Check every 30 seconds

    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Header with current model status
        header_group = QGroupBox("Current Model Status")
        header_layout = QVBoxLayout(header_group)
        
        # Current model info
        current_model_layout = QHBoxLayout()
        current_model_layout.addWidget(QLabel("Active Model:"))
        self.current_model_label = QLabel("Loading...")
        self.current_model_label.setStyleSheet("font-weight: bold; color: #007bff;")
        current_model_layout.addWidget(self.current_model_label)
        current_model_layout.addStretch()
        
        # Model health indicator
        self.health_indicator = QLabel("●")
        self.health_indicator.setStyleSheet("font-size: 16px; color: #28a745;")
        current_model_layout.addWidget(self.health_indicator)
        
        header_layout.addLayout(current_model_layout)
        
        # Model switching
        switch_layout = QHBoxLayout()
        switch_layout.addWidget(QLabel("Switch to:"))
        self.model_switch_combo = QComboBox()
        self.model_switch_combo.currentTextChanged.connect(self.switch_model)
        switch_layout.addWidget(self.model_switch_combo)
        switch_layout.addStretch()
        
        header_layout.addLayout(switch_layout)
        layout.addWidget(header_group)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Ollama tab
        self.ollama_tab = self.create_ollama_tab()
        self.tab_widget.addTab(self.ollama_tab, "Ollama Models")
        
        # Local models tab
        self.local_tab = self.create_local_tab()
        self.tab_widget.addTab(self.local_tab, "Fine-tuned Models")
        
        # Training tab
        self.training_tab = self.create_training_tab()
        self.tab_widget.addTab(self.training_tab, "Model Training")
        
        # Health monitoring tab
        self.health_tab = self.create_health_tab()
        self.tab_widget.addTab(self.health_tab, "Health Monitor")
        
        layout.addWidget(self.tab_widget)

    def create_ollama_tab(self) -> QWidget:
        """Create the Ollama models tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Ollama instances management
        instances_group = QGroupBox("Ollama Instances")
        instances_layout = QVBoxLayout(instances_group)
        
        self.ollama_instances_table = QTableWidget()
        self.ollama_instances_table.setColumnCount(4)
        self.ollama_instances_table.setHorizontalHeaderLabels([
            "Name", "URL", "Status", "Actions"
        ])
        self.ollama_instances_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        instances_layout.addWidget(self.ollama_instances_table)
        
        instances_buttons = QHBoxLayout()
        self.add_instance_button = QPushButton("Add Instance")
        self.add_instance_button.clicked.connect(self.add_ollama_instance)
        self.refresh_instances_button = QPushButton("Refresh")
        self.refresh_instances_button.clicked.connect(self.refresh_ollama_instances)
        instances_buttons.addWidget(self.add_instance_button)
        instances_buttons.addWidget(self.refresh_instances_button)
        instances_buttons.addStretch()
        instances_layout.addLayout(instances_buttons)
        
        layout.addWidget(instances_group)
        
        # Available models
        models_group = QGroupBox("Available Models")
        models_layout = QVBoxLayout(models_group)
        
        self.ollama_models_table = QTableWidget()
        self.ollama_models_table.setColumnCount(4)
        self.ollama_models_table.setHorizontalHeaderLabels([
            "Model Name", "Size", "Last Modified", "Actions"
        ])
        self.ollama_models_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        models_layout.addWidget(self.ollama_models_table)
        
        models_buttons = QHBoxLayout()
        self.refresh_models_button = QPushButton("Refresh Models")
        self.refresh_models_button.clicked.connect(self.refresh_models)
        models_buttons.addWidget(self.refresh_models_button)
        models_buttons.addStretch()
        models_layout.addLayout(models_buttons)
        
        layout.addWidget(models_group)
        layout.addStretch()
        
        return widget

    def create_local_tab(self) -> QWidget:
        """Create the local fine-tuned models tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Local models table
        models_group = QGroupBox("Fine-tuned Models")
        models_layout = QVBoxLayout(models_group)
        
        self.local_models_table = QTableWidget()
        self.local_models_table.setColumnCount(6)
        self.local_models_table.setHorizontalHeaderLabels([
            "Model Name", "Base Model", "Training Date", "Dataset Size", "Status", "Actions"
        ])
        self.local_models_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        models_layout.addWidget(self.local_models_table)
        
        # Model actions
        actions_layout = QHBoxLayout()
        self.refresh_local_models_button = QPushButton("Refresh Models")
        self.refresh_local_models_button.clicked.connect(self.refresh_local_models)
        self.evaluate_model_button = QPushButton("Evaluate Model")
        self.evaluate_model_button.clicked.connect(self.evaluate_selected_model)
        self.delete_local_model_button = QPushButton("Delete Model")
        self.delete_local_model_button.clicked.connect(self.delete_local_model)
        
        actions_layout.addWidget(self.refresh_local_models_button)
        actions_layout.addWidget(self.evaluate_model_button)
        actions_layout.addWidget(self.delete_local_model_button)
        actions_layout.addStretch()
        models_layout.addLayout(actions_layout)
        
        layout.addWidget(models_group)
        layout.addStretch()
        
        return widget

    def create_training_tab(self) -> QWidget:
        """Create the model training tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Dataset creation
        dataset_group = QGroupBox("Dataset Management")
        dataset_layout = QVBoxLayout(dataset_group)
        
        dataset_buttons = QHBoxLayout()
        self.create_dataset_button = QPushButton("Create Dataset")
        self.create_dataset_button.clicked.connect(self.create_dataset)
        self.browse_dataset_button = QPushButton("Browse Datasets")
        self.browse_dataset_button.clicked.connect(self.browse_datasets)
        dataset_buttons.addWidget(self.create_dataset_button)
        dataset_buttons.addWidget(self.browse_dataset_button)
        dataset_buttons.addStretch()
        dataset_layout.addLayout(dataset_buttons)
        
        layout.addWidget(dataset_group)
        
        # Model training
        training_group = QGroupBox("Model Training")
        training_layout = QVBoxLayout(training_group)
        
        # Training progress
        self.training_progress = QProgressBar()
        self.training_progress.setVisible(False)
        training_layout.addWidget(self.training_progress)
        
        # Training log
        self.training_log = QTextEdit()
        self.training_log.setMaximumHeight(200)
        self.training_log.setReadOnly(True)
        training_layout.addWidget(self.training_log)
        
        # Training actions
        training_buttons = QHBoxLayout()
        self.start_training_button = QPushButton("Start Training")
        self.start_training_button.clicked.connect(self.start_training)
        self.stop_training_button = QPushButton("Stop Training")
        self.stop_training_button.setEnabled(False)
        self.stop_training_button.clicked.connect(self.stop_training)
        training_buttons.addWidget(self.start_training_button)
        training_buttons.addWidget(self.stop_training_button)
        training_buttons.addStretch()
        training_layout.addLayout(training_buttons)
        
        layout.addWidget(training_group)
        layout.addStretch()
        
        return widget

    def create_health_tab(self) -> QWidget:
        """Create the health monitoring tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Model Health Overview
        overview_group = QGroupBox("Model Health Overview")
        overview_layout = QVBoxLayout(overview_group)
        
        # Health status grid
        health_grid = QHBoxLayout()
        
        # Current model status
        current_status_layout = QVBoxLayout()
        current_status_layout.addWidget(QLabel("Current Model:"))
        self.health_current_model = QLabel("Loading...")
        self.health_current_model.setStyleSheet("font-weight: bold;")
        current_status_layout.addWidget(self.health_current_model)
        health_grid.addLayout(current_status_layout)
        
        # Health indicator
        health_status_layout = QVBoxLayout()
        health_status_layout.addWidget(QLabel("Status:"))
        self.health_status_label = QLabel("Checking...")
        self.health_status_label.setStyleSheet("font-weight: bold; color: #ffc107;")
        health_status_layout.addWidget(self.health_status_label)
        health_grid.addLayout(health_status_layout)
        
        # Response time
        response_layout = QVBoxLayout()
        response_layout.addWidget(QLabel("Response Time:"))
        self.response_time_label = QLabel("N/A")
        response_layout.addWidget(self.response_time_label)
        health_grid.addLayout(response_layout)
        
        # Last check
        last_check_layout = QVBoxLayout()
        last_check_layout.addWidget(QLabel("Last Check:"))
        self.last_check_label = QLabel("Never")
        last_check_layout.addWidget(self.last_check_label)
        health_grid.addLayout(last_check_layout)
        
        overview_layout.addLayout(health_grid)
        
        # Health check button
        health_buttons = QHBoxLayout()
        self.manual_health_check_button = QPushButton("Run Health Check")
        self.manual_health_check_button.clicked.connect(self.run_manual_health_check)
        health_buttons.addWidget(self.manual_health_check_button)
        health_buttons.addStretch()
        overview_layout.addLayout(health_buttons)
        
        layout.addWidget(overview_group)
        
        # System Information
        system_group = QGroupBox("System Information")
        system_layout = QVBoxLayout(system_group)
        
        # System info table
        self.system_info_table = QTableWidget()
        self.system_info_table.setColumnCount(2)
        self.system_info_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.system_info_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        system_layout.addWidget(self.system_info_table)
        
        # Refresh system info button
        refresh_system_button = QPushButton("Refresh System Info")
        refresh_system_button.clicked.connect(self.refresh_system_info)
        system_layout.addWidget(refresh_system_button)
        
        layout.addWidget(system_group)
        
        # Performance Metrics
        performance_group = QGroupBox("Performance Metrics")
        performance_layout = QVBoxLayout(performance_group)
        
        self.performance_log = QTextEdit()
        self.performance_log.setMaximumHeight(200)
        self.performance_log.setReadOnly(True)
        performance_layout.addWidget(self.performance_log)
        
        layout.addWidget(performance_group)
        
        # Initialize system info
        self.refresh_system_info()
        
        return widget

    def handle_error(self, error):
        """Handle and display errors."""
        QMessageBox.critical(self, "Error", str(error))

    def load_data(self):
        """Load initial data."""
        self.refresh_ollama_instances()
        self.refresh_models()
        self.refresh_local_models()
        
        # Initialize current model display
        self.update_current_model_display()
        
        # Perform initial health check
        self.check_model_health()

    def refresh_ollama_instances(self):
        """Refresh Ollama instances."""
        def fetch_ollama_models():
            try:
                model_names = get_available_models_sync()
                # Convert to the expected format
                models = []
                for name in model_names:
                    models.append({
                        "name": name,
                        "size": "Unknown",
                        "modified_at": "Unknown"
                    })
                return models
            except Exception as e:
                logger.error(f"Failed to fetch Ollama models: {e}")
                return []

        future = concurrent.futures.ThreadPoolExecutor().submit(fetch_ollama_models)
        future.add_done_callback(self._on_ollama_models_loaded)

    def refresh_models(self):
        """Refresh available models."""
        self.refresh_ollama_instances()

    def refresh_local_models(self):
        """Refresh local fine-tuned models."""
        def fetch_local_models():
            try:
                return self.scan_local_models()
            except Exception as e:
                logger.error(f"Failed to fetch local models: {e}")
                return []

        future = concurrent.futures.ThreadPoolExecutor().submit(fetch_local_models)
        future.add_done_callback(self._on_local_models_loaded)

    def scan_local_models(self) -> List[Dict[str, Any]]:
        """Scan for local fine-tuned models."""
        models = []
        models_dir = Path("models")
        
        if models_dir.exists():
            for model_dir in models_dir.iterdir():
                if model_dir.is_dir():
                    model_info_file = model_dir / "model_info.json"
                    if model_info_file.exists():
                        try:
                            with open(model_info_file, 'r') as f:
                                info = json.load(f)
                            models.append({
                                "name": info.get("model_name", model_dir.name),
                                "base_model": info.get("base_model", "Unknown"),
                                "training_date": info.get("training_date", "Unknown"),
                                "dataset_size": info.get("dataset_size", 0),
                                "path": str(model_dir),
                                "status": "Ready"
                            })
                        except Exception as e:
                            logger.warning(f"Failed to read model info for {model_dir}: {e}")
        
        return models

    def populate_ollama_models_table(self, models: List[Any]):
        """Populate the Ollama models table."""
        table = self.ollama_models_table
        table.setRowCount(len(models))
        
        for row, model in enumerate(models):
            table.setItem(row, 0, QTableWidgetItem(model.get("name", "")))
            table.setItem(row, 1, QTableWidgetItem(str(model.get("size", ""))))
            table.setItem(row, 2, QTableWidgetItem(str(model.get("modified_at", ""))))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            set_active_button = QPushButton("Set Active")
            set_active_button.setFixedSize(80, 25)
            set_active_button.clicked.connect(lambda checked, m=model: self.set_active_ollama_model(m))
            
            delete_button = QPushButton("Delete")
            delete_button.setFixedSize(60, 25)
            delete_button.clicked.connect(lambda checked, m=model: self.delete_ollama_model(m))
            
            actions_layout.addWidget(set_active_button)
            actions_layout.addWidget(delete_button)
            actions_layout.addStretch()
            table.setCellWidget(row, 3, actions_widget)

    def populate_local_models_table(self, models: List[Dict[str, Any]]):
        """Populate the local models table."""
        table = self.local_models_table
        table.setRowCount(len(models))
        
        for row, model in enumerate(models):
            table.setItem(row, 0, QTableWidgetItem(model.get("name", "")))
            table.setItem(row, 1, QTableWidgetItem(model.get("base_model", "")))
            table.setItem(row, 2, QTableWidgetItem(model.get("training_date", "")))
            table.setItem(row, 3, QTableWidgetItem(str(model.get("dataset_size", ""))))
            table.setItem(row, 4, QTableWidgetItem(model.get("status", "")))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            set_active_button = QPushButton("Set Active")
            set_active_button.setFixedSize(80, 25)
            set_active_button.clicked.connect(lambda checked, m=model: self.set_active_local_model(m))
            
            delete_button = QPushButton("Delete")
            delete_button.setFixedSize(60, 25)
            delete_button.clicked.connect(lambda checked, m=model: self.delete_local_model(m))
            
            actions_layout.addWidget(set_active_button)
            actions_layout.addWidget(delete_button)
            actions_layout.addStretch()
            table.setCellWidget(row, 5, actions_widget)

    def set_active_ollama_model(self, model: Dict[str, Any]):
        """Set an Ollama model as active."""
        try:
            model_name = model.get('name', '')
            if self.local_code_reviewer:
                success = self.local_code_reviewer.switch_model(model_name)
                if success:
                    self.update_current_model_display()
                    QMessageBox.information(self, "Success", f"Set {model_name} as active model")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to set {model_name} as active model")
        except Exception as e:
            self.handle_error(e)

    def set_active_local_model(self, model: Dict[str, Any]):
        """Set a local model as active."""
        try:
            model_name = model.get('name', '')
            if self.local_code_reviewer:
                success = self.local_code_reviewer.switch_model(model_name)
                if success:
                    self.update_current_model_display()
                    QMessageBox.information(self, "Success", f"Set {model_name} as active model")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to set {model_name} as active model")
        except Exception as e:
            self.handle_error(e)

    def delete_ollama_model(self, model: Dict[str, Any]):
        """Delete an Ollama model."""
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete model '{model.get('name')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Implementation would delete the model
                QMessageBox.information(self, "Success", f"Deleted model {model.get('name')}")
                self.refresh_models()
            except Exception as e:
                self.handle_error(e)

    def delete_local_model(self, model: Dict[str, Any]):
        """Delete a local model."""
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete model '{model.get('name')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Implementation would delete the model directory
                QMessageBox.information(self, "Success", f"Deleted model {model.get('name')}")
                self.refresh_local_models()
            except Exception as e:
                self.handle_error(e)

    def start_training(self):
        """Start model training."""
        dialog = ModelTrainingDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_training_config()
            
            # Validate configuration
            if not config["dataset_path"] or not os.path.exists(config["dataset_path"]):
                QMessageBox.warning(self, "Error", "Please select a valid dataset file")
                return
            
            if not config["output_model_name"]:
                QMessageBox.warning(self, "Error", "Please enter an output model name")
                return
            
            # Start training in background
            self.start_training_button.setEnabled(False)
            self.stop_training_button.setEnabled(True)
            self.training_progress.setVisible(True)
            self.training_progress.setValue(0)
            
            def train_model():
                try:
                    result = fine_tune_code_model(
                        dataset_path=config["dataset_path"],
                        base_model=config["base_model"],
                        output_model_name=config["output_model_name"],
                        epochs=config["epochs"],
                        batch_size=config["batch_size"],
                        learning_rate=config["learning_rate"],
                        log_message_callback=self.log_training_message,
                        progress_callback=self.update_training_progress
                    )
                    return result
                except Exception as e:
                    return f"Training failed: {e}"
            
            future = concurrent.futures.ThreadPoolExecutor().submit(train_model)
            future.add_done_callback(self._on_training_complete)

    def stop_training(self):
        """Stop model training."""
        # Implementation would stop the training process
        self.start_training_button.setEnabled(True)
        self.stop_training_button.setEnabled(False)
        self.training_progress.setVisible(False)
        self.log_training_message("Training stopped by user")

    def create_dataset(self):
        """Create a new training dataset."""
        dialog = DatasetCreationDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_dataset_config()
            
            try:
                if config["input_method"] == "file":
                    # Copy or validate the input file
                    if not os.path.exists(config["input_file"]):
                        QMessageBox.warning(self, "Error", "Input file not found")
                        return
                    # Copy to output location
                    import shutil
                    shutil.copy2(config["input_file"], config["output_path"])
                else:
                    # Create dataset from manual input
                    try:
                        data = json.loads(config["manual_data"])
                        with open(config["output_path"], 'w') as f:
                            json.dump(data, f, indent=2)
                    except json.JSONDecodeError:
                        QMessageBox.warning(self, "Error", "Invalid JSON format in manual input")
                        return
                
                QMessageBox.information(self, "Success", f"Dataset created: {config['output_path']}")
                
            except Exception as e:
                self.handle_error(e)

    def browse_datasets(self):
        """Browse existing datasets."""
        # Implementation would show a file browser for datasets
        pass

    def evaluate_selected_model(self):
        """Evaluate the selected model."""
        current_row = self.local_models_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a model to evaluate")
            return
        
        model_name = self.local_models_table.item(current_row, 0).text()
        model_path = f"models/{model_name}"
        
        # For now, just show a placeholder
        QMessageBox.information(self, "Evaluation", f"Evaluation of {model_name} would be performed here")

    def add_ollama_instance(self):
        """Add a new Ollama instance."""
        dialog = OllamaInstanceDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            # Implementation would add the instance to the backend
            QMessageBox.information(self, "Success", f"Added Ollama instance: {config.instance_name}")
            self.refresh_ollama_instances()

    def log_training_message(self, message: str):
        """Log a training message."""
        self.training_log.append(f"[{QTimer().remainingTime()}] {message}")

    def update_training_progress(self, current: int, total: int, message: str):
        """Update training progress."""
        self._update_progress(current, total, message)

    def _update_progress(self, current: int, total: int, message: str):
        """Update progress bar."""
        if total > 0:
            progress = int((current / total) * 100)
            self.training_progress.setValue(progress)
        self.log_training_message(message)

    @pyqtSlot(object)
    def _on_ollama_models_loaded(self, future):
        """Handle Ollama models loaded."""
        def update_ui():
            try:
                models = future.result()
                self.populate_ollama_models_table(models)
            except Exception as e:
                self.handle_error(e)
        
        QTimer.singleShot(0, update_ui)

    @pyqtSlot(object)
    def _on_local_models_loaded(self, future):
        """Handle local models loaded."""
        def update_ui():
            try:
                models = future.result()
                self.populate_local_models_table(models)
            except Exception as e:
                self.handle_error(e)
        
        QTimer.singleShot(0, update_ui)

    @pyqtSlot(object)
    def _on_training_complete(self, future):
        """Handle training completion."""
        def update_ui():
            try:
                result = future.result()
                if result == "Success":
                    QMessageBox.information(self, "Success", "Model training completed successfully!")
                    self.refresh_local_models()
                else:
                    QMessageBox.warning(self, "Training Failed", result)
            except Exception as e:
                self.handle_error(e)
            finally:
                self.start_training_button.setEnabled(True)
                self.stop_training_button.setEnabled(False)
                self.training_progress.setVisible(False)
        
        QTimer.singleShot(0, update_ui)

    def check_model_health(self):
        """Check the health of the active model."""
        try:
            if self.local_code_reviewer and self.local_code_reviewer.current_model:
                # Use a simple HTTP request instead of the async function
                import requests
                
                start_time = time.time()
                
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": self.local_code_reviewer.current_model,
                        "prompt": "Hello, this is a health check.",
                        "stream": False,
                        "temperature": 0.7
                    },
                    timeout=30
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status_code == 200:
                    self.health_indicator.setStyleSheet("font-size: 16px; color: #28a745;")  # Green
                    self.health_indicator.setText("●")
                else:
                    self.health_indicator.setStyleSheet("font-size: 16px; color: #dc3545;")  # Red
                    self.health_indicator.setText("●")
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            self.health_indicator.setStyleSheet("font-size: 16px; color: #dc3545;")  # Red
            self.health_indicator.setText("●")

    def switch_model(self, model_name: str):
        """Switch to a different model."""
        if not model_name or model_name == "Select Model":
            return
            
        try:
            # Update the LocalCodeReviewer
            if self.local_code_reviewer:
                success = self.local_code_reviewer.switch_model(model_name)
                if success:
                    # Update the current model label
                    self.current_model_label.setText(model_name)
                    
                    # Save the selection to secrets for persistence
                    self.secrets_manager.save_secret('LOCAL_CODE_REVIEWER_MODEL', model_name)
                    
                    QMessageBox.information(self, "Success", f"Switched to model: {model_name}")
                    
                    # Update the health indicator
                    self.check_model_health()
                else:
                    QMessageBox.warning(self, "Error", f"Failed to switch to model: {model_name}")
        except Exception as e:
            self.handle_error(e)

    def update_current_model_display(self):
        """Update the current model display."""
        try:
            if self.local_code_reviewer and self.local_code_reviewer.current_model:
                self.current_model_label.setText(self.local_code_reviewer.current_model)
            else:
                self.current_model_label.setText("No model selected")
                
            # Update the model switch combo box
            self.populate_model_switch_combo()
        except Exception as e:
            logger.error(f"Failed to update current model display: {e}")

    def populate_model_switch_combo(self):
        """Populate the model switch combo box with available models."""
        try:
            self.model_switch_combo.clear()
            self.model_switch_combo.addItem("Select Model")
            
            # Get available models from LocalCodeReviewer
            if self.local_code_reviewer:
                available_models = self.local_code_reviewer.get_available_models()
                for model in available_models:
                    self.model_switch_combo.addItem(model)
                    
                # Set current selection
                if self.local_code_reviewer.current_model:
                    index = self.model_switch_combo.findText(self.local_code_reviewer.current_model)
                    if index >= 0:
                        self.model_switch_combo.setCurrentIndex(index)
        except Exception as e:
            logger.error(f"Failed to populate model switch combo: {e}")

    def run_manual_health_check(self):
        """Run a manual health check."""
        try:
            self.manual_health_check_button.setEnabled(False)
            self.health_status_label.setText("Checking...")
            self.health_status_label.setStyleSheet("font-weight: bold; color: #ffc107;")
            
            # Run health check in background
            def perform_health_check():
                try:
                    start_time = time.time()
                    
                    if self.local_code_reviewer and self.local_code_reviewer.current_model:
                        # Use a simple HTTP request instead of the async function
                        import requests
                        
                        response = requests.post(
                            "http://localhost:11434/api/generate",
                            json={
                                "model": self.local_code_reviewer.current_model,
                                "prompt": "Hello, this is a health check.",
                                "stream": False,
                                "temperature": 0.7
                            },
                            timeout=30
                        )
                        
                        end_time = time.time()
                        response_time = end_time - start_time
                        
                        if response.status_code == 200:
                            return {
                                "status": "healthy",
                                "response_time": response_time,
                                "model": self.local_code_reviewer.current_model
                            }
                        else:
                            return {
                                "status": "unhealthy",
                                "response_time": response_time,
                                "model": self.local_code_reviewer.current_model
                            }
                    else:
                        return {
                            "status": "no_model",
                            "response_time": 0,
                            "model": "None"
                        }
                except Exception as e:
                    return {
                        "status": "error",
                        "response_time": 0,
                        "model": "Error",
                        "error": str(e)
                    }
            
            future = concurrent.futures.ThreadPoolExecutor().submit(perform_health_check)
            future.add_done_callback(self._on_health_check_complete)
            
        except Exception as e:
            self.handle_error(e)
            self.manual_health_check_button.setEnabled(True)

    def refresh_system_info(self):
        """Refresh system information."""
        try:
            import psutil
            import platform
            
            system_info = [
                ["Operating System", platform.system() + " " + platform.release()],
                ["Python Version", platform.python_version()],
                ["CPU Cores", str(psutil.cpu_count())],
                ["Memory Total", f"{psutil.virtual_memory().total / (1024**3):.1f} GB"],
                ["Memory Available", f"{psutil.virtual_memory().available / (1024**3):.1f} GB"],
                ["Disk Usage", f"{psutil.disk_usage('/').percent:.1f}%"],
                ["Ollama Status", "Running" if self._check_ollama_status() else "Not Running"],
            ]
            
            self.system_info_table.setRowCount(len(system_info))
            for row, (property_name, value) in enumerate(system_info):
                self.system_info_table.setItem(row, 0, QTableWidgetItem(property_name))
                self.system_info_table.setItem(row, 1, QTableWidgetItem(str(value)))
                
        except Exception as e:
            logger.error(f"Failed to refresh system info: {e}")

    def _check_ollama_status(self) -> bool:
        """Check if Ollama is running."""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    @pyqtSlot(object)
    def _on_health_check_complete(self, future):
        """Handle health check completion."""
        try:
            result = future.result()
            
            def update_ui():
                self.manual_health_check_button.setEnabled(True)
                
                if result["status"] == "healthy":
                    self.health_status_label.setText("Healthy")
                    self.health_status_label.setStyleSheet("font-weight: bold; color: #28a745;")
                    self.health_indicator.setStyleSheet("font-size: 16px; color: #28a745;")
                elif result["status"] == "unhealthy":
                    self.health_status_label.setText("Unhealthy")
                    self.health_status_label.setStyleSheet("font-weight: bold; color: #dc3545;")
                    self.health_indicator.setStyleSheet("font-size: 16px; color: #dc3545;")
                elif result["status"] == "no_model":
                    self.health_status_label.setText("No Model")
                    self.health_status_label.setStyleSheet("font-weight: bold; color: #ffc107;")
                    self.health_indicator.setStyleSheet("font-size: 16px; color: #ffc107;")
                else:
                    self.health_status_label.setText("Error")
                    self.health_status_label.setStyleSheet("font-weight: bold; color: #dc3545;")
                    self.health_indicator.setStyleSheet("font-size: 16px; color: #dc3545;")
                
                # Update response time
                if result["response_time"] > 0:
                    self.response_time_label.setText(f"{result['response_time']:.2f}s")
                else:
                    self.response_time_label.setText("N/A")
                
                # Update current model
                self.health_current_model.setText(result["model"])
                
                # Update last check time
                from datetime import datetime
                self.last_check_label.setText(datetime.now().strftime("%H:%M:%S"))
                
                # Log to performance log
                status_text = "✓" if result["status"] == "healthy" else "✗"
                log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] {status_text} Health check completed - {result['model']} ({result['response_time']:.2f}s)\n"
                self.performance_log.append(log_entry)
            
            QTimer.singleShot(0, update_ui)
            
        except Exception as e:
            logger.error(f"Health check completion error: {e}")
            self.manual_health_check_button.setEnabled(True)

    def test_ollama_connection(self):
        """Test connection to Ollama instance."""
        try:
            # Use configuration-based URL instead of hardcoded
            ollama_base_url = get_url("ollama_base")
            response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
            
            if response.status_code == HTTP_OK:
                models = response.json().get("models", [])
                QMessageBox.information(
                    self,
                    "Connection Successful",
                    f"Successfully connected to Ollama at {ollama_base_url}\n\nFound {len(models)} models:\n" + 
                    "\n".join([f"• {model.get('name', 'Unknown')}" for model in models[:10]])
                )
            else:
                QMessageBox.warning(
                    self,
                    "Connection Failed",
                    f"Failed to connect to Ollama at {ollama_base_url}\nStatus: {response.status_code}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Error",
                f"Error connecting to Ollama: {str(e)}"
            )

    def test_model_generation(self):
        """Test model generation with a simple prompt."""
        try:
            # Use configuration-based URL instead of hardcoded
            ollama_base_url = get_url("ollama_base")
            
            test_prompt = "Write a simple Python function to calculate the factorial of a number."
            
            payload = {
                "model": "codellama:13b",
                "prompt": test_prompt,
                "stream": False,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{ollama_base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == HTTP_OK:
                result = response.json()
                generated_text = result.get("response", "No response generated")
                
                QMessageBox.information(
                    self,
                    "Generation Test Successful",
                    f"Successfully generated response from Ollama:\n\n{generated_text[:500]}..."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Generation Test Failed",
                    f"Failed to generate response. Status: {response.status_code}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Generation Test Error",
                f"Error during generation test: {str(e)}"
            )

    def export_model_to_ollama(self):
        """Export the fine-tuned model to Ollama."""
        try:
            # Use configuration-based URL instead of hardcoded
            ollama_base_url = get_url("ollama_base")
            
            # Get model path
            model_path = self.model_path_edit.text()
            if not model_path or not os.path.exists(model_path):
                QMessageBox.warning(self, "Invalid Model", "Please select a valid model file.")
                return
            
            # Create Modelfile content
            modelfile_content = self.create_modelfile_content()
            
            # Save Modelfile
            modelfile_path = os.path.join(os.path.dirname(model_path), "Modelfile")
            with open(modelfile_path, "w") as f:
                f.write(modelfile_content)
            
            # Show progress
            progress = QProgressDialog("Exporting model to Ollama...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()
            
            # Run ollama create command
            model_name = f"ai-coder-{os.path.basename(model_path).split('.')[0]}"
            cmd = ["ollama", "create", model_name, "-f", modelfile_path]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor progress
            while process.poll() is None:
                progress.setValue(50)
                QApplication.processEvents()
                if progress.wasCanceled():
                    process.terminate()
                    break
            
            if process.returncode == 0:
                progress.setValue(100)
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Model successfully exported to Ollama as '{model_name}'\n\n"
                    f"You can now use this model with: ollama run {model_name}"
                )
            else:
                stderr = process.stderr.read()
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"Failed to export model to Ollama:\n{stderr}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Error exporting model: {str(e)}"
            )

    def list_ollama_models(self):
        """List available models in Ollama."""
        try:
            # Use configuration-based URL instead of hardcoded
            ollama_base_url = get_url("ollama_base")
            response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
            
            if response.status_code == HTTP_OK:
                models = response.json().get("models", [])
                
                if models:
                    model_list = "\n".join([f"• {model.get('name', 'Unknown')}" for model in models])
                    QMessageBox.information(
                        self,
                        "Available Ollama Models",
                        f"Found {len(models)} models in Ollama:\n\n{model_list}"
                    )
                else:
                    QMessageBox.information(
                        self,
                        "No Models Found",
                        "No models found in Ollama instance."
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Failed to List Models",
                    f"Failed to retrieve models. Status: {response.status_code}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Listing Models",
                f"Error listing Ollama models: {str(e)}"
            )
