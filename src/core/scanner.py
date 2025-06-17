# src/core/scanner.py
import os
import subprocess
import re
from typing import List, Tuple, Optional, Dict
import pathspec

# --- FIXED: Use relative imports for modules within the same package ---
from ..config import settings
from . import ai_tools, ollama_client

# Define the 20 most used programming languages with their file extensions and linters
SUPPORTED_LANGUAGES = {
    'python': {
        'extensions': ['.py', '.pyw', '.pyx', '.pyi'],
        'linter': 'flake8',
        'linter_args': [],
        'language_name': 'Python'
    },
    'javascript': {
        'extensions': ['.js', '.jsx', '.mjs'],
        'linter': 'eslint',
        'linter_args': ['--format=compact'],
        'language_name': 'JavaScript'
    },
    'typescript': {
        'extensions': ['.ts', '.tsx'],
        'linter': 'eslint',
        'linter_args': ['--format=compact'],
        'language_name': 'TypeScript'
    },
    'java': {
        'extensions': ['.java'],
        'linter': 'checkstyle',
        'linter_args': ['-c', 'google_checks.xml'],
        'language_name': 'Java'
    },
    'c': {
        'extensions': ['.c', '.h'],
        'linter': 'cppcheck',
        'linter_args': ['--enable=all', '--xml'],
        'language_name': 'C'
    },
    'cpp': {
        'extensions': ['.cpp', '.cc', '.cxx', '.hpp', '.hh', '.hxx'],
        'linter': 'cppcheck',
        'linter_args': ['--enable=all', '--xml'],
        'language_name': 'C++'
    },
    'csharp': {
        'extensions': ['.cs'],
        'linter': 'dotnet',
        'linter_args': ['format', '--verify-no-changes'],
        'language_name': 'C#'
    },
    'go': {
        'extensions': ['.go'],
        'linter': 'golangci-lint',
        'linter_args': ['run'],
        'language_name': 'Go'
    },
    'rust': {
        'extensions': ['.rs'],
        'linter': 'cargo',
        'linter_args': ['clippy', '--message-format=short'],
        'language_name': 'Rust'
    },
    'php': {
        'extensions': ['.php'],
        'linter': 'phpcs',
        'linter_args': ['--standard=PSR12'],
        'language_name': 'PHP'
    },
    'ruby': {
        'extensions': ['.rb'],
        'linter': 'rubocop',
        'linter_args': ['--format=simple'],
        'language_name': 'Ruby'
    },
    'swift': {
        'extensions': ['.swift'],
        'linter': 'swiftlint',
        'linter_args': ['lint'],
        'language_name': 'Swift'
    },
    'kotlin': {
        'extensions': ['.kt', '.kts'],
        'linter': 'ktlint',
        'linter_args': ['--format=plain'],
        'language_name': 'Kotlin'
    },
    'scala': {
        'extensions': ['.scala'],
        'linter': 'scalafmt',
        'linter_args': ['--test'],
        'language_name': 'Scala'
    },
    'dart': {
        'extensions': ['.dart'],
        'linter': 'dart',
        'linter_args': ['analyze'],
        'language_name': 'Dart'
    },
    'r': {
        'extensions': ['.r', '.R'],
        'linter': 'lintr',
        'linter_args': [],
        'language_name': 'R'
    },
    'matlab': {
        'extensions': ['.m'],
        'linter': 'mlint',
        'linter_args': [],
        'language_name': 'MATLAB'
    },
    'shell': {
        'extensions': ['.sh', '.bash', '.zsh', '.fish'],
        'linter': 'shellcheck',
        'linter_args': ['--format=gcc'],
        'language_name': 'Shell'
    },
    'sql': {
        'extensions': ['.sql'],
        'linter': 'sqlfluff',
        'linter_args': ['lint'],
        'language_name': 'SQL'
    },
    'html': {
        'extensions': ['.html', '.htm'],
        'linter': 'htmlhint',
        'linter_args': [],
        'language_name': 'HTML'
    }
}

