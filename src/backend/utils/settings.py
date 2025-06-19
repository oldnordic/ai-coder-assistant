"""
settings.py

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

# config/settings.py
import os
import torch
from typing import Dict, Any
from backend.utils.constants import OLLAMA_API_BASE_URL as _OLLAMA_API_BASE_URL

# The project root is now two levels up from this file's directory (config/ -> project_root/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_best_device():
    """
    Checks for available hardware and returns the best device for PyTorch,
    with enhanced ROCm support and better diagnostics.
    """
    import subprocess
    
    # Set environment variables for GPU selection
    os.environ["ROCR_VISIBLE_DEVICES"] = "0"
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    
    # Check if ROCm is available on the system
    rocm_available = False
    try:
        result = subprocess.run(['rocm-smi'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            rocm_available = True
            print("ROCm detected on system")
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass
    
    # Check PyTorch CUDA/ROCm availability
    if torch.cuda.is_available():
        device_count = torch.cuda.device_count()
        print(f"CUDA/ROCm is available. Found {device_count} GPU(s).")
        
        # List available devices
        for i in range(device_count):
            try:
                device_name = torch.cuda.get_device_name(i)
                print(f"  GPU {i}: {device_name}")
            except Exception as e:
                print(f"  GPU {i}: Unable to get name ({e})")
        
        return "cuda:0"
    
    # Check for Apple MPS
    try:
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("Apple MPS is available. Using GPU.")
            return "mps"
    except Exception:
        pass 
    
    # If we get here, no GPU is available
    print("No GPU acceleration available. Using CPU.")
    
    # Provide helpful diagnostics
    if rocm_available:
        print("\n🔧 ROCm GPU Detection Diagnostics:")
        print("  ✓ ROCm is installed and GPUs are detected by rocm-smi")
        print("  ✗ PyTorch ROCm version is not installed")
        print("\nTo enable GPU acceleration, install PyTorch with ROCm support:")
        print("  pip uninstall torch torchvision torchaudio")
        print("  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.7")
        print("\nOr for the latest ROCm version:")
        print("  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0")
    else:
        print("\n🔧 GPU Detection Diagnostics:")
        print("  ✗ No ROCm installation detected")
        print("  ✗ PyTorch CUDA/ROCm version not available")
        print("\nTo enable GPU acceleration:")
        print("  1. Install ROCm: https://rocmdocs.amd.com/en/latest/Installation_Guide/Installation-Guide.html")
        print("  2. Install PyTorch with ROCm support")
    
    return "cpu"

# --- Device Configuration ---
DEVICE = get_best_device()

# --- Data Directories ---
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DOCS_DIR = os.path.join(DATA_DIR, "docs") 
LEARNING_DATA_DIR = os.path.join(DATA_DIR, "learning_data")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed_data")

# --- Custom Language Model Training Files ---
LEARNING_DATA_FILE = os.path.join(LEARNING_DATA_DIR, "learning_data.jsonl")
CONCAT_FILE_PATH = os.path.join(PROCESSED_DATA_DIR, "concatenated_corpus.txt")
FINETUNING_FILE_PATH = os.path.join(PROCESSED_DATA_DIR, "finetuning_dataset.txt")

# --- Model Saving Path ---
MODEL_DIR_NAME = "ai_coder_model"
MODEL_SAVE_PATH = os.path.join(PROCESSED_DATA_DIR, MODEL_DIR_NAME)

# --- Ollama Configuration ---
# OLLAMA_API_BASE_URL is now imported from constants
OLLAMA_API_BASE_URL = _OLLAMA_API_BASE_URL
OLLAMA_MODEL = "llama3"

# --- Custom Language Model Hyperparameters ---
VOCAB_SIZE = 20000 
MAX_SEQUENCE_LENGTH = 256 
NUM_EPOCHS = 3
BATCH_SIZE = 8
EMBED_DIM = 128
NUM_HEADS = 4
NUM_LAYERS = 2
DROPOUT = 0.1

# --- Cloud Models Settings ---
def get_settings() -> Dict[str, Any]:
    """Get settings for cloud models and other services."""
    return {
        "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
        "openai_base_url": os.environ.get("OPENAI_BASE_URL", ""),
        "openai_organization": os.environ.get("OPENAI_ORGANIZATION", ""),
        "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
        "google_api_key": os.environ.get("GOOGLE_API_KEY", ""),
        "azure_api_key": os.environ.get("AZURE_API_KEY", ""),
        "azure_endpoint": os.environ.get("AZURE_ENDPOINT", ""),
        "aws_access_key": os.environ.get("AWS_ACCESS_KEY", ""),
        "aws_secret_key": os.environ.get("AWS_SECRET_KEY", ""),
        "aws_region": os.environ.get("AWS_REGION", ""),
        "cohere_api_key": os.environ.get("COHERE_API_KEY", ""),
    }

def is_docker_available() -> bool:
    """Check if Docker is installed and available in the system PATH."""
    import shutil
    return shutil.which("docker") is not None