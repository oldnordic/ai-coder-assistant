import os
import re
import json
from tqdm import tqdm
from collections import Counter
from . import config

def clean_text(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def preprocess_documentation_for_ai(base_raw_docs_dir, processed_docs_dir, chunk_size, overlap_size, vocab_size,
                                    progress_callback=None, log_message_callback=None):
    _log = log_message_callback if callable(log_message_callback) else print
    if not os.path.exists(base_raw_docs_dir):
        _log(f"Error: Raw docs directory not found.")
        return
    if not os.path.exists(processed_docs_dir):
        os.makedirs(processed_docs_dir)

    all_doc_filepaths = [os.path.join(root, file) for root, _, files in os.walk(base_raw_docs_dir) for file in files if file.endswith('.txt')]
    if not all_doc_filepaths:
        _log("No text files found to preprocess.")
        return

    all_tokens_raw, all_text_chunks_metadata = [], []
    
    with tqdm(total=len(all_doc_filepaths), desc="Cleaning Docs", disable=(progress_callback is not None)) as pbar:
        for filepath in all_doc_filepaths:
            with open(filepath, 'r', encoding='utf-8') as f:
                tokens = clean_text(f.read()).split()
            all_tokens_raw.extend(tokens)
            for i in range(0, len(tokens), chunk_size - overlap_size):
                all_text_chunks_metadata.append({"chunk_text": ' '.join(tokens[i:i + chunk_size])})
            pbar.update(1)

    word_counts = Counter(all_tokens_raw)
    vocabulary = {"<pad>": 0, "<unk>": 1}
    vocabulary.update({word: i + 2 for i, (word, count) in enumerate(word_counts.most_common(vocab_size - 2))})
    
    with open(config.VOCAB_FILE, 'w', encoding='utf-8') as f:
        json.dump(vocabulary, f, indent=4)
    
    with open(config.TOKENIZED_CHUNKS_FILE, 'w', encoding='utf-8') as f_out:
        for chunk_data in all_text_chunks_metadata:
            numerical_tokens = [vocabulary.get(token, vocabulary["<unk>"]) for token in chunk_data["chunk_text"].split()]
            padded_tokens = numerical_tokens[:chunk_size] + [vocabulary["<pad>"]] * (chunk_size - len(numerical_tokens))
            f_out.write(json.dumps({"numerical_tokens": padded_tokens}) + '\n')
            
    _log("Preprocessing complete.")