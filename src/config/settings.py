# config/settings.py
import os
import torch

# The project root is now two levels up from this file's directory (config/ -> project_root/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_best_device():
    """
    Checks for available hardware and returns the best device for PyTorch,
    explicitly setting the visible device to avoid multi-GPU errors.
    """
    os.environ["ROCR_VISIBLE_DEVICES"] = "0"
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"

    if torch.cuda.is_available():
        print("CUDA (or ROCm) is available. Using GPU 0.")
        return "cuda:0"
    
    try:
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("Apple MPS is available. Using GPU.")
            return "mps"
    except Exception:
        pass 
    
    print("CUDA/MPS not available. Using CPU.")
    return "cpu"

# --- Device Configuration ---
DEVICE = get_best_device()

# --- Data Directories ---
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DOCS_DIR = os.path.join(DATA_DIR, "docs") 
LEARNING_DATA_DIR = os.path.join(DATA_DIR, "learning_data")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed_data")

# --- Optional Vector Database Configuration (only used when needed) ---
# These are only used when explicitly building vector databases
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'  # Only loaded when needed

# --- Custom Language Model Training Files ---
LEARNING_DATA_FILE = os.path.join(LEARNING_DATA_DIR, "learning_data.jsonl")
CONCAT_FILE_PATH = os.path.join(PROCESSED_DATA_DIR, "concatenated_corpus.txt")
FINETUNING_FILE_PATH = os.path.join(PROCESSED_DATA_DIR, "finetuning_dataset.txt")

# --- Model Saving Path ---
MODEL_DIR_NAME = "ai_coder_model"
MODEL_SAVE_PATH = os.path.join(PROCESSED_DATA_DIR, MODEL_DIR_NAME)

# --- Ollama Configuration ---
OLLAMA_API_BASE_URL = "http://localhost:11434/api"
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