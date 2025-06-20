"""
ollama_export_tab.py

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

import os
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QPushButton, QTextEdit, QMessageBox, QWidget, QComboBox, QProgressDialog)
import requests
from typing import Any
from PyQt6.QtWidgets import QApplication
import concurrent.futures

from backend.utils.constants import HTTP_TIMEOUT_SHORT, HTTP_TIMEOUT_LONG, HTTP_OK, STATUS_BOX_MIN_HEIGHT
from backend.utils.constants import OLLAMA_BASE_URL

def is_ollama_running() -> bool:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=HTTP_TIMEOUT_SHORT)
        return response.status_code == HTTP_OK
    except requests.exceptions.ConnectionError:
        return False
    except Exception as e:
        print(f"Error checking Ollama status: {e}")
        return False

def find_llama_cpp() -> str | None:
    """Finds the llama.cpp directory containing convert_hf_to_gguf.py, prioritizing stability."""
    # 1. Try LLAMA_CPP_PATH environment variable
    env_path = os.environ.get("LLAMA_CPP_PATH")
    if env_path and os.path.exists(os.path.join(env_path, "convert_hf_to_gguf.py")):
        return env_path

    # 2. Try common relative paths within the current project folder (non-recursive)
    project_root = os.path.abspath(os.path.dirname(__file__))
    # Go up from src/ui to project root
    project_root = os.path.abspath(os.path.join(project_root, "..", ".."))

    for candidate_relative in ["llama.cpp", os.path.join("..", "llama.cpp")]:
        candidate_path = os.path.join(project_root, candidate_relative)
        if os.path.exists(os.path.join(candidate_path, "convert_hf_to_gguf.py")):
            return candidate_path

    # 3. Try very specific, non-recursive common locations in the home directory
    home = os.path.expanduser("~")
    common_home_paths = [
        os.path.join(home, "llama.cpp"),
        os.path.join(home, "projects", "llama.cpp"),
        os.path.join(home, "dev", "llama.cpp"),
        os.path.join(home, "git", "llama.cpp"),
    ]
    for path in common_home_paths:
        if os.path.exists(os.path.join(path, "convert_hf_to_gguf.py")):
            return path

    # If not found in any of the above safe locations, return None
    return None

def get_ollama_models() -> list[str]:
    """Fetch the list of models from the local Ollama instance."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=HTTP_TIMEOUT_LONG)
        if resp.status_code == HTTP_OK:
            data = resp.json()
            return [m['name'] for m in data.get('models', [])]
        else:
            return []
    except Exception:
        return []

def setup_ollama_export_tab(parent_widget: QWidget, main_app_instance: Any):
    layout = QVBoxLayout(parent_widget)
    title = QLabel("Export Local Model to Ollama")
    title.setStyleSheet("font-weight: bold; font-size: 16px;")
    layout.addWidget(title)

    info = QLabel("""
This tool will export your locally trained model (HuggingFace format) to GGUF and create an enhanced Ollama model.
- The GGUF export requires llama.cpp's conversion script (convert_hf_to_gguf.py).
- An enhanced Ollama model will be created that extends your selected base model with custom parameters and system prompts.
- The enhanced model can be used for improved code suggestions in the AI Agent tab.
    """)
    info.setWordWrap(True)
    layout.addWidget(info)

    # Model selection
    model_label = QLabel("Select Ollama Model to Feed Knowledge:")
    layout.addWidget(model_label)
    model_selector = QComboBox()
    model_selector.addItem("(Click 'Refresh Models' to load)")
    layout.addWidget(model_selector)

    # Add a refresh button
    refresh_button = QPushButton("Refresh Models")
    layout.addWidget(refresh_button)

    status_box = QTextEdit()
    status_box.setReadOnly(True)
    status_box.setMinimumHeight(STATUS_BOX_MIN_HEIGHT)
    layout.addWidget(status_box)

    export_button = QPushButton("Export & Send to Ollama")
    layout.addWidget(export_button)

    def log(msg: str):
        status_box.append(msg)

    def refresh_models():
        model_selector.clear()
        log("Fetching available models from Ollama...")
        models = get_ollama_models()
        if not models:
            model_selector.addItem("(No models found)")
            log("No models found on Ollama or Ollama is not running.")
        else:
            for m in models:
                model_selector.addItem(m)
            log(f"Found {len(models)} model(s) on Ollama.")

    # Connect the refresh button instead of auto-refreshing
    refresh_button.clicked.connect(refresh_models)

    def start_export():
        progress_dialog = QProgressDialog("Exporting model to Ollama...", "Cancel", 0, 0, parent_widget)
        progress_dialog.setWindowTitle("Ollama Export Progress")
        progress_dialog.setAutoClose(False)
        progress_dialog.setAutoReset(False)
        progress_dialog.show()
        # Keep a reference to the worker to prevent GC
        parent_widget.ollama_export_worker = OllamaExportWorker(parent_widget, model_selector, status_box)
        worker = parent_widget.ollama_export_worker
        def on_progress(msg):
            status_box.append(msg)
            QApplication.processEvents()
        def on_finished(msg):
            progress_dialog.close()
            status_box.append(msg)
            QMessageBox.information(parent_widget, "Export Complete", msg)
            parent_widget.ollama_export_worker = None
        def on_error(msg):
            progress_dialog.close()
            status_box.append(msg)
            QMessageBox.critical(parent_widget, "Export Failed", msg)
            parent_widget.ollama_export_worker = None
        worker.progress.connect(on_progress)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        progress_dialog.canceled.connect(worker.cancel)
        worker.start()
    export_button.clicked.connect(start_export)

# Stub class for OllamaExportWorker
class OllamaExportWorker:
    """Stub class for Ollama export worker."""
    def __init__(self, parent_widget, model_selector, status_box):
        self.parent_widget = parent_widget
        self.model_selector = model_selector
        self.status_box = status_box

class OllamaExportTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.setup_ui() 