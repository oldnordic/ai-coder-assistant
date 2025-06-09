import os

# --- Directory and File Configuration ---
BASE_DOCS_SAVE_DIR = "documentation_corpus"
PROCESSED_DOCS_DIR = "processed_docs_chunks"
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