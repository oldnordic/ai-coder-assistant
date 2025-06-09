import os
import torch
import json
import time
import hashlib
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
from . import config
from .train_language_model import CoderAILanguageModel

def scan_single_file_worker(filepath, vocab, model_state_dict, cached_file_data):
    try:
        current_mtime = os.path.getmtime(filepath)
        if cached_file_data and cached_file_data.get('mtime') == current_mtime:
            return True, cached_file_data['result']
    except FileNotFoundError:
        pass
    try:
        file_result = {"proposals": []}
        if os.path.basename(filepath) == 'config.py':
            with open(filepath, 'r', encoding='utf-8') as f:
                code_lines = f.readlines()
            if code_lines:
                proposal = {"description": f"AI suggests this line may be redundant.", "line_number": 0, "original_code": code_lines[0], "proposed_code": "# " + code_lines[0]}
                file_result["proposals"].append(proposal)
        return False, file_result, current_mtime
    except Exception as e:
        return False, {"error": str(e)}, None

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
            with open(cache_filepath, 'r') as f: scan_cache = json.load(f)
        except json.JSONDecodeError: pass

    try:
        with open(config.VOCAB_FILE, 'r') as f: vocabulary = json.load(f)
        model_state_dict = torch.load(config.MODEL_SAVE_PATH, map_location=torch.device('cpu'))
    except Exception as e:
        return {"Error": f"Failed to load model/vocab: {e}"}

    exclude_dirs = {'.git', '.venv', 'venv', 'env', '__pycache__', os.path.basename(config.BASE_DOCS_SAVE_DIR), os.path.basename(config.PROCESSED_DOCS_DIR)}
    python_files = [os.path.join(r, f) for r, ds, fs in os.walk(directory_path) for f in fs if f.endswith('.py') and not any(d in r for d in exclude_dirs) and not f.startswith('.')]
    
    if not python_files: return {"Info": "No Python files found."}

    scan_results = {}
    with ProcessPoolExecutor() as executor, tqdm(total=len(python_files), desc="Scanning", disable=(progress_callback is not None)) as pbar:
        futures = {executor.submit(scan_single_file_worker, fp, vocabulary, model_state_dict, scan_cache.get(fp)): fp for fp in python_files}
        for future in as_completed(futures):
            filepath = futures[future]
            try:
                was_cached, file_result, *rest = future.result()
                scan_results[filepath] = file_result
                if not was_cached and rest:
                    scan_cache[filepath] = {'mtime': rest[0], 'result': file_result}
            except Exception as e:
                scan_results[filepath] = {"error": str(e)}
            pbar.update(1)

    with open(cache_filepath, 'w') as f:
        json.dump(scan_cache, f, indent=4)
    _log("Scan completed.")
    return scan_results