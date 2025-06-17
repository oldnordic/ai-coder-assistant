import os
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QPushButton, QTextEdit, QFileDialog, 
                             QMessageBox, QWidget, QComboBox)
import subprocess
import requests
from typing import Any

def is_ollama_running() -> bool:
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False
    except Exception as e:
        print(f"Error checking Ollama status: {e}")
        return False

def find_llama_cpp() -> str | None:
    """Finds the llama.cpp directory containing convert.py, prioritizing stability."""
    # 1. Try LLAMA_CPP_PATH environment variable
    env_path = os.environ.get("LLAMA_CPP_PATH")
    if env_path and os.path.exists(os.path.join(env_path, "convert.py")):
        return env_path

    # 2. Try common relative paths within the current project folder (non-recursive)
    project_root = os.path.abspath(os.path.dirname(__file__))
    # Go up from src/ui to project root
    project_root = os.path.abspath(os.path.join(project_root, "..", ".."))

    for candidate_relative in ["llama.cpp", os.path.join("..", "llama.cpp")]:
        candidate_path = os.path.join(project_root, candidate_relative)
        if os.path.exists(os.path.join(candidate_path, "convert.py")):
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
        if os.path.exists(os.path.join(path, "convert.py")):
            return path

    # If not found in any of the above safe locations, return None
    return None

def get_ollama_models() -> list[str]:
    """Fetch the list of models from the local Ollama instance."""
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=10)
        if resp.status_code == 200:
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
This tool will export your locally trained model (HuggingFace format) to GGUF and send it to your running Ollama instance for integration.
- The GGUF export requires llama.cpp's conversion script (convert.py).
- The exported model will be uploaded to Ollama using its API and Ollama will be auto-reloaded.
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
    status_box.setMinimumHeight(100)
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

    def export_and_send():
        # Pre-check: Is Ollama running?
        if not is_ollama_running():
            log("Error: Ollama is not running. Please start Ollama before exporting.")
            QMessageBox.critical(parent_widget, "Ollama Not Running", "Ollama server is not running. Please start it to continue.")
            return
        else:
            log("Ollama server is running.")

        # 1. Locate the local model directory
        from ..config import settings
        model_dir = settings.MODEL_SAVE_PATH
        if not os.path.exists(model_dir):
            QMessageBox.warning(parent_widget, "Model Not Found", f"Model directory not found: {model_dir}")
            return
        log(f"Found local model at: {model_dir}")

        # 2. Ask user for GGUF output path
        gguf_path, _ = QFileDialog.getSaveFileName(parent_widget, "Save GGUF Model As", "ai_coder_model.gguf", "GGUF Files (*.gguf)")
        if not gguf_path:
            log("Export cancelled by user.")
            return

        # 3. Auto-detect llama.cpp
        llama_cpp_dir = find_llama_cpp()
        if not llama_cpp_dir:
            log("Could not auto-detect llama.cpp. Please set LLAMA_CPP_PATH environment variable.")
            return
        log(f"Using llama.cpp at: {llama_cpp_dir}")
        convert_script = os.path.join(llama_cpp_dir, "convert.py")
        if not os.path.exists(convert_script):
            log(f"convert.py not found at {convert_script}.")
            return

        # 4. Convert to GGUF using llama.cpp's convert.py
        log("Converting HuggingFace model to GGUF format...")
        try:
            cmd = [
                "python3", convert_script,
                "--outtype", "gguf",
                "--outfile", gguf_path,
                model_dir
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                log(f"Conversion failed: {result.stderr}")
                return
            log(f"Model converted to GGUF: {gguf_path}")
        except Exception as e:
            log(f"Error during conversion: {e}")
            return

        # 5. Upload to Ollama, specifying the model name
        selected_model = model_selector.currentText()
        if not selected_model or selected_model.startswith("("):
            log("No valid model selected for Ollama upload.")
            return
        log(f"Uploading GGUF model to Ollama for model: {selected_model} ...")
        try:
            ollama_url = f"http://localhost:11434/api/import?name={selected_model}"
            with open(gguf_path, "rb") as f:
                files = {"file": (os.path.basename(gguf_path), f, "application/octet-stream")}
                response = requests.post(ollama_url, files=files, timeout=60)
            if response.status_code == 200:
                log(f"Model uploaded to Ollama as '{selected_model}' successfully!")
                # 6. Auto-reload Ollama
                try:
                    reload_url = "http://localhost:11434/api/reload"
                    reload_resp = requests.post(reload_url, timeout=10)
                    if reload_resp.status_code == 200:
                        log("Ollama reloaded successfully!")
                    else:
                        log(f"Ollama reload failed: {reload_resp.status_code} {reload_resp.text}")
                except Exception as e:
                    log(f"Error reloading Ollama: {e}")
            else:
                log(f"Ollama upload failed: {response.status_code} {response.text}")
        except Exception as e:
            log(f"Error uploading to Ollama: {e}")

    export_button.clicked.connect(export_and_send) 