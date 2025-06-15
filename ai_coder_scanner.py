# ai_coder_scanner.py
import os
import subprocess
import re
from typing import List, Tuple, Optional
import torch
from tokenizers import Tokenizer
from torch import nn
import train_language_model
import pathspec
import config
import ai_tools

from ollama_client import enhance_with_ollama

def _get_all_python_files(directory: str, log_message_callback: Optional[callable] = None) -> List[str]:
    """
    Walks a directory and returns a list of all Python files, respecting
    the patterns in the .ai_coder_ignore file, with verbose logging.
    """
    _log = log_message_callback if callable(log_message_callback) else print
    ignore_file_path = os.path.join(config.PROJECT_ROOT, '.ai_coder_ignore')
    patterns = []
    if os.path.exists(ignore_file_path):
        _log(f"Found '.ai_coder_ignore' at: {ignore_file_path}")
        with open(ignore_file_path, 'r', encoding='utf-8') as f:
            patterns = f.readlines()
        _log(f"Loaded {len(patterns)} patterns from .ai_coder_ignore:")
        for pattern_line in patterns:
            if pattern_line.strip() and not pattern_line.strip().startswith('#'):
                 _log(f"  - Using pattern: '{pattern_line.strip()}'")
    else:
        _log(f"'.ai_coder_ignore' not found at {ignore_file_path}. Will not ignore any custom files.")
    
    vcs_ignores = ['.git/', '.svn/', '.hg/']
    for vcs_ignore in vcs_ignores:
        if vcs_ignore not in patterns:
            patterns.append(vcs_ignore)

    spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
    python_files = []
    _log("--- Starting File Scan ---")
    for root, dirs, files in os.walk(directory, topdown=True):
        relative_root = os.path.relpath(root, directory)
        if relative_root == '.':
            relative_root = ''
        dir_paths_to_check = {os.path.join(relative_root, d).replace(os.sep, '/') for d in dirs}
        ignored_dir_paths = set(spec.match_files(dir_paths_to_check))
        ignored_dir_names = {os.path.basename(p.strip('/')) for p in ignored_dir_paths}
        if ignored_dir_names:
            _log(f"In '{relative_root or './'}', ignoring subdirectories: {ignored_dir_names}")
        dirs[:] = [d for d in dirs if d not in ignored_dir_names]
        for filename in files:
            if filename.endswith('.py'):
                relative_file_path = os.path.join(relative_root, filename).replace(os.sep, '/')
                if spec.match_file(relative_file_path):
                    _log(f"  - Ignoring file: {relative_file_path}")
                else:
                    _log(f"  + Including file: {relative_file_path}")
                    python_files.append(os.path.join(root, filename))
    _log("--- File Scan Complete ---")
    return python_files

def run_flake8(filepath: str) -> List[str]:
    """Runs flake8 on a given file and returns the output lines."""
    try:
        result = subprocess.run(
            ['flake8', filepath],
            capture_output=True,
            text=True,
            check=False 
        )
        return result.stdout.strip().split('\n') if result.stdout else []
    except FileNotFoundError:
        return ["flake8 command not found. Please ensure it's installed and in your PATH."]
    except Exception as e:
        return [f"An error occurred while running flake8: {e}"]

def parse_flake8_output(line: str) -> Optional[Tuple[int, str]]:
    """Parses a single line of flake8 output to extract line number and message."""
    match = re.match(r'.*:(\d+):\d+: (.*)', line)
    if match:
        return int(match.group(1)), match.group(2)
    return None

def get_code_context(filepath: str, line_number: int, context_lines: int = 0) -> str:
    """Extracts a few lines of code around the specified line number."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if context_lines == 0 and 0 <= line_number - 1 < len(lines):
             return lines[line_number - 1]
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        return "".join(lines[start:end])
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
    """
    Enhances a line of code using either Ollama or the custom model.
    """
    try:
        parsed_issue = parse_flake8_output(issue_line)
        if not parsed_issue:
            return f"Could not parse issue: {issue_line}"
        
        line_num, issue_msg = parsed_issue
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if not (0 < line_num <= len(lines)):
            return "Invalid line number from flake8."
        original_code = lines[line_num - 1].strip()

        if model_mode == "ollama":
            suggestion = enhance_with_ollama(filepath, issue_line, model_ref)
            code_blocks = re.findall(r"```python\n(.*?)\n```", suggestion, re.DOTALL)
            clean_suggestion = code_blocks[0].strip() if code_blocks else suggestion.strip()
        
        elif model_mode == "own_model":
            prompt = (
                f"Fix the following Python code snippet.\n"
                f"Issue: {issue_msg}\n"
                f"Original Code:\n---\n{original_code}\n---\n"
                f"Suggested Fix:\n---\n"
            )
            clean_suggestion = ai_tools.generate_with_own_model(
                model=model_ref,
                tokenizer=tokenizer_ref,
                prompt=prompt
            )
        else:
            clean_suggestion = f"Unknown model mode: {model_mode}"

        return clean_suggestion.replace("\\n", "\n")

    except Exception as e:
        if log_message_callback:
            log_message_callback(f"Error enhancing code: {e}")
        return f"Error: {e}"

def scan_code(
    directory: str, 
    model_mode: str, 
    model_ref: any,
    tokenizer_ref: any,
    progress_callback: Optional[callable] = None,
    log_message_callback: Optional[callable] = None
) -> List[dict]:
    """
    Scans a directory for Python files, runs flake8, and gets AI suggestions.
    """
    _log = log_message_callback if callable(log_message_callback) else print
    _log(f"Starting code scan in '{directory}' using '{model_mode}' model.")
    python_files = _get_all_python_files(directory, log_message_callback=_log)
    _log(f"Found {len(python_files)} Python files to scan.")
    
    all_issues = []
    total_files = len(python_files)
    for i, filepath in enumerate(python_files):
        if progress_callback:
            progress_callback(i, total_files, f"Scanning {os.path.relpath(filepath, directory)}")
        issues = run_flake8(filepath)
        if not (issues and issues[0]):
            continue
        for issue_line in issues:
            parsed = parse_flake8_output(issue_line)
            if not parsed: continue
            line_num, _ = parsed
            original_code = get_code_context(filepath, line_num, 0)
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
                'original_code': original_code.strip(),
                'proposed_code': suggestion
            })

    if progress_callback:
        progress_callback(total_files, total_files, "Scan complete.")
    _log("Code scan completed.")
    return all_issues