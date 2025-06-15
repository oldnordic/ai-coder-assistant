# preprocess_docs.py
import os
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from tqdm import tqdm
import config

def build_vector_db(docs_dir, index_path, metadata_path, reset_db=True, **kwargs):
    log_message_callback = kwargs.get('log_message_callback', print)
    progress_callback = kwargs.get('progress_callback', lambda c, t, m: None)

    try:
        log_message_callback("Starting document preprocessing...")
        progress_callback(0, 100, "Initializing...")

        if reset_db:
            if os.path.exists(index_path): os.remove(index_path)
            if os.path.exists(metadata_path): os.remove(metadata_path)
            if os.path.exists(config.CONCAT_FILE_PATH): os.remove(config.CONCAT_FILE_PATH)
            # --- NEW: Also clear the finetuning dataset if resetting ---
            finetuning_file = os.path.join(config.PROCESSED_DOCS_DIR, "finetuning_dataset.txt")
            if os.path.exists(finetuning_file):
                os.remove(finetuning_file)
                log_message_callback(f"Removed existing finetuning dataset.")


        all_chunks = []
        files_to_process = [f for f in os.listdir(docs_dir) if os.path.isfile(os.path.join(docs_dir, f))]
        total_files = len(files_to_process)
        log_message_callback(f"Found {total_files} files for general corpus.")

        with open(config.CONCAT_FILE_PATH, 'a', encoding='utf-8') as concat_file:
            for i, filename in enumerate(files_to_process):
                progress_callback(i, total_files, f"Processing file {i+1}/{total_files}: {filename}")
                filepath = os.path.join(docs_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                concat_file.write(content + "\n")
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
                chunks = text_splitter.split_text(content)
                all_chunks.extend(chunks)
        
        # --- NEW: Process the learning feedback data for finetuning ---
        log_message_callback("Processing user feedback for finetuning...")
        finetuning_entries = 0
        if os.path.exists(config.LEARNING_DATA_FILE):
            finetuning_dataset_path = os.path.join(config.PROCESSED_DOCS_DIR, "finetuning_dataset.txt")
            with open(config.LEARNING_DATA_FILE, 'r', encoding='utf-8') as infile, \
                 open(finetuning_dataset_path, 'w', encoding='utf-8') as outfile:
                for line in infile:
                    try:
                        entry = json.loads(line)
                        # Create a structured prompt for training
                        instruction = f"### Issue: {entry['issue']}\n"
                        original = f"### Bad Code: {entry['original_code']}\n"
                        corrected = f"### Good Code: {entry['user_feedback_or_code']}"
                        outfile.write(f"{instruction}{original}{corrected}\n")
                        finetuning_entries += 1
                    except json.JSONDecodeError:
                        continue # Skip malformed lines
            log_message_callback(f"Created finetuning dataset with {finetuning_entries} entries.")
        else:
            log_message_callback("No learning data file found. Skipping finetuning dataset creation.")

        if not all_chunks:
            log_message_callback("No text chunks found for vector DB. Aborting.")
            progress_callback(100, 100, "No documents found.")
            return "Error: No documents found to process."
        
        progress_callback(50, 100, "Embedding chunks...")
        model = SentenceTransformer(config.EMBEDDING_MODEL_NAME, device=config.DEVICE)
        embeddings = model.encode(all_chunks, show_progress_bar=True, device=config.DEVICE)
        
        progress_callback(80, 100, "Building FAISS index...")
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(np.array(embeddings).astype('float32'))
        
        faiss.write_index(index, index_path)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f)

        log_message_callback("Preprocessing and vector DB creation complete.")
        progress_callback(100, 100, "Preprocessing complete!")
        return "Success"

    except Exception as e:
        log_message_callback(f"An error occurred during preprocessing: {e}")
        return f"Error: {e}"