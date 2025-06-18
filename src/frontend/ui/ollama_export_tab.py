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
import shutil
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QPushButton, QTextEdit, QFileDialog, 
                             QMessageBox, QWidget, QComboBox, QInputDialog, QProgressDialog)
import subprocess
import requests
from typing import Any
import time
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication
import sys

from ...backend.utils.constants import HTTP_TIMEOUT_SHORT, HTTP_TIMEOUT_LONG, HTTP_OK, STATUS_BOX_MIN_HEIGHT
from ...backend.utils import settings
from ...utils.constants import OLLAMA_BASE_URL

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

class OllamaExportWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, parent_widget, model_selector, status_box):
        super().__init__()
        self.parent_widget = parent_widget
        self.model_selector = model_selector
        self.status_box = status_box
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            def log(msg):
                self.progress.emit(msg)
            # Pre-check: Is Ollama running?
            if not is_ollama_running():
                log("Error: Ollama is not running. Please start Ollama before exporting.")
                self.error.emit("Ollama server is not running. Please start it to continue.")
                return
            else:
                log("Ollama server is running.")
            from ...backend.utils import settings
            model_dir = settings.MODEL_SAVE_PATH
            if not os.path.exists(model_dir):
                self.error.emit(f"Model directory not found: {model_dir}")
                return
            log(f"Found local model at: {model_dir}")
            # 2. Ask user for GGUF output path (must be done in main thread, so skip here)
            gguf_path = os.path.join(model_dir, "ai_coder_model.gguf")
            # 3. Auto-detect llama.cpp
            llama_cpp_dir = find_llama_cpp()
            if not llama_cpp_dir:
                log("Could not auto-detect llama.cpp. Please set LLAMA_CPP_PATH environment variable.")
                self.error.emit("Could not auto-detect llama.cpp. Please set LLAMA_CPP_PATH environment variable.")
                return
            log(f"Using llama.cpp at: {llama_cpp_dir}")
            convert_script = os.path.join(llama_cpp_dir, "convert_hf_to_gguf.py")
            if not os.path.exists(convert_script):
                log(f"convert_hf_to_gguf.py not found at {convert_script}.")
                self.error.emit(f"convert_hf_to_gguf.py not found at {convert_script}.")
                return
            # 4. Convert to GGUF using llama.cpp's convert_hf_to_gguf.py
            log("Converting HuggingFace model to GGUF format...")
            try:
                venv_python = sys.executable
                cmd = [
                    venv_python, convert_script,
                    "--outfile", gguf_path,
                    "--outtype", "q8_0",
                    model_dir
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    log(f"Conversion failed: {result.stderr}")
                    self.error.emit(f"Conversion failed: {result.stderr}")
                    return
                log(f"Model converted to GGUF: {gguf_path}")
            except Exception as e:
                log(f"Error during conversion: {e}")
                self.error.emit(f"Error during conversion: {e}")
                return
            # 5. Create Modelfile and import to Ollama
            selected_model = self.model_selector.currentText()
            if not selected_model or selected_model.startswith("("):
                log("No valid model selected for Ollama upload.")
                self.error.emit("No valid model selected for Ollama upload.")
                return
            existing_enhanced_models = [m for m in get_ollama_models() if m.endswith('-ai-coder-enhanced')]
            # For simplicity, always create a new model in this worker
            timestamp = int(time.time())
            model_name = f"{selected_model}-ai-coder-enhanced-{timestamp}"
            log(f"Creating new model: {model_name}")
            try:
                modelfile_content = f"""FROM {selected_model}
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER seed 42
SYSTEM You are an AI coding assistant trained on custom documentation and user feedback. You provide helpful code suggestions and explanations. You have been enhanced with domain-specific knowledge from the user's documentation and learning data.
"""
                modelfile_path = os.path.join(os.path.dirname(gguf_path), "Modelfile")
                with open(modelfile_path, 'w') as f:
                    f.write(modelfile_content)
                cmd = [
                    "ollama", "create", model_name, 
                    "-f", modelfile_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(gguf_path))
                if result.returncode != 0:
                    log(f"Failed to create new Ollama model: {result.stderr}")
                    self.error.emit(f"Failed to create new Ollama model: {result.stderr}")
                    return
                log(f"Successfully created new model: {model_name}")
                self.finished.emit(f"Model '{model_name}' exported to Ollama successfully.")
            except Exception as e:
                log(f"Error creating new model: {e}")
                self.error.emit(f"Error creating new model: {e}")
                return
        except Exception as e:
            self.error.emit(f"Unexpected error: {e}")

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