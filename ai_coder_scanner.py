# ai_coder_scanner.py
import os
import subprocess
import pathspec
import config
import ollama_client
import torch # Import torch for own model inference
import train_language_model # To use your CoderAILanguageModel class
import json # To load vocab if needed by own model

def get_ignore_spec(scan_dir):
    """
    Loads ignore patterns from the default and project-specific .ai_coder_ignore files.
    Returns a PathSpec object for matching files.
    """
    patterns = []
    
    # Load default ignore file from the application's root directory
    app_root_dir = os.path.dirname(os.path.abspath(__file__))
    default_ignore_file = os.path.join(app_root_dir, '.ai_coder_ignore')
    if os.path.exists(default_ignore_file):
        with open(default_ignore_file, 'r', encoding='utf-8') as f:
            patterns.extend(f.readlines())

    # Load project-specific ignore file from the directory being scanned
    project_ignore_file = os.path.join(scan_dir, '.ai_coder_ignore')
    if os.path.exists(project_ignore_file):
        with open(project_ignore_file, 'r', encoding='utf-8') as f:
            patterns.extend(f.readlines())
    
    # Also, always ignore the AI Coder Assistant's own source code if it's nested
    patterns.append(app_root_dir + '/')
    
    # Create the spec object from the collected patterns
    return pathspec.PathSpec.from_lines('gitwildmatch', patterns)


# MODIFIED FUNCTION SIGNATURE to accept model_mode and model_ref
def scan_directory_for_errors(scan_dir, model_mode, model_ref, log_message_callback=None, progress_callback=None):
    _log = log_message_callback if callable(log_message_callback) else print

    try:
        # Get the compiled ignore specification
        ignore_spec = get_ignore_spec(scan_dir)

        all_filepaths = []
        for root, _, files in os.walk(scan_dir):
            for name in files:
                all_filepaths.append(os.path.join(root, name))
        
        # Filter the files using the ignore spec
        scannable_files = [
            path for path in all_filepaths
            if not ignore_spec.match_file(os.path.relpath(path, scan_dir))
        ]
        
        python_files = [f for f in scannable_files if f.endswith('.py')]

    except Exception as e:
        _log(f"Error while collecting files to scan: {e}")
        return {"Error": f"Could not collect files: {e}", "report": "# Scan Report\nError during file collection."}

    if not python_files:
        return {"Info": "No Python files found to scan.", "report": "# Scan Report\nNo scannable Python files found."}

    total_files = len(python_files)
    scan_results = {}
    _log(f"Found {total_files} Python files to scan.")

    for i, filepath in enumerate(python_files):
        if progress_callback:
            progress_callback(i, total_files, f"Scanning {os.path.basename(filepath)}")
        
        issues = run_flake8(filepath)
        if not issues: continue

        proposals = []
        for issue in issues:
            # Pass model_mode and model_ref to enhance_with_ollama
            suggestion = enhance_with_ollama(filepath, issue, model_mode, model_ref)
            if suggestion:
                proposals.append(suggestion)
        
        if proposals:
            scan_results[filepath] = {"proposals": proposals}

    report_content = generate_scan_report(scan_results)
    scan_results["report"] = report_content

    if progress_callback:
        progress_callback(total_files, total_files, "Scan complete. Report generated.")
    
    return scan_results

def run_flake8(filepath):
    try:
        result = subprocess.run(['flake8', filepath], capture_output=True, text=True, check=False)
        return [line for line in result.stdout.strip().split('\n') if line]
    except FileNotFoundError:
        return ["Flake8 not found. Please ensure it's installed (`pip install flake8`)."]
    except Exception as e:
        return [f"An error occurred while running flake8: {e}"]

# MODIFIED FUNCTION SIGNATURE to accept model_mode and model_ref
def enhance_with_ollama(filepath, issue_line, model_mode, model_ref):
    try:
        with open(filepath, 'r', encoding='utf-8') as f: lines = f.readlines()
        parts = issue_line.split(':');
        if len(parts) < 2 or not parts[1].isdigit(): return None
        line_index = int(parts[1]) - 1
        if not (0 <= line_index < len(lines)): return None
        original_code = lines[line_index].strip()
        
        # --- Conditional logic for model inference ---
        if model_mode == "ollama":
            # model_ref is the model_name string (e.g., "llama3:latest")
            prompt = (
                f"You are an expert Python linter and code corrector. "
                f"Analyze this Python code snippet from '{os.path.basename(filepath)}' which has a flake8 issue: '{issue_line}'.\n"
                f"Original code: ```python\n{original_code}\n```\n"
                f"Provide ONLY the single corrected line of code. Do NOT include any conversational text, explanations, or code block delimiters (` ``` `)."
            )
            suggestion = ollama_client.get_ollama_response(prompt, model_ref)
            if suggestion.startswith("API_ERROR:"): return None
            clean_suggestion = suggestion.strip()
        
        elif model_mode == "own_model":
            # model_ref is the loaded PyTorch model instance
            model = model_ref
            
            # --- IMPORTANT: THIS IS A SIMPLIFIED PLACEHOLDER ---
            # You need to implement proper tokenization and inference for your custom model here.
            # This is a significant piece of work.
            
            # Example placeholder:
            # You would typically load the vocab from config.VOCAB_FILE
            # vocab = json.load(open(config.VOCAB_FILE, 'r'))
            # And then use a tokenizer built during your training process to encode the prompt.
            # For a language model, the prompt might be "correct this code: ORIGINAL_CODE"
            # input_tokens = [vocab.get(token, vocab['<unk>']) for token in "some_tokenized_prompt_here".split()] # Simplified
            # input_tensor = torch.tensor([input_tokens], dtype=torch.long).to(train_language_model.get_best_device(print))
            
            # model.eval()
            # with torch.no_grad():
            #     outputs = model(input_tensor)
            #     # You would then decode outputs to get the generated text.
            #     # This decoding logic depends heavily on your model's output and your tokenizer.
            #     predicted_tokens = torch.argmax(outputs, dim=-1).squeeze().tolist()
            #     suggestion = YOUR_DECODER(predicted_tokens) # Implement your decoder
            
            clean_suggestion = f"Own model suggestion for: '{original_code}' (Issue: '{issue_line}'). (Inference logic not fully implemented yet)"
            # --- END PLACEHOLDER ---

        else:
            return None # Should not happen if modes are handled correctly

        # Ensure it's not empty and actually different
        if clean_suggestion and clean_suggestion != original_code:
            return {"line_number": line_index, "original_code": original_code, "proposed_code": clean_suggestion, "description": issue_line}
    except Exception as e:
        print(f"Enhancement failed ({model_mode}): {e}")
    return None

def generate_scan_report(scan_results_dict):
    report_lines = ["# AI Code Scan Report\n"]
    valid_results = {fp: res for fp, res in scan_results_dict.items() if res and res.get("proposals")}
    if not valid_results:
        report_lines.append("No actionable suggestions were found in the scanned files.")
        return "".join(report_lines)
    for filepath, results in valid_results.items():
        filename = os.path.basename(filepath)
        report_lines.append(f"## File: `{filename}`\n")
        for proposal in results["proposals"]:
            line_num = proposal['line_number'] + 1
            description = proposal['description']
            original_code = proposal['original_code']
            proposed_code = proposal['proposed_code']
            report_lines.append(f"### Issue at line {line_num}: `{description}`\n```diff\n- {original_code}\n+ {proposed_code}\n```\n")
    return "\n".join(report_lines)