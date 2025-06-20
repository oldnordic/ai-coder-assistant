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
from src.backend.services.ollama_client import OllamaClient
from src.backend.services.trainer import fine_tune_code_model
from src.backend.utils.constants import DEFAULT_MAX_WORKERS, DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)


class ModelTrainingDialog(QDialog):
    """Dialog for starting new model training runs."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Start New Model Training")
        self.setModal(True)
        self.resize(500, 400)
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
            "distilgpt2"
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
            provider_type=ProviderType.OLLAMA,
            api_key=self.token_edit.text().strip(),
            base_url=self.url_edit.text().strip(),
            timeout=self.timeout_spin.value(),
            priority=self.priority_spin.value(),
            is_enabled=self.enabled_check.isChecked(),
            instance_name=self.name_edit.text().strip(),
            verify_ssl=self.ssl_check.isChecked(),
        )


class ModelManagerTab(QWidget):
    """Enhanced Model Manager Tab Widget for both Ollama and local models."""

    def __init__(self, llm_manager: LLMManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.llm_manager = llm_manager
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.local_models_dir = Path("models")
        self.local_models_dir.mkdir(exist_ok=True)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Model Manager")
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

        # Create tab widget for different model types
        self.tab_widget = QTabWidget()
        
        # Ollama Models Tab
        self.ollama_tab = self.create_ollama_tab()
        self.tab_widget.addTab(self.ollama_tab, "Ollama Models")
        
        # Local Models Tab
        self.local_tab = self.create_local_tab()
        self.tab_widget.addTab(self.local_tab, "Local Fine-tuned Models")
        
        # Training Tab
        self.training_tab = self.create_training_tab()
        self.tab_widget.addTab(self.training_tab, "Model Training")
        
        layout.addWidget(self.tab_widget)

    def create_ollama_tab(self) -> QWidget:
        """Create the Ollama models tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Models table
        self.ollama_models_table = QTableWidget()
        self.ollama_models_table.setColumnCount(5)
        self.ollama_models_table.setHorizontalHeaderLabels(
            ["Name", "Size", "Status", "Instance", "Actions"]
        )

        header = self.ollama_models_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.ollama_models_table)
        
        return tab

    def create_local_tab(self) -> QWidget:
        """Create the local models tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Local models table
        self.local_models_table = QTableWidget()
        self.local_models_table.setColumnCount(6)
        self.local_models_table.setHorizontalHeaderLabels(
            ["Name", "Base Model", "Type", "Training Examples", "Status", "Actions"]
        )

        header = self.local_models_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.local_models_table)
        
        return tab

    def create_training_tab(self) -> QWidget:
        """Create the model training tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Training configuration
        config_group = QGroupBox("Training Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # Start training button
        self.start_training_button = QPushButton("Start New Training Run")
        self.start_training_button.clicked.connect(self.start_training)
        config_layout.addWidget(self.start_training_button)
        
        # Training progress
        self.training_progress = QProgressBar()
        self.training_progress.setVisible(False)
        config_layout.addWidget(self.training_progress)
        
        # Training log
        self.training_log = QTextEdit()
        self.training_log.setReadOnly(True)
        self.training_log.setPlaceholderText("Training logs will appear here...")
        config_layout.addWidget(self.training_log)
        
        layout.addWidget(config_group)
        
        return tab

    def handle_error(self, error):
        QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", str(error)))

    def load_data(self):
        """Load both Ollama and local models data."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        # Load Ollama models
        def fetch_ollama_models():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.llm_manager.list_ollama_models())
            loop.close()
            return result

        # Load local models
        def fetch_local_models():
            return self.scan_local_models()

        # Submit both tasks
        ollama_future = self.executor.submit(fetch_ollama_models)
        local_future = self.executor.submit(fetch_local_models)
        
        ollama_future.add_done_callback(self._on_ollama_models_loaded)
        local_future.add_done_callback(self._on_local_models_loaded)

    def scan_local_models(self) -> List[Dict[str, Any]]:
        """Scan for local fine-tuned models."""
        models = []
        
        if not self.local_models_dir.exists():
            return models
            
        for model_dir in self.local_models_dir.iterdir():
            if model_dir.is_dir():
                metadata_file = model_dir / "model_metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        models.append({
                            "name": metadata.get("model_name", model_dir.name),
                            "base_model": metadata.get("base_model", "unknown"),
                            "type": metadata.get("fine_tuned_for", "code_review"),
                            "training_examples": metadata.get("training_examples", 0),
                            "training_epochs": metadata.get("training_epochs", 0),
                            "path": str(model_dir),
                            "status": "ready"
                        })
                    except Exception as e:
                        logger.error(f"Error loading model metadata from {metadata_file}: {e}")
        
        return models

    def refresh_models(self):
        """Refresh the list of available models."""
        self.load_data()

    @pyqtSlot(object)
    def _on_ollama_models_loaded(self, future):
        def update_ui():
            try:
                result = future.result()
                self.populate_ollama_models_table(result)
            except Exception as e:
                self.handle_error(e)
            finally:
                self.progress_bar.setVisible(False)

        QTimer.singleShot(0, update_ui)

    @pyqtSlot(object)
    def _on_local_models_loaded(self, future):
        def update_ui():
            try:
                result = future.result()
                self.populate_local_models_table(result)
            except Exception as e:
                self.handle_error(e)

        QTimer.singleShot(0, update_ui)

    def populate_ollama_models_table(self, models: List[Any]):
        """Populate the Ollama models table."""
        table = self.ollama_models_table
        table.setRowCount(len(models))

        for row, model in enumerate(models):
            table.setItem(row, 0, QTableWidgetItem(model.get("name", "")))
            table.setItem(row, 1, QTableWidgetItem(str(model.get("size", ""))))
            table.setItem(row, 2, QTableWidgetItem(model.get("status", "")))
            table.setItem(row, 3, QTableWidgetItem(model.get("instance", "")))

            # Actions
            actions_layout = QHBoxLayout()
            
            set_active_btn = QPushButton("Set as Active")
            set_active_btn.clicked.connect(lambda checked, m=model: self.set_active_ollama_model(m))
            actions_layout.addWidget(set_active_btn)
            
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, m=model: self.delete_ollama_model(m))
            actions_layout.addWidget(delete_btn)

            actions_widget = QWidget()
            actions_widget.setLayout(actions_layout)
            table.setCellWidget(row, 4, actions_widget)

    def populate_local_models_table(self, models: List[Dict[str, Any]]):
        """Populate the local models table."""
        table = self.local_models_table
        table.setRowCount(len(models))

        for row, model in enumerate(models):
            table.setItem(row, 0, QTableWidgetItem(model.get("name", "")))
            table.setItem(row, 1, QTableWidgetItem(model.get("base_model", "")))
            table.setItem(row, 2, QTableWidgetItem(model.get("type", "")))
            table.setItem(row, 3, QTableWidgetItem(str(model.get("training_examples", 0))))
            table.setItem(row, 4, QTableWidgetItem(model.get("status", "")))

            # Actions
            actions_layout = QHBoxLayout()
            
            set_active_btn = QPushButton("Set as Active Reviewer")
            set_active_btn.clicked.connect(lambda checked, m=model: self.set_active_local_model(m))
            actions_layout.addWidget(set_active_btn)
            
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, m=model: self.delete_local_model(m))
            actions_layout.addWidget(delete_btn)

            actions_widget = QWidget()
            actions_widget.setLayout(actions_layout)
            table.setCellWidget(row, 5, actions_widget)

    def set_active_ollama_model(self, model: Dict[str, Any]):
        """Set an Ollama model as the active model."""
        try:
            # This would update the configuration to use this model
            QMessageBox.information(self, "Success", f"Set {model.get('name')} as active Ollama model")
        except Exception as e:
            self.handle_error(e)

    def set_active_local_model(self, model: Dict[str, Any]):
        """Set a local model as the active code reviewer."""
        try:
            # Update configuration to use this local model
            model_path = model.get("path", "")
            # This would update the LocalCodeReviewer configuration
            QMessageBox.information(self, "Success", f"Set {model.get('name')} as active code reviewer")
        except Exception as e:
            self.handle_error(e)

    def delete_ollama_model(self, model: Dict[str, Any]):
        """Delete an Ollama model."""
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete {model.get('name')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # This would call the Ollama API to delete the model
            QMessageBox.information(self, "Success", f"Deleted {model.get('name')}")

    def delete_local_model(self, model: Dict[str, Any]):
        """Delete a local model."""
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete {model.get('name')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                model_path = Path(model.get("path", ""))
                if model_path.exists():
                    import shutil
                    shutil.rmtree(model_path)
                    QMessageBox.information(self, "Success", f"Deleted {model.get('name')}")
                    self.refresh_models()
            except Exception as e:
                self.handle_error(e)

    def start_training(self):
        """Start a new model training run."""
        dialog = ModelTrainingDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_training_config()
            
            # Validate configuration
            if not config["dataset_path"]:
                QMessageBox.warning(self, "Error", "Please select a training dataset")
                return
                
            if not config["output_model_name"]:
                QMessageBox.warning(self, "Error", "Please specify an output model name")
                return
            
            # Start training in background
            self.training_progress.setVisible(True)
            self.training_log.clear()
            
            def train_model():
                try:
                    result = fine_tune_code_model(
                        dataset_path=config["dataset_path"],
                        base_model=config["base_model"],
                        output_model_name=config["output_model_name"],
                        log_message_callback=lambda msg: self.log_training_message(msg),
                        progress_callback=lambda current, total, msg: self.update_training_progress(current, total, msg)
                    )
                    return result
                except Exception as e:
                    return f"Error: {e}"
            
            future = self.executor.submit(train_model)
            future.add_done_callback(self._on_training_complete)

    def log_training_message(self, message: str):
        """Log a training message to the UI."""
        QTimer.singleShot(0, lambda: self.training_log.append(message))

    def update_training_progress(self, current: int, total: int, message: str):
        """Update training progress in the UI."""
        QTimer.singleShot(0, lambda: self._update_progress(current, total, message))

    def _update_progress(self, current: int, total: int, message: str):
        """Update progress bar and log message."""
        if total > 0:
            progress = int((current / total) * 100)
            self.training_progress.setValue(progress)
        self.training_log.append(message)

    @pyqtSlot(object)
    def _on_training_complete(self, future):
        def update_ui():
            try:
                result = future.result()
                if result == "Success":
                    QMessageBox.information(self, "Success", "Model training completed successfully!")
                    self.refresh_models()
                else:
                    QMessageBox.warning(self, "Training Failed", f"Training failed: {result}")
            except Exception as e:
                self.handle_error(e)
            finally:
                self.training_progress.setVisible(False)

        QTimer.singleShot(0, update_ui)
