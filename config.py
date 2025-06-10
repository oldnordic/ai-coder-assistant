import os

# --- Project Root ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- Directory and File Configuration ---
BASE_DOCS_SAVE_DIR = os.path.join(PROJECT_ROOT, "documentation_corpus")
PROCESSED_DOCS_DIR = os.path.join(PROJECT_ROOT, "processed_docs_chunks")
LEARNING_DATA_FILE = os.path.join(PROCESSED_DOCS_DIR, "learning_data.jsonl")

# --- Preprocessing & Vocabulary ---
VOCAB_FILE = os.path.join(PROCESSED_DOCS_DIR, "vocabulary.json")
TOKENIZED_CHUNKS_FILE = os.path.join(PROCESSED_DOCS_DIR, "tokenized_chunks.jsonl")
VOCAB_SIZE = 10000

# --- Model & Training Configuration ---
CHUNK_SIZE = 256
OVERLAP_SIZE = 32
MODEL_FILENAME = "ai_coder_model.pth"
MODEL_SAVE_PATH = os.path.join(PROCESSED_DOCS_DIR, MODEL_FILENAME)

# --- Transformer Architecture ---
NUM_EPOCHS = 5
BATCH_SIZE = 32
EMBED_DIM = 128
NUM_HEADS = 2
NUM_LAYERS = 2
DROPOUT = 0.1

# --- NEW: Scanner Configuration ---
# Determines the number of CPU cores to use for the code scanner.
# A good rule is to leave 1 or 2 cores free for the OS and other apps.
# os.cpu_count() might return None, so we handle that case.
CPU_CORES = os.cpu_count() or 4  # Default to 4 if cpu_count fails
SCANNER_MAX_WORKERS = max(1, CPU_CORES - 2) # Always use at least 1 core