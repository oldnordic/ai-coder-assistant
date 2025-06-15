# ai_coder_scanner.py
import os
import subprocess
import pathspec
import config
import ollama_client
import torch
from tokenizers import Tokenizer
import train_language_model

def get_ignore_spec(scan_dir):
    """Loads ignore patterns and returns a PathSpec object."""
    patterns = []
    app_root_dir = os.path.dirname(os.path.abspath(__file__))
    default_ignore_file = os.path.join(app_root_dir, '.ai_coder_ignore')
    if os.path.exists(default_ignore_file):
        with open(default_ignore_file, 'r', encoding='utf-8') as f:
            patterns.extend(f.readlines())
    project_ignore_file = os.path.join(scan_dir, '.ai_coder_ignore')
    if os.path.exists(project_ignore_file):
        with open(project_ignore_file, 'r', encoding='utf-8') as f:
            patterns.extend(f.readlines())
    patterns.append(os.path.join(app_root_dir, ''))
    return pathspec.PathSpec.from_lines('gitwildmatch', patterns)

def scan_directory_for_errors(scan_dir, model_mode, model_ref, log_message_callback=None, progress_callback=None):
    _log = log_message_callback if callable(log_message_callback) else print
    _progress = progress_callback if callable(progress_callback) else lambda c, t, m: None

    try:
        ignore_spec = get_ignore_spec(scan_dir)
        all_filepaths = [os.path.join(root, name) for root, _, files in os.walk(scan_dir) for name in files]
        scannable_files = [path for path in all_filepaths if not ignore_spec.match_file(os.path.relpath(path, scan_dir))]
        python_files = [f for f in scannable_files if f.endswith('.py')]
    except Exception as e:
        return {"Error": f"Could not collect files: {e}", "report": "# Scan Report\nError during file collection."}

    if not python_files:
        return {"Info": "No Python files found.", "report": "# Scan Report\nNo scannable Python files found."}

    total_files = len(python_files)
    scan_results = {}
    _log(f"Found {total_files} Python files to scan.")

    tokenizer = None
    tokenizer_path = os.path.join(config.VOCAB_DIR, "tokenizer.json")
    if model_mode == "own_model" and os.path.exists(tokenizer_path):
        _log("Loading custom tokenizer for inference.")
        tokenizer = Tokenizer.from_file(tokenizer_path)

    for i, filepath in enumerate(python_files):
        _progress(i, total_files, f"Scanning {os.path.basename(filepath)}")
        issues = run_flake8(filepath)
        if not issues: continue
        
        proposals = [enhance_suggestion(filepath, issue, model_mode, model_ref, tokenizer, _log) for issue in issues]
        proposals = [p for p in proposals if p]
        
        if proposals:
            scan_results[filepath] = {"proposals": proposals}

    scan_results["report"] = generate_scan_report(scan_results)
    _progress(total_files, total_files, "Scan complete. Report generated.")
    return scan_results

def run_flake8(filepath):
    try:
        result = subprocess.run(['flake8', filepath], capture_output=True, text=True, check=False)
        return [line for line in result.stdout.strip().split('\n') if line]
    except FileNotFoundError:
        return ["Flake8 not found. Please ensure it's installed (`pip install flake8`)."]
    except Exception as e:
        return [f"An error occurred while running flake8: {e}"]

def enhance_suggestion(filepath, issue_line, model_mode, model_ref, tokenizer, _log):
    """Generates a code suggestion using the selected model."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f: lines = f.readlines()
        parts = issue_line.split(':');
        if len(parts) < 2 or not parts[1].isdigit(): return None
        line_index = int(parts[1]) - 1
        if not (0 <= line_index < len(lines)): return None
        original_code = lines[line_index].strip()
        
        clean_suggestion = None
        if model_mode == "ollama":
            prompt = (f"You are an expert Python code corrector. Analyze the following Python code from '{os.path.basename(filepath)}' "
                      f"which has this flake8 issue: '{issue_line}'.\n\n"
                      f"Original code: ```python\n{original_code}\n```\n\n"
                      f"Provide ONLY the single corrected line of Python code. Do not include explanations, conversation, or markdown.")
            suggestion_text = ollama_client.get_ollama_response(prompt, model_ref)
            if not suggestion_text.startswith("API_ERROR:"):
                clean_suggestion = suggestion_text.strip().replace("`", "").replace("python", "").strip()

        elif model_mode == "own_model":
            if model_ref is None or tokenizer is None:
                return {"line_number": line_index, "original_code": original_code, "proposed_code": "# Own model or tokenizer not loaded.", "description": issue_line}
            
            prompt = f"### Bad Code: {original_code}\n### Good Code:"
            _log(f"Generating suggestion with own model for: '{original_code}'")
            
            input_ids = tokenizer.encode(prompt).ids
            input_tensor = torch.tensor([input_ids], dtype=torch.long).to(config.DEVICE)
            
            output_tokens = model_ref.generate(input_tensor, max_new_tokens=40)
            
            generated_ids = output_tokens[0][len(input_ids):]
            suggestion_text = tokenizer.decode(generated_ids)
            
            clean_suggestion = suggestion_text.split('\n')[0].strip()

        if clean_suggestion and clean_suggestion != original_code:
            return {"line_number": line_index, "original_code": original_code, "proposed_code": clean_suggestion, "description": issue_line}
            
    except Exception as e:
        _log(f"Enhancement failed ({model_mode}): {e}")
    return None

def generate_scan_report(scan_results_dict):
    report_lines = ["# AI Code Scan Report\n"]
    valid_results = {fp: res for fp, res in scan_results_dict.items() if res and res.get("proposals")}
    if not valid_results:
        report_lines.append("No actionable suggestions were found in the scanned files.")
        return "".join(report_lines)
    for filepath, results in valid_results.items():
        filename = os.path.basename(filepath)
        report_lines.append(f"\n## File: `{filename}`\n")
        for proposal in results["proposals"]:
            line_num = proposal['line_number'] + 1
            description = proposal['description']
            original_code = proposal['original_code']
            proposed_code = proposal['proposed_code']
            report_lines.append(f"### Issue at line {line_num}: `{description}`\n```diff\n- {original_code}\n+ {proposed_code}\n```\n")
    return "\n".join(report_lines)