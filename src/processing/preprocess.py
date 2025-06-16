# src/processing/preprocess.py
import os
import json
import re
from bs4 import BeautifulSoup
import PyPDF2
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import logging

from ..config import settings
from ..core import scanner as ai_coder_scanner

"""Preprocess documentation into embeddings and datasets for training."""

logger = logging.getLogger(__name__)

def extract_text_from_pdf(filepath: str) -> str:
    """Extracts text content from a PDF file."""
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        logger.error(f"Could not read PDF file {filepath}: {e}")
        return ""

def extract_text_from_html(filepath: str) -> str:
    """Extracts clean text from an HTML file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
        for script_or_style in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            script_or_style.decompose()
        return soup.get_text(separator='\n', strip=True)
    except Exception as e:
        logger.error(f"Could not read HTML file {filepath}: {e}")
        return ""

def save_learning_feedback(suggestion_data, user_provided_code=None, **kwargs):
    # ... (This function remains unchanged) ...
    pass

def parse_md_report(md_path, log_message_callback):
    # ... (This function remains unchanged) ...
    pass


def build_vector_db(docs_dir, index_path, metadata_path, reset_db=True, **kwargs):
    """Create a FAISS vector store from raw documents and feedback."""

    log_message_callback = kwargs.get('log_message_callback', print)
    progress_callback = kwargs.get('progress_callback', lambda c, t, m: None)
    _log = log_message_callback

    try:
        _log("Starting document preprocessing...")
        if reset_db:
            for path in [index_path, metadata_path, settings.CONCAT_FILE_PATH, settings.FINETUNING_FILE_PATH]:
                if os.path.exists(path):
                    os.remove(path)
                    _log(f"Removed existing file: {os.path.basename(path)}")
        
        os.makedirs(settings.PROCESSED_DATA_DIR, exist_ok=True)

        all_chunks = []
        files_to_process = [f for f in os.listdir(docs_dir) if os.path.isfile(os.path.join(docs_dir, f))]
        
        with open(settings.CONCAT_FILE_PATH, 'a', encoding='utf-8', errors='ignore') as concat_file:
            for i, filename in enumerate(files_to_process):
                progress_callback(i + 1, len(files_to_process), f"Processing doc: {filename}")
                filepath = os.path.join(docs_dir, filename)
                content = ""
                
                # --- FIXED: Intelligent text extraction based on file type ---
                if filename.lower().endswith('.pdf'):
                    _log(f"Extracting text from PDF: {filename}")
                    content = extract_text_from_pdf(filepath)
                elif filename.lower().endswith(('.html', '.htm')):
                    _log(f"Extracting text from HTML: {filename}")
                    content = extract_text_from_html(filepath)
                elif filename.lower().endswith('.txt'):
                     _log(f"Reading text file: {filename}")
                     with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                else:
                    _log(f"Skipping unsupported file type: {filename}")
                    continue

                if content:
                    concat_file.write(content + "\n\n")
                    all_chunks.extend(content.splitlines())
        
        finetuning_examples = []
        if os.path.exists(settings.LEARNING_DATA_FILE):
            with open(settings.LEARNING_DATA_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    try: finetuning_examples.append(json.loads(line))
                    except json.JSONDecodeError: continue
        
        valid_finetuning_strings = []
        if finetuning_examples:
            for entry in finetuning_examples:
                original_code = entry.get('original_code', '').strip()
                good_code = entry.get('user_feedback_or_code', '').strip()
                if not (original_code and good_code):
                    continue
                training_example = f"[BAD_CODE] {original_code} [GOOD_CODE] {good_code}"
                valid_finetuning_strings.append(training_example)
                all_chunks.append(training_example)
        
        if valid_finetuning_strings:
            with open(settings.FINETUNING_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write("\n".join(valid_finetuning_strings))
            _log(f"Created finetuning dataset with {len(valid_finetuning_strings)} valid examples.")
        else:
            _log("No valid feedback data found to create finetuning dataset.")

        if not all_chunks:
            _log("No text chunks found to build the vector DB.")
            progress_callback(100, 100, "Preprocessing complete! No new data found.")
            return "Success - No new data processed."
        else:
            _log(f"Building vector DB from {len(all_chunks)} total text chunks...")
            progress_callback(50, 100, "Embedding chunks for Vector DB...")
            model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, device=settings.DEVICE)
            embeddings = model.encode(all_chunks, show_progress_bar=False)
            index = faiss.IndexFlatL2(embeddings.shape[1])
            index.add(np.array(embeddings).astype('float32'))
            faiss.write_index(index, index_path)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(all_chunks, f)
            _log("Vector DB built successfully.")
        
        _log("Preprocessing complete.")
        progress_callback(100, 100, "Preprocessing complete!")
        return "Success"
    except Exception as e:
        import traceback
        _log(f"An error occurred during preprocessing: {e}\n{traceback.format_exc()}")
        return f"Error: {e}"
