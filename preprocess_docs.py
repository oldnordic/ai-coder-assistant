import os
import re
import json
from collections import Counter
import config

def clean_text(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def build_vocabulary_from_files(files, log_callback):
    _log = log_callback
    word_counts = Counter()
    total_files = len(files)
    _log(f"Building vocabulary from {total_files} files (Pass 1/2)...")
    for i, filepath in enumerate(files):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    tokens = clean_text(line).split()
                    word_counts.update(tokens)
        except Exception as e:
            _log(f"Could not read file for vocab build {filepath}: {e}")
    
    vocabulary = {"<pad>": 0, "<unk>": 1}
    vocabulary.update({word: i + 2 for i, (word, count) in enumerate(word_counts.most_common(config.VOCAB_SIZE - 2))})
    _log("Vocabulary build complete.")
    return vocabulary

def tokenize_and_save_chunks(files, vocabulary, progress_callback, log_callback):
    _log = log_callback
    _log("Tokenizing and saving chunks (Pass 2/2)...")
    total_files = len(files)
    
    chunk_size = config.CHUNK_SIZE
    overlap = config.OVERLAP_SIZE
    step_size = chunk_size - overlap

    with open(config.TOKENIZED_CHUNKS_FILE, 'w', encoding='utf-8') as f_out:
        for i, filepath in enumerate(files):
            token_buffer = []
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line_tokens = clean_text(line).split()
                        token_buffer.extend(line_tokens)
                        
                        while len(token_buffer) >= chunk_size:
                            chunk_to_process = token_buffer[:chunk_size]
                            numerical_tokens = [vocabulary.get(token, vocabulary["<unk>"]) for token in chunk_to_process]
                            # No need for extra padding as we ensure chunk is full size
                            f_out.write(json.dumps({"numerical_tokens": numerical_tokens}) + '\n')
                            # Slide the buffer window
                            token_buffer = token_buffer[step_size:]
                
                # Process any remaining tokens in the buffer after the file is done
                if token_buffer:
                    numerical_tokens = [vocabulary.get(token, vocabulary["<unk>"]) for token in token_buffer]
                    padded_tokens = numerical_tokens + [vocabulary["<pad>"]] * (chunk_size - len(numerical_tokens))
                    f_out.write(json.dumps({"numerical_tokens": padded_tokens[:chunk_size]}) + '\n')

                if progress_callback:
                    progress_callback(i + 1, total_files, f"Processing {i+1}/{total_files}: {os.path.basename(filepath)}")
            except Exception as e:
                _log(f"Could not process file for tokenization {filepath}: {e}")
    _log("Tokenization and chunking complete.")


def preprocess_documentation_for_ai(base_raw_docs_dir, processed_docs_dir, chunk_size, overlap_size, vocab_size,
                                    local_corpus_dir=None, progress_callback=None, log_message_callback=None):
    _log = log_message_callback if callable(log_message_callback) else print
    
    all_doc_filepaths = []
    if os.path.exists(base_raw_docs_dir):
        all_doc_filepaths.extend([os.path.join(root, file) for root, _, files in os.walk(base_raw_docs_dir) for file in files if file.endswith(('.txt', '.py'))])
    
    if local_corpus_dir and os.path.isdir(local_corpus_dir):
        _log(f"Adding local files from: {local_corpus_dir}")
        all_doc_filepaths.extend([os.path.join(root, file) for root, _, files in os.walk(local_corpus_dir) for file in files if file.endswith(('.txt', '.py'))])

    if not all_doc_filepaths:
        _log("No text or python files found to preprocess.")
        if progress_callback: progress_callback(1, 1, "No files found.")
        return
        
    if not os.path.exists(processed_docs_dir):
        os.makedirs(processed_docs_dir)

    # Pass 1: Build Vocabulary in a memory-safe way
    vocabulary = build_vocabulary_from_files(all_doc_filepaths, _log)
    with open(config.VOCAB_FILE, 'w', encoding='utf-8') as f:
        json.dump(vocabulary, f, indent=4)
    _log(f"Vocabulary with {len(vocabulary)} words saved.")

    # Pass 2: Tokenize and Save Chunks in a memory-safe way
    tokenize_and_save_chunks(all_doc_filepaths, vocabulary, progress_callback, _log)
            
    _log("Preprocessing complete.")