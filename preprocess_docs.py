# preprocess_docs.py
import os
import json
from bs4 import BeautifulSoup
import html
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import config

def parse_html_report(html_path):
    """Parses a generated HTML report to extract suggestion pairs."""
    if not os.path.exists(html_path):
        return []
    
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    suggestions = []
    for suggestion_div in soup.find_all('div', class_='suggestion'):
        try:
            issue = suggestion_div.find('h3').text.replace('Issue: ', '').strip()
            original_code = suggestion_div.find('div', class_='original').text.strip()
            original_code = html.unescape(original_code)
            
            proposed_code_element = suggestion_div.find('div', class_='proposed')
            proposed_code = proposed_code_element.text.strip()
            proposed_code = html.unescape(proposed_code)
            
            if '```' in proposed_code:
                code_parts = proposed_code.split('```')
                if len(code_parts) > 1:
                    proposed_code = code_parts[1].replace('python', '').strip()
                else:
                    proposed_code = code_parts[0].strip()

            if original_code and proposed_code and "logic not fully implemented" not in proposed_code:
                suggestions.append({
                    'issue': issue,
                    'original_code': original_code,
                    'user_feedback_or_code': proposed_code
                })
        except (AttributeError, IndexError):
            continue
    return suggestions

def build_vector_db(docs_dir, index_path, metadata_path, reset_db=True, **kwargs):
    log_message_callback = kwargs.get('log_message_callback', print)
    progress_callback = kwargs.get('progress_callback', lambda c, t, m: None)

    try:
        log_message_callback("Starting document preprocessing...")
        if reset_db:
            for path in [index_path, metadata_path, config.CONCAT_FILE_PATH, config.FINETUNING_FILE_PATH]:
                if os.path.exists(path):
                    os.remove(path)
                    log_message_callback(f"Removed existing file: {os.path.basename(path)}")
        
        all_chunks = []
        files_to_process = [f for f in os.listdir(docs_dir) if os.path.isfile(os.path.join(docs_dir, f))]
        with open(config.CONCAT_FILE_PATH, 'a', encoding='utf-8') as concat_file:
            for i, filename in enumerate(files_to_process):
                progress_callback(i, len(files_to_process), f"Processing doc: {filename}")
                filepath = os.path.join(docs_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                concat_file.write(content + "\n")
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
                all_chunks.extend(text_splitter.split_text(content))
        
        finetuning_examples = []
        if os.path.exists(config.LEARNING_DATA_FILE):
            with open(config.LEARNING_DATA_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    try: finetuning_examples.append(json.loads(line))
                    except json.JSONDecodeError: continue
        
        # Check for both possible report names
        ollama_report_path1 = os.path.join(config.PROJECT_ROOT, 'olamma_coder1.5_ai_code_review_report.html')
        ollama_report_path2 = os.path.join(config.PROJECT_ROOT, 'Own_trained_model_ai_code_review_report.html')
        if os.path.exists(ollama_report_path1):
            finetuning_examples.extend(parse_html_report(ollama_report_path1))
        if os.path.exists(ollama_report_path2):
            finetuning_examples.extend(parse_html_report(ollama_report_path2))
        
        if finetuning_examples:
            with open(config.FINETUNING_FILE_PATH, 'w', encoding='utf-8') as f:
                for entry in finetuning_examples:
                    instruction = f"### Issue: {entry.get('issue', 'N/A')}"
                    original = f"### Bad Code: {entry.get('original_code', '')}"
                    corrected = f"### Good Code: {entry.get('user_feedback_or_code', entry.get('ai_proposed_code', ''))}"
                    f.write(f"{instruction}\n{original}\n{corrected}\n\n")
            log_message_callback(f"Created finetuning dataset with {len(finetuning_examples)} examples.")
        else:
            log_message_callback("No feedback or report data found. Skipping finetuning dataset creation.")

        if not all_chunks:
            log_message_callback("No text chunks found for vector DB.")
        else:
            progress_callback(50, 100, "Embedding chunks for Vector DB...")
            model = SentenceTransformer(config.EMBEDDING_MODEL_NAME, device=config.DEVICE)
            embeddings = model.encode(all_chunks, show_progress_bar=True, device=config.DEVICE)
            index = faiss.IndexFlatL2(embeddings.shape[1])
            index.add(np.array(embeddings).astype('float32'))
            faiss.write_index(index, index_path)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(all_chunks, f)
        
        log_message_callback("Preprocessing complete.")
        progress_callback(100, 100, "Preprocessing complete!")
        return "Success"
    except Exception as e:
        log_message_callback(f"An error occurred during preprocessing: {e}")
        return f"Error: {e}"