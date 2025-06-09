import os
import torch
import json
import torch.nn as nn
import traceback
import hashlib
from concurrent.futures import ProcessPoolExecutor, as_completed
import config
from train_language_model import CoderAILanguageModel

def scan_single_file_worker(filepath, vocab, model_state_dict, cached_file_data):
    try:
        current_mtime = os.path.getmtime(filepath)
        if cached_file_data and cached_file_data.get('mtime') == current_mtime:
            return True, cached_file_data.get('result', {"proposals": []})
    except FileNotFoundError:
        return False, {"error": f"File not found during scan: {filepath}"}, None

    try:
        device = torch.device('cpu')
        vocab_size = len(vocab)
        model = CoderAILanguageModel(
            vocab_size=vocab_size,
            embed_dim=config.EMBED_DIM,
            num_heads=config.NUM_HEADS,
            num_layers=config.NUM_LAYERS,
            dropout=config.DROPOUT,
            max_seq_len=config.CHUNK_SIZE
        )
        model.load_state_dict(model_state_dict)
        model.to(device)
        model.eval()

        criterion = nn.CrossEntropyLoss()
        ERROR_THRESHOLD = 3.5
        file_result = {"proposals": []}

        with open(filepath, 'r', encoding='utf-8') as f:
            code_lines = f.readlines()

        for i, line_with_newline in enumerate(code_lines):
            line = line_with_newline.strip()
            if not line or line.startswith('#'):
                continue

            tokens = line.lower().split()
            if len(tokens) < 2:
                continue

            numerical_tokens = [vocab.get(token, vocab["<unk>"]) for token in tokens]
            padded_tokens = numerical_tokens[:config.CHUNK_SIZE] + [vocab["<pad>"]] * (config.CHUNK_SIZE - len(numerical_tokens))
            
            input_tensor = torch.tensor([padded_tokens[:-1]], dtype=torch.long, device=device)
            target_tensor = torch.tensor([padded_tokens[1:]], dtype=torch.long, device=device)

            with torch.no_grad():
                outputs = model(input_tensor)
                loss = criterion(outputs.view(-1, vocab_size), target_tensor.view(-1))
            
            if loss.item() > ERROR_THRESHOLD:
                proposal = {
                    "description": f"AI model found this line to be statistically unusual (loss: {loss.item():.2f}). It may contain a subtle error or be unconventional.",
                    "line_number": i,
                    "original_code": code_lines[i],
                    "proposed_code": f"# AI-REVIEW: This line was flagged as unusual.\n{code_lines[i]}"
                }
                file_result["proposals"].append(proposal)

        return False, file_result, current_mtime
    except Exception as e:
        return False, {"error": f"Failed to scan file {os.path.basename(filepath)}: {str(e)}\n{traceback.format_exc()}"}, None

def scan_directory_for_errors(directory_path, progress_callback=None, log_message_callback=None):
    _log = log_message_callback if callable(log_message_callback) else print
    if not os.path.isdir(directory_path):
        return {"Error": f"Directory not found: {directory_path}"}

    dir_hash = hashlib.md5(directory_path.encode('utf-8')).hexdigest()
    cache_filename = f"scan_cache_{dir_hash}.json"
    cache_filepath = os.path.join(config.PROCESSED_DOCS_DIR, cache_filename)
    _log(f"Using cache file: {cache_filename}")
    scan_cache = {}
    if os.path.exists(cache_filepath):
        try:
            with open(cache_filepath, 'r') as f:
                scan_cache = json.load(f)
        except json.JSONDecodeError:
            pass

    try:
        with open(config.VOCAB_FILE, 'r') as f:
            vocabulary = json.load(f)
        model_state_dict = torch.load(config.MODEL_SAVE_PATH, map_location=torch.device('cpu'))
    except Exception as e:
        return {"Error": f"Failed to load model/vocab for scanning: {e}"}

    exclude_dirs = {'.git', '.venv', 'venv', 'env', '__pycache__', os.path.basename(config.BASE_DOCS_SAVE_DIR), os.path.basename(config.PROCESSED_DOCS_DIR)}
    python_files = [os.path.join(r, f) for r, ds, fs in os.walk(directory_path) for f in fs if f.endswith('.py') and not any(d in r for d in exclude_dirs) and not f.startswith('.')]
    
    if not python_files:
        return {"Info": "No Python files found to scan in the selected directory."}

    scan_results = {}
    total_files = len(python_files)

    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(scan_single_file_worker, fp, vocabulary, model_state_dict, scan_cache.get(fp)): fp for fp in python_files}
        for i, future in enumerate(as_completed(futures)):
            filepath = futures[future]
            try:
                was_cached, file_result, *rest = future.result()
                scan_results[filepath] = file_result
                if not was_cached and rest:
                    scan_cache[filepath] = {'mtime': rest[0], 'result': file_result}
            except Exception as e:
                scan_results[filepath] = {"error": str(e)}
            
            if progress_callback:
                filename = os.path.basename(filepath)
                progress_callback(i + 1, total_files, f"Checking {i+1}/{total_files}: {filename}")

    with open(cache_filepath, 'w') as f:
        json.dump(scan_cache, f, indent=4)
    _log("Scan completed.")
    return scan_results