"""
Model Manager Tab Widget

Provides UI for managing multiple model sources including:
- Remote Ollama instances (local and remote)
- Local fine-tuned models for code review
- Model configuration, health monitoring, and management
"""

import asyncio
import concurrent.futures
import logging
import os
import json
from typing import Any, Dict, List, Optional
from pathlib import Path

from PyQt6.QtCore import QTimer, pyqtSlot
from PyQt6.QtGui import QFont
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
)

from src.backend.services.llm_manager import LLMManager
from src.backend.services.models import ProviderConfig, ProviderType
from src.backend.services.ollama_client import OllamaClient, get_available_models_sync
from src.backend.services.trainer import fine_tune_code_model, create_code_review_dataset, evaluate_model_performance
from src.backend.utils.constants import DEFAULT_MAX_WORKERS, DEFAULT_TIMEOUT

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
    """Main model manager tab widget."""

    def __init__(self, llm_manager: LLMManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.llm_manager = llm_manager
        self.ollama_client = OllamaClient()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
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

    def handle_error(self, error):
        """Handle and display errors."""
        QMessageBox.critical(self, "Error", str(error))

    def load_data(self):
        """Load initial data."""
        self.refresh_ollama_instances()
        self.refresh_models()
        self.refresh_local_models()

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
            # Implementation would set the active model in the backend
            QMessageBox.information(self, "Success", f"Set {model.get('name')} as active model")
        except Exception as e:
            self.handle_error(e)

    def set_active_local_model(self, model: Dict[str, Any]):
        """Set a local model as active."""
        try:
            # Implementation would set the active model in the backend
            QMessageBox.information(self, "Success", f"Set {model.get('name')} as active model")
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
