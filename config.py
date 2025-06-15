# config.py
import os
import torch

def get_best_device():
    """
    Checks for available hardware and returns the best device for PyTorch.
    """
    if torch.cuda.is_available():
        print("CUDA is available. Using GPU.")
        return "cuda"
    try:
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("Apple MPS is available. Using GPU.")
            return "mps"
    except Exception:
        pass 
    
    print("CUDA/MPS not available. Using CPU.")
    return "cpu"

# --- Project Root ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- Device Configuration ---
DEVICE = get_best_device()

# --- Vector Database (FAISS) Configuration ---
FAISS_INDEX_PATH = os.path.join(PROJECT_ROOT, "vector_store.faiss")
FAISS_METADATA_PATH = os.path.join(PROJECT_ROOT, "vector_store.json")
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'

# --- Directory and File Configuration ---
PROCESSED_DOCS_DIR = os.path.join(PROJECT_ROOT, "processed_docs_chunks")
LEARNING_DATA_FILE_DIR = os.path.join(PROJECT_ROOT, "learning_data")
LEARNING_DATA_FILE = os.path.join(LEARNING_DATA_FILE_DIR, "learning_data.jsonl")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs") 

# --- Custom Language Model Training Files ---
VOCAB_DIR = PROCESSED_DOCS_DIR 
VOCAB_FILE = os.path.join(PROCESSED_DOCS_DIR, "tokenizer.json")
CONCAT_FILE_PATH = os.path.join(PROCESSED_DOCS_DIR, "concatenated_corpus.txt")
FINETUNING_FILE_PATH = os.path.join(PROCESSED_DOCS_DIR, "finetuning_dataset.txt")

# --- Custom Language Model Hyperparameters & Special Tokens ---
PAD_TOKEN = '<pad>'
UNK_TOKEN = '<unk>'
PAD_TOKEN_ID = 1 
UNK_TOKEN_ID = 0
MAX_SEQUENCE_LENGTH = 256 

# --- Ollama Configuration ---
OLLAMA_API_BASE_URL = "http://localhost:11434/api"
OLLAMA_MODEL = "llama3" 
USE_OLLAMA_FOR_ENHANCEMENT = True

# --- Custom Language Model Training Config ---
VOCAB_SIZE = 20000 
MODEL_FILENAME = "ai_coder_model.pth"
MODEL_SAVE_PATH = os.path.join(PROCESSED_DOCS_DIR, MODEL_FILENAME)
NUM_EPOCHS = 5
BATCH_SIZE = 32
EMBED_DIM = 128
NUM_HEADS = 4
NUM_LAYERS = 2
DROPOUT = 0.1