# src/core/scanner.py
import os
import subprocess
import re
from typing import List, Tuple, Optional
import pathspec

# --- FIXED: Use relative imports for modules within the same package ---
from ..config import settings
from . import ai_tools, ollama_client

def _get_all_python_files(directory: str, log_message_callback: Optional[callable] = None) -> List[str]:
    _log = log_message_callback if callable(log_message_callback) else print
    ignore_file_path = os.path.join(settings.PROJECT_ROOT, '.ai_coder_ignore')
    patterns = []
    if os.path.exists(ignore_file_path):
        with open(ignore_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            patterns = f.readlines()
    vcs_ignores = ['.git/', '.svn/', '.hg/']
    for vcs_ignore in vcs_ignores:
        if vcs_ignore not in patterns:
            patterns.append(vcs_ignore)
    spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
    python_files = []
    for root, dirs, files in os.walk(directory, topdown=True):
        relative_root = os.path.relpath(root, directory)
        if relative_root == '.': relative_root = ''
        dir_paths_to_check = {os.path.join(relative_root, d).replace(os.sep, '/') for d in dirs}
        ignored_dir_paths = set(spec.match_files(dir_paths_to_check))
        ignored_dir_names = {os.path.basename(p.strip('/')) for p in ignored_dir_paths}
        dirs[:] = [d for d in dirs if d not in ignored_dir_names]
        for filename in files:
            if filename.endswith('.py'):
                relative_file_path = os.path.join(relative_root, filename).replace(os.sep, '/')
                if not spec.match_file(relative_file_path):
                    python_files.append(os.path.join(root, filename))
    return python_files

def run_flake8(filepath: str) -> List[str]:
    try:
        result = subprocess.run(['flake8', filepath], capture_output=True, text=True, check=False)
        return result.stdout.strip().split('\n') if result.stdout else []
    except FileNotFoundError:
        return ["flake8 command not found. Please ensure it's installed and in your PATH."]
    except Exception as e:
        return [f"An error occurred while running flake8: {e}"]

def parse_flake8_output(line: str) -> Optional[Tuple[int, str]]:
    match = re.match(r'.*:(\d+):\d+: (.*)', line)
    if match:
        return int(match.group(1)), match.group(2).strip()
    return None

def get_code_context(filepath: str, line_number: int, context_lines: int = 3) -> str:
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        start_index = max(0, line_number - 1 - context_lines)
        end_index = min(len(lines), line_number + context_lines)
        
        return "".join(lines[start_index:end_index])
    except Exception:
        return ""

def enhance_code(
    filepath: str, 
    issue_line: str,
    model_mode: str,
    model_ref: any,
    tokenizer_ref: any = None,
    log_message_callback: Optional[callable] = None
) -> str:
    try:
        parsed_issue = parse_flake8_output(issue_line)
        if not parsed_issue: return f"Could not parse issue: {issue_line}"
        
        line_num, issue_msg = parsed_issue
        
        original_code_line = get_code_context(filepath, line_num, context_lines=0).strip()
        if not original_code_line: return "Could not read code context from file."

        if model_mode == "ollama":
            code_context = get_code_context(filepath, line_num, context_lines=5)
            prompt = (
                f"Analyze the following Python code snippet from file '{os.path.basename(filepath)}'.\n"
                f"An issue was detected near or on line {line_num}: {issue_msg}\n\n"
                f"### Code Snippet (with comments):\n```python\n{code_context}\n```\n\n"
                f"Based on the surrounding code and comments, provide only the single corrected line of Python code to fix the issue."
            )
            suggestion = ollama_client.get_ollama_response(prompt, model_ref)
            code_blocks = re.findall(r"```python\n(.*?)\n```", suggestion, re.DOTALL)
            clean_suggestion = code_blocks[0].strip() if code_blocks else suggestion.strip()
        
        elif model_mode == "own_model":
            prompt = f"[BAD_CODE] {original_code_line} [GOOD_CODE]"
            
            clean_suggestion = ai_tools.generate_with_own_model(
                model=model_ref,
                tokenizer=tokenizer_ref,
                prompt=prompt
            )
        else:
            clean_suggestion = f"Unknown model mode: {model_mode}"

        return clean_suggestion.replace("\\n", "\n")

    except Exception as e:
        if log_message_callback: log_message_callback(f"Error enhancing code: {e}")
        return f"Error: {e}"

def scan_code(
    directory: str, 
    model_mode: str, 
    model_ref: any,
    tokenizer_ref: any,
    progress_callback: Optional[callable] = None,
    log_message_callback: Optional[callable] = None
) -> List[dict]:
    _log = log_message_callback if callable(log_message_callback) else print
    
    _log(f"Starting code scan in '{directory}' using '{model_mode}' model.")
    python_files = _get_all_python_files(directory, log_message_callback=_log)
    _log(f"Found {len(python_files)} Python files to scan.")
    
    all_issues = []
    total_files = len(python_files)
    for i, filepath in enumerate(python_files):
        if progress_callback: progress_callback(i + 1, total_files, f"Scanning {os.path.relpath(filepath, directory)}")
        
        issues = run_flake8(filepath)
        if not (issues and issues[0]): continue
            
        for issue_line in issues:
            parsed = parse_flake8_output(issue_line)
            if not parsed: continue
            
            line_num, _ = parsed
            original_code_line = get_code_context(filepath, line_num, context_lines=0)
            
            suggestion = enhance_code(
                filepath, 
                issue_line, 
                model_mode, 
                model_ref,
                tokenizer_ref,
                log_message_callback=_log
            )
            all_issues.append({
                'filepath': filepath,
                'line_number': line_num - 1,
                'description': issue_line,
                'original_code': original_code_line.strip(),
                'proposed_code': suggestion
            })

    if progress_callback: progress_callback(total_files, total_files, "Scan complete.")
    _log("Code scan completed.")
    return all_issues