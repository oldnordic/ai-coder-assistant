"""
studio_ui.py

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
LLM Studio GUI for provider/model management and chat playground (PyQt6 version).
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTabWidget, QComboBox, QTextEdit, QListWidget, QListWidgetItem, QMessageBox, QFormLayout, QInputDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from .llm_manager import LLMManager
from .models import ProviderType, ModelConfig, ProviderConfig, ChatMessage


class LLMStudioUI(QWidget):
    def __init__(self, config_path=None):
        super().__init__()
        self.setWindowTitle("LLM Studio")
        self.resize(700, 500)
        self.manager = LLMManager(config_path)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.addTab(self.provider_tab_ui(), "Providers")
        self.tabs.addTab(self.model_tab_ui(), "Models")
        self.tabs.addTab(self.chat_tab_ui(), "Chat Playground")
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def provider_tab_ui(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.provider_list = QListWidget()
        self.refresh_provider_list()
        layout.addWidget(QLabel("Configured Providers:"))
        layout.addWidget(self.provider_list)
        btns = QHBoxLayout()
        add_btn = QPushButton("Add Provider/API Key")
        add_btn.clicked.connect(self.add_provider_dialog)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_provider)
        test_btn = QPushButton("Test Selected")
        test_btn.clicked.connect(self.test_selected_provider)
        btns.addWidget(add_btn)
        btns.addWidget(remove_btn)
        btns.addWidget(test_btn)
        layout.addLayout(btns)
        widget.setLayout(layout)
        return widget

    def refresh_provider_list(self):
        self.provider_list.clear()
        for pt, pc in self.manager.config.providers.items():
            item = QListWidgetItem(f"{pt.value} | {pc.api_key[:6]}... | Enabled: {pc.is_enabled}")
            item.setData(Qt.ItemDataRole.UserRole, pt)
            self.provider_list.addItem(item)

    def add_provider_dialog(self):
        provider, ok = QInputDialog.getItem(self, "Select Provider", "Provider:",
                                            [pt.value for pt in ProviderType], 0, False)
        if not ok:
            return
        api_key, ok = QInputDialog.getText(self, "API Key", f"Enter API key for {provider}:")
        if not ok or not api_key:
            return
        pt = ProviderType(provider)
        pc = ProviderConfig(provider_type=pt, api_key=api_key)
        try:
            self.manager.add_provider(pc)
            self.refresh_provider_list()
            QMessageBox.information(self, "Success", f"Added provider {provider}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def remove_selected_provider(self):
        item = self.provider_list.currentItem()
        if not item:
            return
        pt = item.data(Qt.ItemDataRole.UserRole)
        self.manager.remove_provider(pt)
        self.refresh_provider_list()

    def test_selected_provider(self):
        item = self.provider_list.currentItem()
        if not item:
            return
        pt = item.data(Qt.ItemDataRole.UserRole)
        pc = self.manager.config.providers[pt]
        class TestThread(QThread):
            result = pyqtSignal(bool)
            def run(self_):
                import asyncio
                ok = asyncio.run(self.manager.test_provider(pt, pc.api_key))
                self_.result.emit(ok)
        thread = TestThread()
        thread.result.connect(lambda ok: QMessageBox.information(self, "Test Result", f"Provider {pt.value}: {'OK' if ok else 'Failed'}"))
        thread.start()

    def model_tab_ui(self):
        widget = QWidget()
        layout = QVBoxLayout()
        self.model_list = QListWidget()
        self.refresh_model_list()
        layout.addWidget(QLabel("Configured Models:"))
        layout.addWidget(self.model_list)
        btns = QHBoxLayout()
        add_btn = QPushButton("Add Model")
        add_btn.clicked.connect(self.add_model_dialog)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_model)
        btns.addWidget(add_btn)
        btns.addWidget(remove_btn)
        layout.addLayout(btns)
        widget.setLayout(layout)
        return widget

    def refresh_model_list(self):
        self.model_list.clear()
        for name, mc in self.manager.config.models.items():
            item = QListWidgetItem(f"{name} | {mc.provider.value} | {mc.model_type.value}")
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.model_list.addItem(item)

    def add_model_dialog(self):
        name, ok = QInputDialog.getText(self, "Model Name", "Enter model name:")
        if not ok or not name:
            return
        provider, ok = QInputDialog.getItem(self, "Provider", "Provider:",
                                            [pt.value for pt in ProviderType], 0, False)
        if not ok:
            return
        # For model_type, use the ModelType enum
        from .models import ModelType
        model_type, ok = QInputDialog.getItem(self, "Model Type", "Type:",
                                              [mt.value for mt in ModelType], 0, False)
        if not ok:
            return
        mc = ModelConfig(name=name, provider=ProviderType(provider), model_type=ModelType(model_type))
        self.manager.add_model(mc)
        self.refresh_model_list()

    def remove_selected_model(self):
        item = self.model_list.currentItem()
        if not item:
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        self.manager.remove_model(name)
        self.refresh_model_list()

    def chat_tab_ui(self):
        widget = QWidget()
        layout = QVBoxLayout()
        form = QFormLayout()
        self.model_combo = QComboBox()
        self.refresh_model_combo()
        form.addRow(QLabel("Model:"), self.model_combo)
        layout.addLayout(form)
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Type your message and press Enter...")
        self.user_input.returnPressed.connect(self.send_chat_message)
        layout.addWidget(self.user_input)
        widget.setLayout(layout)
        return widget

    def refresh_model_combo(self):
        self.model_combo.clear()
        for name in self.manager.config.models:
            self.model_combo.addItem(name)

    def send_chat_message(self):
        user_msg = self.user_input.text().strip()
        if not user_msg:
            return
        model = self.model_combo.currentText()
        self.chat_history.append(f"<b>You:</b> {user_msg}")
        self.user_input.clear()
        class ChatThread(QThread):
            result = pyqtSignal(str)
            def run(self_):
                import asyncio
                try:
                    messages = []
                    system_prompt = self.manager.config.models[model].system_prompt
                    if system_prompt and system_prompt.strip():
                        messages.append(ChatMessage(role="system", content=system_prompt.strip()))
                    messages.append(ChatMessage(role="user", content=user_msg))
                    resp = asyncio.run(self.manager.chat_completion(messages))
                    text = resp.choices[0]["message"]["content"]
                except Exception as e:
                    text = f"Error: {e}"
                self_.result.emit(text)
        thread = ChatThread()
        thread.result.connect(lambda text: self.chat_history.append(f"<b>AI:</b> {text}"))
        thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LLMStudioUI()
    win.show()
    sys.exit(app.exec()) 