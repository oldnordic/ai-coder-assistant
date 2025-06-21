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

import concurrent.futures
import os
from typing import Any

import requests
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.backend.utils.constants import (
    HTTP_OK,
    HTTP_TIMEOUT_LONG,
    HTTP_TIMEOUT_SHORT,
    OLLAMA_BASE_URL,
    STATUS_BOX_MIN_HEIGHT,
)


def is_ollama_running() -> bool:
    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags", timeout=HTTP_TIMEOUT_SHORT
        )
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
            return [m["name"] for m in data.get("models", [])]
        else:
            return []
    except Exception:
        return []


def setup_ollama_export_tab(parent_widget: QWidget, main_app_instance: Any):
    """Set up the Ollama export tab with widget dictionary organization."""
    # Initialize widget dictionary for Ollama export tab
    main_app_instance.widgets["ollama_export_tab"] = {}
    w = main_app_instance.widgets["ollama_export_tab"]

    layout = QVBoxLayout(parent_widget)

    # Title
    w["title"] = QLabel("Export Local Model to Ollama")
    w["title"].setStyleSheet("font-weight: bold; font-size: 16px;")
    layout.addWidget(w["title"])

    # Info text
    w["info"] = QLabel(
        """
This tool will export your locally trained model (HuggingFace format) to GGUF and create an enhanced Ollama model.
- The GGUF export requires llama.cpp's conversion script (convert_hf_to_gguf.py).
- An enhanced Ollama model will be created that extends your selected base model with custom parameters and system prompts.
- The enhanced model can be used for improved code suggestions in the AI Agent tab.
    """
    )
    w["info"].setWordWrap(True)
    layout.addWidget(w["info"])

    # Model selection
    w["model_label"] = QLabel("Select Ollama Model to Feed Knowledge:")
    layout.addWidget(w["model_label"])

    w["model_selector"] = QComboBox()
    w["model_selector"].addItem("(Click 'Refresh Models' to load)")
    layout.addWidget(w["model_selector"])

    # Refresh button
    w["refresh_button"] = QPushButton("Refresh Models")
    layout.addWidget(w["refresh_button"])

    # Status box
    w["status_box"] = QTextEdit()
    w["status_box"].setReadOnly(True)
    w["status_box"].setMinimumHeight(STATUS_BOX_MIN_HEIGHT)
    layout.addWidget(w["status_box"])

    # Export button
    w["export_button"] = QPushButton("Export & Send to Ollama")
    layout.addWidget(w["export_button"])

    def log(msg: str):
        w["status_box"].append(msg)

    def refresh_models():
        w["model_selector"].clear()
        log("Fetching available models from Ollama...")
        models = get_ollama_models()
        if not models:
            w["model_selector"].addItem("(No models found)")
            log("No models found on Ollama or Ollama is not running.")
        else:
            for m in models:
                w["model_selector"].addItem(m)
            log(f"Found {len(models)} model(s) on Ollama.")

    # Connect the refresh button
    w["refresh_button"].clicked.connect(refresh_models)

    def start_export():
        progress_dialog = QProgressDialog(
            "Exporting model to Ollama...", "Cancel", 0, 0, parent_widget
        )
        progress_dialog.setWindowTitle("Ollama Export Progress")
        progress_dialog.setAutoClose(False)
        progress_dialog.setAutoReset(False)
        progress_dialog.show()

        # Keep a reference to the worker to prevent GC
        parent_widget.ollama_export_worker = OllamaExportWorker(
            parent_widget, w["model_selector"], w["status_box"]
        )
        worker = parent_widget.ollama_export_worker

        def on_progress(msg):
            w["status_box"].append(msg)
            QApplication.processEvents()

        def on_finished(msg):
            progress_dialog.close()
            w["status_box"].append(msg)
            QMessageBox.information(parent_widget, "Export Complete", msg)
            parent_widget.ollama_export_worker = None

        def on_error(msg):
            progress_dialog.close()
            w["status_box"].append(msg)
            QMessageBox.critical(parent_widget, "Export Failed", msg)
            parent_widget.ollama_export_worker = None

        worker.progress.connect(on_progress)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        progress_dialog.canceled.connect(worker.cancel)
        worker.start()

    w["export_button"].clicked.connect(start_export)


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

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        self.title = QLabel("Export Local Model to Ollama")
        self.title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(self.title)

        # Info text
        self.info = QLabel(
            """
This tool will export your locally trained model (HuggingFace format) to GGUF and create an enhanced Ollama model.
- The GGUF export requires llama.cpp's conversion script (convert_hf_to_gguf.py).
- An enhanced Ollama model will be created that extends your selected base model with custom parameters and system prompts.
- The enhanced model can be used for improved code suggestions in the AI Agent tab.
            """
        )
        self.info.setWordWrap(True)
        layout.addWidget(self.info)

        # Model selection
        self.model_label = QLabel("Select Ollama Model to Feed Knowledge:")
        layout.addWidget(self.model_label)

        self.model_selector = QComboBox()
        self.model_selector.addItem("(Click 'Refresh Models' to load)")
        layout.addWidget(self.model_selector)

        # Refresh button
        self.refresh_button = QPushButton("Refresh Models")
        layout.addWidget(self.refresh_button)

        # Status box
        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        self.status_box.setMinimumHeight(STATUS_BOX_MIN_HEIGHT)
        layout.addWidget(self.status_box)

        # Export button
        self.export_button = QPushButton("Export & Send to Ollama")
        layout.addWidget(self.export_button)

        # Format selector
        self.format_selector = QComboBox()
        self.format_selector.addItems(["JSON", "CSV", "Markdown (.md)", "PDF"])
        layout.addWidget(self.format_selector)

        def log(msg: str):
            self.status_box.append(msg)

        def refresh_models():
            self.model_selector.clear()
            log("Fetching available models from Ollama...")
            models = get_ollama_models()
            if not models:
                self.model_selector.addItem("(No models found)")
                log("No models found on Ollama or Ollama is not running.")
            else:
                for m in models:
                    self.model_selector.addItem(m)
                log(f"Found {len(models)} model(s) on Ollama.")

        # Connect the refresh button
        self.refresh_button.clicked.connect(refresh_models)

        def start_export():
            progress_dialog = QProgressDialog(
                "Exporting model to Ollama...", "Cancel", 0, 0, self
            )
            progress_dialog.setWindowTitle("Ollama Export Progress")
            progress_dialog.setAutoClose(False)
            progress_dialog.setAutoReset(False)
            progress_dialog.show()

            # Keep a reference to the worker to prevent GC
            self.ollama_export_worker = OllamaExportWorker(
                self, self.model_selector, self.status_box
            )
            worker = self.ollama_export_worker

            def on_progress(msg):
                self.status_box.append(msg)
                QApplication.processEvents()

            def on_finished(msg):
                progress_dialog.close()
                self.status_box.append(msg)
                QMessageBox.information(self, "Export Complete", msg)
                self.ollama_export_worker = None

            def on_error(msg):
                progress_dialog.close()
                self.status_box.append(msg)
                QMessageBox.critical(self, "Export Failed", msg)
                self.ollama_export_worker = None

            worker.progress.connect(on_progress)
            worker.finished.connect(on_finished)
            worker.error.connect(on_error)
            progress_dialog.canceled.connect(worker.cancel)
            worker.start()

        self.export_button.clicked.connect(start_export)