def _get_all_code_files(directory: str, log_message_callback: Optional[callable] = None) -> Dict[str, List[str]]:
    """
    Get all code files organized by language from the given directory.
    """
    _log = log_message_callback if callable(log_message_callback) else print
    ignore_file_path = os.path.join(settings.PROJECT_ROOT, '.ai_coder_ignore')
    patterns = []
    if os.path.exists(ignore_file_path):
        with open(ignore_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            patterns = f.readlines()
    
    # Add common VCS and build directories to ignore
    vcs_ignores = ['.git/', '.svn/', '.hg/', 'node_modules/', 'vendor/', 'build/', 'dist/', '__pycache__/']
    for vcs_ignore in vcs_ignores:
        if vcs_ignore not in patterns:
            patterns.append(vcs_ignore)
    
    spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
    
    # Initialize result dictionary
    language_files = {lang: [] for lang in SUPPORTED_LANGUAGES.keys()}
    
    for root, dirs, files in os.walk(directory, topdown=True):
        relative_root = os.path.relpath(root, directory)
        if relative_root == '.': 
            relative_root = ''
        
        # Check which directories should be ignored
        dir_paths_to_check = {os.path.join(relative_root, d).replace(os.sep, '/') for d in dirs}
        ignored_dir_paths = set(spec.match_files(dir_paths_to_check))
        ignored_dir_names = {os.path.basename(p.strip('/')) for p in ignored_dir_paths}
        dirs[:] = [d for d in dirs if d not in ignored_dir_names]
        
        for filename in files:
            file_ext = os.path.splitext(filename)[1].lower()
            relative_file_path = os.path.join(relative_root, filename).replace(os.sep, '/')
            
            # Skip if file is ignored
            if spec.match_file(relative_file_path):
                continue
            
            # Check if file extension matches any supported language
            for lang, config in SUPPORTED_LANGUAGES.items():
                if file_ext in config['extensions']:
                    language_files[lang].append(os.path.join(root, filename))
                    break
    
    # Log summary
    total_files = sum(len(files) for files in language_files.values())
    _log(f"Found {total_files} code files across {len([lang for lang, files in language_files.items() if files])} languages:")
    for lang, files in language_files.items():
        if files:
            _log(f"  {SUPPORTED_LANGUAGES[lang]['language_name']}: {len(files)} files")
    
    return language_files

def run_linter(filepath: str, language: str) -> List[str]:
    """
    Run the appropriate linter for the given file and language.
    """
    if language not in SUPPORTED_LANGUAGES:
        return [f"Unsupported language: {language}"]
    
    config = SUPPORTED_LANGUAGES[language]
    linter = config['linter']
    args = config['linter_args']
    
    try:
        # Special handling for different linters
        if linter == 'flake8':
            result = subprocess.run(['flake8', filepath], capture_output=True, text=True, check=False)
        elif linter == 'eslint':
            result = subprocess.run(['eslint', filepath] + args, capture_output=True, text=True, check=False)
        elif linter == 'cppcheck':
            result = subprocess.run(['cppcheck', filepath] + args, capture_output=True, text=True, check=False)
        elif linter == 'dotnet':
            result = subprocess.run(['dotnet', 'format', filepath, '--verify-no-changes'], capture_output=True, text=True, check=False)
        elif linter == 'golangci-lint':
            result = subprocess.run(['golangci-lint', 'run', filepath] + args, capture_output=True, text=True, check=False)
        elif linter == 'cargo':
            result = subprocess.run(['cargo', 'clippy', '--message-format=short'], capture_output=True, text=True, check=False, cwd=os.path.dirname(filepath))
        elif linter == 'phpcs':
            result = subprocess.run(['phpcs', filepath] + args, capture_output=True, text=True, check=False)
        elif linter == 'rubocop':
            result = subprocess.run(['rubocop', filepath] + args, capture_output=True, text=True, check=False)
        elif linter == 'swiftlint':
            result = subprocess.run(['swiftlint', 'lint', filepath] + args, capture_output=True, text=True, check=False)
        elif linter == 'ktlint':
            result = subprocess.run(['ktlint', filepath] + args, capture_output=True, text=True, check=False)
        elif linter == 'scalafmt':
            result = subprocess.run(['scalafmt', '--test', filepath] + args, capture_output=True, text=True, check=False)
        elif linter == 'dart':
            result = subprocess.run(['dart', 'analyze', filepath] + args, capture_output=True, text=True, check=False)
        elif linter == 'shellcheck':
            result = subprocess.run(['shellcheck', filepath] + args, capture_output=True, text=True, check=False)
        elif linter == 'sqlfluff':
            result = subprocess.run(['sqlfluff', 'lint', filepath] + args, capture_output=True, text=True, check=False)
        elif linter == 'htmlhint':
            result = subprocess.run(['htmlhint', filepath] + args, capture_output=True, text=True, check=False)
        else:
            return [f"Linter '{linter}' not implemented yet"]
        
        if result.stdout:
            return result.stdout.strip().split('\n')
        elif result.stderr:
            return result.stderr.strip().split('\n')
        else:
            return []
            
    except FileNotFoundError:
        return [f"{linter} command not found. Please ensure it's installed and in your PATH."]
    except Exception as e:
        return [f"An error occurred while running {linter}: {e}"]

def parse_linter_output(line: str, language: str) -> Optional[Tuple[int, str]]:
    """
    Parse linter output to extract line number and issue description.
    Handles different output formats for different linters.
    """
    if language == 'python':
        # flake8 format: file:line:col: code message
        match = re.match(r'.*:(\d+):\d+: (.*)', line)
    elif language in ['javascript', 'typescript']:
        # eslint format: file:line:col: message
        match = re.match(r'.*:(\d+):\d+: (.*)', line)
    elif language in ['c', 'cpp']:
        # cppcheck format: file:line: severity: message
        match = re.match(r'.*:(\d+): (.*)', line)
    elif language == 'shell':
        # shellcheck format: file:line:col: severity: message
        match = re.match(r'.*:(\d+):\d+: (.*)', line)
    else:
        # Generic format: try to extract line number
        match = re.match(r'.*:(\d+).*: (.*)', line)
    
    if match:
        return int(match.group(1)), match.group(2).strip()
    return None

def get_code_context(filepath: str, line_number: int, context_lines: int = 3) -> str:
    """
    Get code context around the specified line number.
    """
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
    language: str,
    model_mode: str,
    model_ref: any,
    tokenizer_ref: any = None,
    log_message_callback: Optional[callable] = None
) -> str:
    """
    Enhance code by getting AI suggestions for the detected issue.
    """
    try:
        parsed_issue = parse_linter_output(issue_line, language)
        if not parsed_issue: 
            return f"Could not parse issue: {issue_line}"
        
        line_num, issue_msg = parsed_issue
        original_code_line = get_code_context(filepath, line_num, context_lines=0).strip()
        if not original_code_line: 
            return "Could not read code context from file."

        if model_mode == "ollama":
            code_context = get_code_context(filepath, line_num, context_lines=5)
            language_name = SUPPORTED_LANGUAGES[language]['language_name']
            prompt = (
                f"Analyze the following {language_name} code snippet from file '{os.path.basename(filepath)}'.\n"
                f"An issue was detected near or on line {line_num}: {issue_msg}\n\n"
                f"### Code Snippet (with comments):\n```{language}\n{code_context}\n```\n\n"
                f"Based on the surrounding code and comments, provide only the single corrected line of {language_name} code to fix the issue."
            )
            suggestion = ollama_client.get_ollama_response(prompt, model_ref)
            code_blocks = re.findall(rf"```{language}\n(.*?)\n```", suggestion, re.DOTALL)
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
    Scan code in the given directory for issues across all supported languages.
    """
    _log = log_message_callback if callable(log_message_callback) else print
    
    _log(f"Starting multi-language code scan in '{directory}' using '{model_mode}' model.")
    language_files = _get_all_code_files(directory, log_message_callback=_log)
    
    all_issues = []
    total_files = sum(len(files) for files in language_files.values())
    processed_files = 0
    
    for language, files in language_files.items():
        if not files:
            continue
            
        _log(f"Scanning {len(files)} {SUPPORTED_LANGUAGES[language]['language_name']} files...")
        
        for filepath in files:
            processed_files += 1
            if progress_callback: 
                progress_callback(processed_files, total_files, f"Scanning {os.path.relpath(filepath, directory)}")
            
            issues = run_linter(filepath, language)
            if not (issues and issues[0]): 
                continue
                
            for issue_line in issues:
                parsed = parse_linter_output(issue_line, language)
                if not parsed: 
                    continue
                
                line_num, _ = parsed
                original_code_line = get_code_context(filepath, line_num, context_lines=0)
                
                suggestion = enhance_code(
                    filepath, 
                    issue_line, 
                    language,
                    model_mode, 
                    model_ref,
                    tokenizer_ref,
                    log_message_callback=_log
                )
                all_issues.append({
                    'file_path': filepath,
                    'line_number': line_num - 1,
                    'description': issue_line,
                    'code_snippet': original_code_line.strip(),
                    'suggested_improvement': suggestion,
                    'language': language
                })

    if progress_callback: 
        progress_callback(total_files, total_files, "Scan complete.")
    _log(f"Multi-language code scan completed. Found {len(all_issues)} issues across {len(set(issue['language'] for issue in all_issues))} languages.")
    return all_issues