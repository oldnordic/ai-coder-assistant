"""
Ollama Manager Tab Widget

Provides UI for managing multiple Ollama instances (local and remote),
including configuration, health monitoring, and model management.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QDialog, QFormLayout, QLineEdit, QCheckBox, QSpinBox, QDialogButtonBox, QLabel, QMessageBox, QTabWidget, QComboBox, QTextEdit, QInputDialog
)
from PyQt6.QtCore import Qt
from backend.services.llm_manager import LLMManager
from backend.services.models import ProviderConfig, ProviderType, ChatMessage, ChatCompletionRequest
import asyncio


class OllamaInstanceDialog(QDialog):
    def __init__(self, parent=None, config: ProviderConfig = None):
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
        self.timeout_spin.setValue(30)
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 10)
        self.priority_spin.setValue(5)
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

class OllamaManagerTab(QWidget):
    """Main Ollama manager tab."""
    
    def __init__(self):
        super().__init__()
        self.llm_manager = LLMManager()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.instances_tab = QWidget()
        self.models_tab = QWidget()
        self.health_tab = QWidget()
        self.init_instances_tab()
        self.init_models_tab()
        self.init_health_tab()
        self.tabs.addTab(self.instances_tab, "Instances")
        self.tabs.addTab(self.models_tab, "Models")
        self.tabs.addTab(self.health_tab, "Health")
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    # --- Instances Tab ---
    def init_instances_tab(self):
        layout = QVBoxLayout()
        self.instances_table = QTableWidget()
        self.instances_table.setColumnCount(6)
        self.instances_table.setHorizontalHeaderLabels([
            "Name", "URL", "Status", "Priority", "Edit", "Delete"
        ])
        layout.addWidget(self.instances_table)
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Instance")
        self.add_btn.clicked.connect(self.add_instance)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        self.instances_tab.setLayout(layout)
        self.refresh_instances()

    def refresh_instances(self):
        instances = self.llm_manager.list_ollama_instances()
        self.instances_table.setRowCount(len(instances))
        for row, config in enumerate(instances):
            self.instances_table.setItem(row, 0, QTableWidgetItem(config.instance_name or ""))
            self.instances_table.setItem(row, 1, QTableWidgetItem(config.base_url or ""))
            status = "Enabled" if config.is_enabled else "Disabled"
            self.instances_table.setItem(row, 2, QTableWidgetItem(status))
            self.instances_table.setItem(row, 3, QTableWidgetItem(str(config.priority)))
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda _, c=config: self.edit_instance(c))
            self.instances_table.setCellWidget(row, 4, edit_btn)
            del_btn = QPushButton("Delete")
            del_btn.clicked.connect(lambda _, c=config: self.delete_instance(c))
            self.instances_table.setCellWidget(row, 5, del_btn)

    def add_instance(self):
        dialog = OllamaInstanceDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            self.llm_manager.add_ollama_instance(config)
            self.refresh_instances()
            self.refresh_models()
            self.refresh_health()

    def edit_instance(self, config: ProviderConfig):
        dialog = OllamaInstanceDialog(self, config)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_config = dialog.get_config()
            self.llm_manager.remove_ollama_instance(config.instance_name)
            self.llm_manager.add_ollama_instance(new_config)
            self.refresh_instances()
            self.refresh_models()
            self.refresh_health()

    def delete_instance(self, config: ProviderConfig):
        reply = QMessageBox.question(self, "Delete Instance", f"Delete '{config.instance_name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.llm_manager.remove_ollama_instance(config.instance_name)
            self.refresh_instances()
            self.refresh_models()
            self.refresh_health()

    # --- Models Tab ---
    def init_models_tab(self):
        layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        self.instance_combo = QComboBox()
        self.instance_combo.currentTextChanged.connect(self.refresh_models)
        top_layout.addWidget(QLabel("Instance:"))
        top_layout.addWidget(self.instance_combo)
        layout.addLayout(top_layout)
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(3)
        self.models_table.setHorizontalHeaderLabels(["Model Name", "Context Length", "Test Chat"])
        layout.addWidget(self.models_table)
        self.models_tab.setLayout(layout)
        self.refresh_models()

    def refresh_models(self):
        instances = self.llm_manager.list_ollama_instances()
        self.instance_combo.blockSignals(True)
        self.instance_combo.clear()
        for config in instances:
            self.instance_combo.addItem(config.instance_name)
        self.instance_combo.blockSignals(False)
        if not instances:
            self.models_table.setRowCount(0)
            return
        instance_name = self.instance_combo.currentText() or instances[0].instance_name
        try:
            models = self.llm_manager.get_ollama_models(instance_name)
        except Exception as e:
            self.models_table.setRowCount(0)
            return
        self.models_table.setRowCount(len(models))
        for row, model in enumerate(models):
            self.models_table.setItem(row, 0, QTableWidgetItem(model.name))
            self.models_table.setItem(row, 1, QTableWidgetItem(str(model.context_length or "?")))
            test_btn = QPushButton("Test Chat")
            test_btn.clicked.connect(lambda _, m=model, i=instance_name: self.test_chat(i, m.name))
            self.models_table.setCellWidget(row, 2, test_btn)

    def test_chat(self, instance_name, model_name):
        prompt, ok = QInputDialog.getText(self, "Test Chat", "Enter prompt:")
        if not ok or not prompt.strip():
            return
        try:
            provider = self.llm_manager.ollama_instances[instance_name]
            request = ChatCompletionRequest(
                messages=[ChatMessage(role="user", content=prompt)],
                model=model_name
            )
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(provider.chat_completion(request))
            loop.close()
            content = response.choices[0]["message"]["content"]
            QMessageBox.information(self, "Chat Result", content)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Chat failed: {e}")

    # --- Health Tab ---
    def init_health_tab(self):
        layout = QVBoxLayout()
        self.health_table = QTableWidget()
        self.health_table.setColumnCount(3)
        self.health_table.setHorizontalHeaderLabels(["Instance", "Status", "Check"])
        layout.addWidget(self.health_table)
        self.health_tab.setLayout(layout)
        self.refresh_health()

    def refresh_health(self):
        instances = self.llm_manager.list_ollama_instances()
        self.health_table.setRowCount(len(instances))
        for row, config in enumerate(instances):
            self.health_table.setItem(row, 0, QTableWidgetItem(config.instance_name or ""))
            status_item = QTableWidgetItem("Unknown")
            self.health_table.setItem(row, 1, status_item)
            check_btn = QPushButton("Check")
            check_btn.clicked.connect(lambda _, c=config: self.check_health(c, row))
            self.health_table.setCellWidget(row, 2, check_btn)

    def check_health(self, config: ProviderConfig, row: int):
        try:
            healthy = self.llm_manager.health_check_ollama(config.instance_name)
            status = "Healthy" if healthy else "Unhealthy"
            item = QTableWidgetItem(status)
            if healthy:
                item.setBackground(Qt.GlobalColor.green)
            else:
                item.setBackground(Qt.GlobalColor.red)
            self.health_table.setItem(row, 1, item)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Health check failed: {e}")
