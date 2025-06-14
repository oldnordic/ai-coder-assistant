# config.py
import os

# --- Project Root ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- NEW: Vector Database (FAISS) Configuration ---
# We now store the index and the document chunks separately.
FAISS_INDEX_PATH = os.path.join(PROJECT_ROOT, "vector_store.faiss")
FAISS_METADATA_PATH = os.path.join(PROJECT_ROOT, "vector_store.json")
# This is a popular, high-quality model for creating text embeddings.
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'


# --- Directory and File Configuration ---
BASE_DOCS_SAVE_DIR = os.path.join(PROJECT_ROOT, "documentation_corpus")
PROCESSED_DOCS_DIR = os.path.join(PROJECT_ROOT, "processed_docs_chunks")
LEARNING_DATA_FILE_DIR = os.path.join(PROJECT_ROOT, "learning_data")
LEARNING_DATA_FILE = os.path.join(LEARNING_DATA_FILE_DIR, "learning_data.jsonl")

# NEW: Folder for storing transcribed/local documents
TRANSCRIPTION_SAVE_DIR = os.path.join(PROJECT_ROOT, "docs") 

# --- Custom Language Model Training Files ---
VOCAB_FILE = os.path.join(PROCESSED_DOCS_DIR, "vocab.json")
TOKENIZED_CHUNKS_FILE = os.path.join(PROCESSED_DOCS_DIR, "tokenized_chunks.jsonl")

# --- Custom Language Model Hyperparameters & Special Tokens ---
PAD_TOKEN = '<pad>'
UNK_TOKEN = '<unk>'
PAD_TOKEN_ID = 1 
UNK_TOKEN_ID = 0
MAX_SEQUENCE_LENGTH = 256 

# --- Multi-language Documentation Sources ---
DOCUMENTATION_SOURCES = {
    "Python": [
        {"name": "Python_StdLib", "start_url": "https://docs.python.org/3/library/", "content_selector": "div[role='main']", "crawl_limit": 100},
        {"name": "Requests", "start_url": "https://requests.readthedocs.io/en/latest/", "content_selector": "div.section", "crawl_limit": 50},
    ],
    "JavaScript": [
        {"name": "MDN_JavaScript_Guide", "start_url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "content_selector": "main#content", "crawl_limit": 100},
    ],
    "Java": [
        {"name": "Java_SE_17_API", "start_url": "https://docs.oracle.com/en/java/javase/17/docs/api/java.base/module-summary.html", "content_selector": "main[role='main']", "crawl_limit": 100},
    ]
}

# --- Ollama Configuration ---
OLLAMA_API_BASE_URL = "http://localhost:11434/api"
OLLAMA_MODEL = "llama3" 
USE_OLLAMA_FOR_ENHANCEMENT = True

# --- Custom Language Model Training Config ---
VOCAB_SIZE = 20000 
CHUNK_SIZE = 256 
OVERLAP_SIZE = 32 
MODEL_FILENAME = "ai_coder_model.pth"
MODEL_SAVE_PATH = os.path.join(PROCESSED_DOCS_DIR, MODEL_FILENAME)
NUM_EPOCHS = 5
BATCH_SIZE = 32
EMBED_DIM = 128
NUM_HEADS = 4
NUM_LAYERS = 2
DROPOUT = 0.1