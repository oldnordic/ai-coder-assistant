# preprocess_docs.py
import os
import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import config

# Imports for tokenization and vocabulary for custom model
from collections import Counter
import re
import hashlib # For hashing content to detect changes

def build_vector_db(base_raw_docs_dir, local_additional_docs_dir=None, accumulation_mode="Accumulate Knowledge (Add New)", progress_callback=None, log_message_callback=None):
    """
    Loads text files, splits them into chunks, creates embeddings for FAISS,
    and also generates tokenized chunks and vocabulary for custom model training.
    Supports 'Reset' (overwrite) or 'Accumulate' (add new) modes.
    """
    _log = log_message_callback if callable(log_message_callback) else print

    _log("Initializing embedding model for FAISS...")
    model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
    embedding_dim = model.get_sentence_embedding_dimension()
    _log(f"Embedding model '{config.EMBEDDING_MODEL_NAME}' loaded.")

    # Gather all document file paths
    all_doc_filepaths = []
    for root, _, files in os.walk(base_raw_docs_dir):
        for file in files:
            if file.endswith('.txt'):
                all_doc_filepaths.append(os.path.join(root, file))
    
    if local_additional_docs_dir and os.path.isdir(local_additional_docs_dir):
        for root, _, files in os.walk(local_additional_docs_dir):
            for file in files:
                if file.endswith('.txt'):
                    all_doc_filepaths.append(os.path.join(root, file))

    if not all_doc_filepaths:
        _log("No documents found to process."); return

    _log(f"Found {len(all_doc_filepaths)} documents to process.")
    
    text_splitter_rag = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    text_splitter_lm = RecursiveCharacterTextSplitter(
        chunk_size=getattr(config, 'CHUNK_SIZE', 256), 
        chunk_overlap=getattr(config, 'OVERLAP_SIZE', 32)
    )

    all_final_rag_chunks = []
    all_final_lm_chunks_raw_text = []
    current_vocab = {}
    index_to_save = None

    if accumulation_mode == "Accumulate Knowledge (Add New)":
        _log("Attempting to load existing knowledge for accumulation.")
        # Load existing FAISS data
        if os.path.exists(config.FAISS_INDEX_PATH) and os.path.exists(config.FAISS_METADATA_PATH):
            try:
                index_to_save = faiss.read_index(config.FAISS_INDEX_PATH)
                with open(config.FAISS_METADATA_PATH, 'r', encoding='utf-8') as f:
                    all_final_rag_chunks = json.load(f)
                _log(f"Loaded existing FAISS index with {index_to_save.ntotal} vectors and {len(all_final_rag_chunks)} chunks.")
            except Exception as e:
                _log(f"Could not load existing FAISS index/metadata ({e}), starting new index.")
                index_to_save = None
                all_final_rag_chunks = []
        
        # Load existing LM data
        if os.path.exists(config.VOCAB_FILE) and os.path.exists(config.TOKENIZED_CHUNKS_FILE):
            try:
                with open(config.VOCAB_FILE, 'r', encoding='utf-8') as f:
                    current_vocab = json.load(f)
                with open(config.TOKENIZED_CHUNKS_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        # Reconstruct raw text from tokenized_chunks.jsonl to re-process for new chunks
                        # This assumes 'original_chunk' is stored, or you'll need to reconstruct from tokens
                        chunk_data = json.loads(line)
                        if 'original_chunk' in chunk_data:
                            all_final_lm_chunks_raw_text.append(chunk_data['original_chunk'])
                        else:
                            # Fallback if original_chunk not stored (e.g., reconstruct from tokens or skip)
                            pass # For now, skip if original_chunk isn't there
                _log(f"Loaded existing LM vocabulary with {len(current_vocab)} words and {len(all_final_lm_chunks_raw_text)} raw text chunks for LM.")
            except Exception as e:
                _log(f"Could not load existing LM data ({e}), starting new LM data.")
                current_vocab = {}
                all_final_lm_chunks_raw_text = []
    elif accumulation_mode == "Reset Knowledge (Overwrite)":
        _log("Resetting all knowledge bases (FAISS and custom LM data).")
        # Ensure directories are clean if resetting
        if os.path.exists(config.FAISS_INDEX_PATH): os.remove(config.FAISS_INDEX_PATH)
        if os.path.exists(config.FAISS_METADATA_PATH): os.remove(config.FAISS_METADATA_PATH)
        if os.path.exists(config.VOCAB_FILE): os.remove(config.VOCAB_FILE)
        if os.path.exists(config.TOKENIZED_CHUNKS_FILE): os.remove(config.TOKENIZED_CHUNKS_FILE)


    newly_processed_rag_chunks = []
    newly_processed_lm_chunks = []
    
    # Use content hashes of raw files to prevent re-processing files that are identical and already in the corpus
    # This is for deduplicating input files for current processing run
    processed_file_hashes = set()
    # If accumulating, you might want to also load hashes of files already incorporated from previous runs
    # For now, just track within this single execution.

    total_files = len(all_doc_filepaths)
    _log(f"Starting to process {total_files} current raw files for both FAISS and custom LM data.")

    for i, filepath in enumerate(all_doc_filepaths):
        filename = os.path.basename(filepath)
        if progress_callback:
            progress_callback(i, total_files, f"Reading & chunking {filename}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Use content hash to avoid re-processing identical files in the input list
            content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            if content_hash in processed_file_hashes:
                _log(f"Skipping identical content from {filename} in current input.")
                continue
            processed_file_hashes.add(content_hash)

            if text.strip():
                # For FAISS (RAG)
                rag_chunks = text_splitter_rag.split_text(text)
                newly_processed_rag_chunks.extend(rag_chunks)

                # For Custom Language Model
                lm_chunks = text_splitter_lm.split_text(text)
                newly_processed_lm_chunks.extend(lm_chunks)

        except Exception as e:
            _log(f"Failed to read or split file {filepath}: {e}")

    # Combine newly processed chunks with previously loaded ones (if in accumulate mode)
    # Note: This does not deduplicate chunks if the same chunk appears in previously loaded data
    # AND in the newly processed data. It only appends.
    all_final_rag_chunks.extend(newly_processed_rag_chunks)
    all_final_lm_chunks_raw_text.extend(newly_processed_lm_chunks)


    # --- Process for Custom Language Model (LM) ---
    if not all_final_lm_chunks_raw_text:
        _log("No text chunks could be created for custom language model training.");
    else:
        _log("Updating vocabulary for custom language model...")
        
        # Ensure special tokens are at the beginning and have consistent IDs
        if getattr(config, 'UNK_TOKEN', '<unk>') not in current_vocab: current_vocab[getattr(config, 'UNK_TOKEN', '<unk>')] = 0
        if getattr(config, 'PAD_TOKEN', '<pad>') not in current_vocab: current_vocab[getattr(config, 'PAD_TOKEN', '<pad>')] = 1
        
        # Build combined word counts from ALL accumulated raw LM chunks
        all_words_for_vocab = re.findall(r'\b\w+\b', " ".join(all_final_lm_chunks_raw_text).lower())
        word_counts_combined = Counter(all_words_for_vocab)
        
        current_id = max(current_vocab.values()) + 1 if current_vocab and current_vocab.values() else 2 # Start IDs from 2 if vocab not empty, else 2
        
        vocab_size_limit = getattr(config, 'VOCAB_SIZE', 20000)
        
        # Add new words to existing vocabulary, respecting vocab size limit
        for word, _ in word_counts_combined.most_common():
            if word not in current_vocab and len(current_vocab) < vocab_size_limit: # Check len(current_vocab) to limit size
                current_vocab[word] = current_id
                current_id += 1
            elif len(current_vocab) >= vocab_size_limit: # Stop adding if vocab limit reached
                break

        _log(f"Saving updated vocabulary ({len(current_vocab)} words) to {config.VOCAB_FILE}")
        os.makedirs(os.path.dirname(config.VOCAB_FILE), exist_ok=True)
        with open(config.VOCAB_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_vocab, f)
            
        setattr(config, 'PAD_TOKEN_ID', current_vocab[getattr(config, 'PAD_TOKEN', '<pad>')])
        setattr(config, 'UNK_TOKEN_ID', current_vocab[getattr(config, 'UNK_TOKEN', '<unk>')])

        _log("Tokenizing all accumulated chunks for custom language model...")
        tokenized_chunks_data = []
        for chunk in all_final_lm_chunks_raw_text:
            numerical_tokens = [current_vocab.get(word, getattr(config, 'UNK_TOKEN_ID', 0)) for word in re.findall(r'\b\w+\b', chunk.lower())]
            if numerical_tokens: 
                tokenized_chunks_data.append({"original_chunk": chunk, "numerical_tokens": numerical_tokens})

        _log(f"Saving tokenized chunks ({len(tokenized_chunks_data)} chunks) to {config.TOKENIZED_CHUNKS_FILE}")
        os.makedirs(os.path.dirname(config.TOKENIZED_CHUNKS_FILE), exist_ok=True)
        with open(config.TOKENIZED_CHUNKS_FILE, 'w', encoding='utf-8') as f:
            for item in tokenized_chunks_data:
                f.write(json.dumps(item) + '\n')
        _log(f"Generated {len(tokenized_chunks_data)} tokenized chunks for custom LM.")

    # --- Process for FAISS (RAG) ---
    if not all_final_rag_chunks:
        _log("No text chunks could be created for FAISS knowledge base.");
        # If no chunks at all, and no existing index, then we can't create one.
        if not (index_to_save and index_to_save.ntotal > 0):
            _log("No data for FAISS index, skipping creation/save.")
            if progress_callback:
                progress_callback(total_files, total_files, "FAISS processing skipped.")
            return

    # Only encode and add if there are actual NEW chunks processed in this run
    if newly_processed_rag_chunks:
        _log(f"Generating embeddings for {len(newly_processed_rag_chunks)} NEW text chunks for FAISS. This may take a while...")
        new_embeddings = model.encode(newly_processed_rag_chunks, show_progress_bar=True)

        if index_to_save: # If an existing index was loaded
            index_to_save.add(np.array(new_embeddings).astype('float32'))
            _log(f"Added {len(new_embeddings)} new embeddings to existing FAISS index. Total vectors: {index_to_save.ntotal}")
        else: # No existing index, create a new one with these embeddings
            index_to_save = faiss.IndexFlatL2(embedding_dim)
            index_to_save.add(np.array(new_embeddings).astype('float32'))
            _log(f"Created new FAISS index with {len(new_embeddings)} embeddings.")
    elif index_to_save: # No new chunks in this run, but an existing index was loaded
        _log("No new chunks to embed for FAISS. Using existing index.")
    else: # No new chunks, no existing index, nothing to do
        _log("No chunks found or generated for FAISS. No index created/updated.")
        return

    _log(f"Saving FAISS index ({index_to_save.ntotal} vectors) to {config.FAISS_INDEX_PATH}")
    os.makedirs(os.path.dirname(config.FAISS_INDEX_PATH), exist_ok=True)
    faiss.write_index(index_to_save, config.FAISS_INDEX_PATH)

    _log(f"Saving document chunks metadata ({len(all_final_rag_chunks)} chunks) to {config.FAISS_METADATA_PATH}")
    os.makedirs(os.path.dirname(config.FAISS_METADATA_PATH), exist_ok=True)
    with open(config.FAISS_METADATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_final_rag_chunks, f)

    if progress_callback:
        progress_callback(total_files, total_files, "Knowledge base processing complete.")
    _log(f"Preprocessing complete. FAISS index updated/created. Custom LM data generated.")

preprocess_documentation_for_ai = build_vector_db