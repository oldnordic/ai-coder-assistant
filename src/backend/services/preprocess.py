"""
preprocess.py

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

# src/processing/preprocess.py
import os
import json
import re
from bs4 import BeautifulSoup
from pypdf import PdfReader
import logging
import datetime
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from backend.utils import settings
from backend.services import scanner as ai_coder_scanner
from backend.utils.constants import PROGRESS_COMPLETE

logger = logging.getLogger(__name__)

def extract_text_from_pdf(filepath: str) -> str:
    """Extracts text content from a PDF file."""
    try:
        with open(filepath, 'rb') as f:
            reader = PdfReader(f)
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
    """
    Saves user feedback and corrections to the learning data file for future model training.
    This creates a feedback loop where the model learns from user corrections.
    """
    log_message_callback = kwargs.get('log_message_callback', print)
    _log = log_message_callback
    
    try:
        # Ensure the learning data directory exists
        os.makedirs(settings.LEARNING_DATA_DIR, exist_ok=True)
        
        # Extract the original code from the suggestion
        original_code = suggestion_data.get('code_snippet', '').strip()
        
        # Use user-provided code if available, otherwise use the suggested improvement
        good_code = user_provided_code if user_provided_code else suggestion_data.get('suggested_improvement', '').strip()
        
        if not original_code or not good_code:
            _log("Warning: Missing original code or good code for feedback learning.")
            return
        
        # Create the learning example
        learning_example = {
            'original_code': original_code,
            'user_feedback_or_code': good_code,
            'file_path': suggestion_data.get('file_path', ''),
            'line_number': suggestion_data.get('line_number', ''),
            'description': suggestion_data.get('description', ''),
            'timestamp': str(datetime.datetime.now())
        }
        
        # Append to the learning data file
        with open(settings.LEARNING_DATA_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(learning_example, ensure_ascii=False) + '\n')
        
        _log(f"Saved learning feedback: {suggestion_data.get('description', 'Unknown suggestion')}")
        
    except Exception as e:
        _log(f"Error saving learning feedback: {e}")
        import traceback
        _log(f"Traceback: {traceback.format_exc()}")

def parse_md_report(md_path, log_message_callback):
    # ... (This function remains unchanged) ...
    pass

def process_file_parallel(filepath: str, filename: str, log_message_callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
    """
    Process a single file in a thread-safe manner.
    Returns the extracted content or None if processing failed.
    """
    _log = log_message_callback if callable(log_message_callback) else print
    
    try:
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
            return None

        return content
        
    except Exception as e:
        _log(f"Error processing {filename}: {e}")
        return None

def build_vector_db(docs_dir, index_path, metadata_path, reset_db=True, **kwargs):
    """
    Builds text processing for documents with multi-threading support.
    """
    log_message_callback = kwargs.get('log_message_callback', print)
    progress_callback = kwargs.get('progress_callback', lambda c, t, m: None)
    _log = log_message_callback
    try:
        _log("Starting document preprocessing with multi-threading...")
        if reset_db:
            for path in [settings.CONCAT_FILE_PATH, settings.FINETUNING_FILE_PATH]:
                if os.path.exists(path):
                    os.remove(path)
                    _log(f"Removed existing file: {os.path.basename(path)}")
        os.makedirs(settings.PROCESSED_DATA_DIR, exist_ok=True)
        all_chunks = []
        files_to_process = [f for f in os.listdir(docs_dir) if os.path.isfile(os.path.join(docs_dir, f))]
        if not files_to_process:
            _log("No files found to process in docs_dir: " + str(docs_dir))
            return "No files found to process. Please acquire or add documents first."
        progress_lock = threading.Lock()
        processed_count = 0
        def update_progress(filename: str):
            nonlocal processed_count
            with progress_lock:
                processed_count += 1
                progress_callback(processed_count, len(files_to_process), f"Processing: {filename}")
        import multiprocessing
        max_workers = min(multiprocessing.cpu_count(), len(files_to_process), 8)
        _log(f"Using {max_workers} worker threads for parallel processing")
        file_contents = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {}
            for filename in files_to_process:
                filepath = os.path.join(docs_dir, filename)
                future = executor.submit(process_file_parallel, filepath, filename, log_message_callback)
                future_to_file[future] = filename
            for future in as_completed(future_to_file):
                filename = future_to_file[future]
                try:
                    content = future.result()
                    if content:
                        file_contents[filename] = content
                        all_chunks.extend(content.splitlines())
                    update_progress(filename)
                except Exception as e:
                    _log(f"Error processing {filename}: {e}")
                    update_progress(filename)
        with open(settings.CONCAT_FILE_PATH, 'a', encoding='utf-8', errors='ignore') as concat_file:
            for filename, content in file_contents.items():
                concat_file.write(content + "\n\n")
        finetuning_examples = []
        if os.path.exists(settings.LEARNING_DATA_FILE):
            with open(settings.LEARNING_DATA_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    try: finetuning_examples.append(json.loads(line))
                    except json.JSONDecodeError: continue
        valid_finetuning_strings = []
        for ex in finetuning_examples:
            if isinstance(ex, dict) and 'prompt' in ex and 'completion' in ex:
                valid_finetuning_strings.append(json.dumps(ex))
        if valid_finetuning_strings:
            with open(settings.FINETUNING_FILE_PATH, 'a', encoding='utf-8', errors='ignore') as f:
                for line in valid_finetuning_strings:
                    f.write(line + "\n")
        _log(f"Preprocessing complete. Processed {len(files_to_process)} files.")
        return f"Success: Processed {len(files_to_process)} files."
    except Exception as e:
        import traceback
        error_msg = f"Error during preprocessing: {e}\n{traceback.format_exc()}"
        _log(error_msg)
        return error_msg