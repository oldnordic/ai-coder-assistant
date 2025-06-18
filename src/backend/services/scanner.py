"""
scanner.py

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2024 AI Coder Assistant Contributors
"""

# src/core/scanner.py
import os
import subprocess
import re
from typing import List, Tuple, Optional, Dict, Callable, Any
import pathspec
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

# --- FIXED: Use relative imports for modules within the same package ---
from ..utils import settings
from . import ai_tools, ollama_client
from .intelligent_analyzer import IntelligentCodeAnalyzer, CodeIssue, IssueType
from ..utils.constants import (
    MAX_CONTENT_SIZE, MAX_DESCRIPTION_LENGTH, MAX_CODE_SNIPPET_LENGTH, 
    MAX_SUGGESTION_LENGTH, MAX_ERROR_MESSAGE_LENGTH, MAX_PROMPT_LENGTH,
    MAX_FILE_SIZE_KB, MAX_FILE_SIZE, MAX_FILENAME_LENGTH,
    MAX_CODE_CONTEXT_LENGTH
)

# File size conversion constant
BYTES_PER_KB = 1024

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

# Add thread lock for linter execution at the top of the file
linter_lock = threading.Lock()

def _get_all_code_files(directory: str, log_message_callback: Optional[Callable[[str], None]] = None) -> Dict[str, List[str]]:
    """
    Get all code files in the directory, organized by language.
    Respects .gitignore patterns and file size limits.
    """
    def _log(message: str):
        if log_message_callback:
            log_message_callback(message)
    
    # Load .gitignore patterns
    gitignore_path = os.path.join(directory, '.gitignore')
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            patterns = f.readlines()
    
    # Add common patterns to ignore
    patterns.extend([
        '*.pyc\n',
        '__pycache__\n',
        '.git\n',
        'node_modules\n',
        'venv\n',
        '.venv\n',
        'env\n',
        '.env\n',
        '*.log\n',
        '*.tmp\n',
        '*.temp\n',
        'build\n',
        'dist\n',
        '.pytest_cache\n',
        '.coverage\n',
        '*.egg-info\n',
        '.mypy_cache\n',
        '.ruff_cache\n',
        '.flake8_cache\n',
        '*.swp\n',
        '*.swo\n',
        '*~\n',
        '.DS_Store\n',
        'Thumbs.db\n'
    ])
    
    spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
    
    # Initialize result dictionary
    language_files = {lang: [] for lang in SUPPORTED_LANGUAGES.keys()}
    
    # File size limit (1MB) to prevent memory issues
    # MAX_FILE_SIZE is now imported from constants
    
    for root, dirs, files in os.walk(directory, topdown=True):
        relative_root = os.path.relpath(root, directory)
        if relative_root == '.': 
            relative_root = ''
        
        # Check which directories should be ignored
        dir_paths_to_check = {os.path.join(relative_root, d).replace(os.sep, '/') for d in dirs}
        ignored_dir_paths = set(spec.match_files(dir_paths_to_check))
        ignored_dir_names = {os.path.basename(str(p).strip('/')) for p in ignored_dir_paths}
        dirs[:] = [d for d in dirs if d not in ignored_dir_names]
        
        for filename in files:
            file_ext = os.path.splitext(filename)[1].lower()
            relative_file_path = os.path.join(relative_root, filename).replace(os.sep, '/')
            
            # Skip if file is ignored
            if spec.match_file(relative_file_path):
                continue
            
            # Check file size
            file_path = os.path.join(root, filename)
            try:
                if os.path.getsize(file_path) > MAX_FILE_SIZE_KB * BYTES_PER_KB:  # Reduced to 512KB limit for better performance
                    _log(f"Skipping large file: {os.path.basename(file_path)} ({os.path.getsize(file_path) // BYTES_PER_KB}KB)")
                    continue
            except OSError:
                continue
            
            # Check if file extension matches any supported language
            for lang, config in SUPPORTED_LANGUAGES.items():
                if file_ext in config['extensions']:
                    language_files[lang].append(file_path)
                    break
    
    # Log summary
    total_files = sum(len(files) for files in language_files.values())
    _log(f"Found {total_files} code files across {len([lang for lang, files in language_files.items() if files])} languages:")
    for lang, files in language_files.items():
        if files:
            _log(f"  {SUPPORTED_LANGUAGES[lang]['language_name']}: {len(files)} files")
    
    return language_files

def run_linter(filepath: str, language: str) -> tuple[list[str], bool]:
    """
    Run the appropriate linter for the given file and language.
    Returns a tuple: (issues, linter_available)
    Thread-safe implementation to prevent memory corruption.
    """
    if language not in SUPPORTED_LANGUAGES:
        return [], False
    
    config = SUPPORTED_LANGUAGES[language]
    linter = config['linter']
    args = config['linter_args']
    
    # Use thread lock to prevent concurrent subprocess calls
    with linter_lock:
        try:
            # Special handling for different linters
            if linter == 'flake8':
                result = subprocess.run(['flake8', filepath], capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'eslint':
                result = subprocess.run(['eslint', filepath] + args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'cppcheck':
                result = subprocess.run(['cppcheck', filepath] + args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'dotnet':
                result = subprocess.run(['dotnet', 'format', filepath, '--verify-no-changes'], capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'golangci-lint':
                result = subprocess.run(['golangci-lint', 'run', filepath] + args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'cargo':
                result = subprocess.run(['cargo', 'clippy', '--message-format=short'], capture_output=True, text=True, check=False, cwd=os.path.dirname(filepath), timeout=30)
            elif linter == 'phpcs':
                result = subprocess.run(['phpcs', filepath] + args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'rubocop':
                result = subprocess.run(['rubocop', filepath] + args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'swiftlint':
                result = subprocess.run(['swiftlint', 'lint', filepath] + args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'ktlint':
                result = subprocess.run(['ktlint', filepath] + args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'scalafmt':
                result = subprocess.run(['scalafmt', '--test', filepath] + args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'dart':
                result = subprocess.run(['dart', 'analyze', filepath] + args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'shellcheck':
                result = subprocess.run(['shellcheck', filepath] + args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'sqlfluff':
                result = subprocess.run(['sqlfluff', 'lint', filepath] + args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'htmlhint':
                result = subprocess.run(['htmlhint', filepath] + args, capture_output=True, text=True, check=False, timeout=30)
            else:
                return [], False
            
            # Linter ran successfully
            if result.stdout:
                return result.stdout.strip().split('\n'), True
            elif result.stderr:
                return result.stderr.strip().split('\n'), True
            else:
                return [], True
                
        except FileNotFoundError:
            return [], False
        except subprocess.TimeoutExpired:
            return [f"Linter {linter} timed out for {filepath}"], False
        except Exception as e:
            return [f"An error occurred while running {linter}: {e}"], False

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
    model_ref: Any,
    tokenizer_ref: Any = None,
    log_message_callback: Optional[Callable[[str], None]] = None
) -> str:
    """
    Enhance code by getting AI suggestions for the detected issue.
    """
    try:
        parsed_issue = parse_linter_output(issue_line, language)
        if not parsed_issue: 
            return f"Could not parse issue: {issue_line[:MAX_ERROR_MESSAGE_LENGTH]}"  # Limit error message
        
        line_num, issue_msg = parsed_issue
        original_code_line = get_code_context(filepath, line_num, context_lines=0).strip()
        if not original_code_line: 
            return "Could not read code context from file."

        if model_mode == "ollama":
            code_context = get_code_context(filepath, line_num, context_lines=2)  # Further reduced context
            language_name = SUPPORTED_LANGUAGES[language]['language_name']
            prompt = (
                f"Fix this {language_name} issue: {issue_msg[:MAX_ERROR_MESSAGE_LENGTH]}\n"
                f"Code: {code_context[:MAX_CODE_CONTEXT_LENGTH]}\n"
                f"Provide only the corrected line."
            )
            
            # Add timeout to prevent hanging
            import signal
            def timeout_handler(signum, frame):
                raise TimeoutError("AI suggestion generation timed out")
            
            # Set timeout for AI call (15 seconds - reduced from 30)
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(15)
            
            try:
                suggestion = ollama_client.get_ollama_response(prompt, model_ref)
                signal.alarm(0)  # Cancel timeout
                
                # Clean and limit suggestion
                clean_suggestion = suggestion.strip()
                if len(clean_suggestion) > MAX_SUGGESTION_LENGTH:
                    clean_suggestion = clean_suggestion[:MAX_SUGGESTION_LENGTH] + "..."
                
                return clean_suggestion[:MAX_CODE_SNIPPET_LENGTH]  # Limit suggestion size
                
            except TimeoutError:
                signal.alarm(0)  # Cancel timeout
                return "AI suggestion generation timed out"
            except Exception as e:
                signal.alarm(0)  # Cancel timeout
                log_message_callback(f"Error enhancing code: {str(e)[:MAX_ERROR_MESSAGE_LENGTH]}")
                return "Error generating AI suggestion"
        
        elif model_mode == "own_model":
            prompt = f"[BAD_CODE] {original_code_line[:MAX_PROMPT_LENGTH]} [GOOD_CODE]"
            try:
                clean_suggestion = ai_tools.generate_with_own_model(
                    model=model_ref,
                    tokenizer=tokenizer_ref,
                    prompt=prompt
                )
                return clean_suggestion[:MAX_CODE_SNIPPET_LENGTH]  # Limit suggestion size
            except Exception as e:
                return f"Model error: {str(e)[:50]}"
        else:
            return f"Unknown model mode: {model_mode}"

    except Exception as e:
        if log_message_callback: 
            log_message_callback(f"Error enhancing code: {str(e)[:MAX_ERROR_MESSAGE_LENGTH]}")
        return f"Error: {str(e)[:50]}"

def process_file_parallel(filepath: str, language: str, model_mode: str, model_ref: Any, tokenizer_ref: Any, analyzer: IntelligentCodeAnalyzer, log_message_callback: Optional[Callable[[str], None]] = None) -> Tuple[List[dict], bool]:
    """
    Process a single file with linter and intelligent analysis in a thread-safe manner.
    Optimized with lazy loading and memory management.
    Returns (issues_list, linter_available)
    """
    _log = log_message_callback if callable(log_message_callback) else print
    
    try:
        # Check file size before processing
        try:
            file_size = os.path.getsize(filepath)
            if file_size > MAX_FILE_SIZE_KB * BYTES_PER_KB:  # Reduced to 512KB limit for better performance
                _log(f"Skipping large file: {os.path.basename(filepath)} ({file_size // BYTES_PER_KB}KB)")
                return [], False
        except OSError:
            return [], False
        
        # Get linter issues if available (lazy loading) - with fallback mode
        linter_issues = []
        linter_available = False
        
        # Disable linters by default to prevent subprocess crashes
        # Linters can be re-enabled later if needed
        if hasattr(process_file_parallel, '_linters_disabled'):
            _log(f"Skipping linter for {filepath} (linters disabled)")
        else:
            # Disable linters to prevent crashes - focus on intelligent analysis
            process_file_parallel._linters_disabled = True
            _log("Disabling linters to prevent subprocess crashes - using intelligent analysis only")
        
        # Perform intelligent analysis with lazy file loading
        try:
            intelligent_issues = analyzer.analyze_file(filepath, language, linter_issues)
        except Exception as e:
            _log(f"Analysis error for {filepath}: {e}")
            intelligent_issues = []
        
        # Convert intelligent issues to the expected format (limit to prevent memory issues)
        file_issues = []
        max_issues_per_file = 10  # Further reduced limit to prevent memory issues
        
        for i, issue in enumerate(intelligent_issues):
            if i >= max_issues_per_file:
                _log(f"Limiting issues for {filepath} to {max_issues_per_file} to prevent memory issues")
                break
                
            try:
                # Get AI suggestion for the issue (lazy loading)
                suggestion = enhance_code(
                    filepath, 
                    issue.description, 
                    language,
                    model_mode, 
                    model_ref,
                    tokenizer_ref,
                    log_message_callback=_log
                )
                
                file_issues.append({
                    'file_path': issue.file_path,
                    'line_number': issue.line_number - 1,  # Convert to 0-based
                    'description': issue.description[:MAX_DESCRIPTION_LENGTH],  # Further limit description size
                    'code_snippet': issue.code_snippet[:MAX_CODE_SNIPPET_LENGTH],  # Further limit snippet size
                    'suggested_improvement': suggestion[:MAX_CODE_SNIPPET_LENGTH],  # Further limit suggestion size
                    'language': language,
                    'issue_type': issue.issue_type.value,
                    'severity': issue.severity,
                    'context': issue.context or {}
                })
            except Exception as e:
                # Skip individual issues that cause errors
                continue
        
        return file_issues, linter_available
        
    except Exception as e:
        _log(f"Error analyzing {filepath}: {e}")
        return [], False

def scan_code(
    directory: str, 
    model_mode: str, 
    model_ref: Any,
    tokenizer_ref: Any,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    log_message_callback: Optional[Callable[[str], None]] = None,
    cancellation_callback: Optional[Callable[[], bool]] = None
) -> List[dict]:
    """
    Comprehensive code scan using intelligent analysis and linter integration with multi-threading.
    Optimized for memory efficiency and proper cancellation handling.
    """
    _log = log_message_callback if callable(log_message_callback) else print
    
    _log(f"Starting intelligent multi-language code scan in '{directory}' using '{model_mode}' model.")
    
    # Initialize intelligent analyzer
    analyzer = IntelligentCodeAnalyzer()
    
    language_files = _get_all_code_files(directory, log_message_callback=_log)
    
    all_issues = []
    total_files = sum(len(files) for files in language_files.values())
    processed_files = 0
    missing_linters = set()
    
    # Thread-safe progress tracking
    progress_lock = threading.Lock()
    
    def update_progress(filepath: str):
        nonlocal processed_files
        with progress_lock:
            processed_files += 1
            if progress_callback:
                progress_callback(processed_files, total_files, f"Analyzing {os.path.relpath(filepath, directory)}")
    
    # Check for cancellation before starting
    if cancellation_callback and cancellation_callback():
        _log("Scan cancelled before starting")
        return []
    
    # Determine optimal number of workers based on CPU cores and file count
    import multiprocessing
    cpu_count = multiprocessing.cpu_count()
    
    # Very conservative threading strategy to prevent memory issues
    # Use single thread for maximum stability
    max_workers = 1  # Single thread for maximum stability
    
    _log(f"Using {max_workers} worker thread for maximum stability (CPU cores: {cpu_count}, files: {total_files})")
    
    # Disable linters to prevent subprocess crashes
    _log("Disabling linters to prevent subprocess crashes - using intelligent analysis only")
    process_file_parallel._linters_disabled = True
    
    # Process files in batches to prevent memory overload
    batch_size = max(1, total_files // 4)  # Smaller batches for single thread
    all_file_paths = []
    for language, files in language_files.items():
        if files:
            all_file_paths.extend([(filepath, language) for filepath in files])
    
    # Process files in batches
    for batch_start in range(0, len(all_file_paths), batch_size):
        batch_end = min(batch_start + batch_size, len(all_file_paths))
        batch_files = all_file_paths[batch_start:batch_end]
        
        # Check for cancellation before processing batch
        if cancellation_callback and cancellation_callback():
            _log("Scan cancelled during batch processing")
            return all_issues
        
        _log(f"Processing batch {batch_start//batch_size + 1}/{(len(all_file_paths) + batch_size - 1)//batch_size} ({len(batch_files)} files)")
        
        # Process batch with ThreadPoolExecutor (single thread)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit batch file processing tasks
            future_to_file = {}
            
            for filepath, language in batch_files:
                future = executor.submit(
                    process_file_parallel,
                    filepath,
                    language,
                    model_mode,
                    model_ref,
                    tokenizer_ref,
                    analyzer,
                    log_message_callback
                )
                future_to_file[future] = (filepath, language)
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                # Check for cancellation during processing
                if cancellation_callback and cancellation_callback():
                    _log("Scan cancelled during processing")
                    # Cancel remaining futures
                    for remaining_future in future_to_file:
                        if not remaining_future.done():
                            remaining_future.cancel()
                    return all_issues
                
                filepath, language = future_to_file[future]
                try:
                    file_issues, linter_available = future.result()
                    all_issues.extend(file_issues)
                    
                    if not linter_available:
                        linter_name = SUPPORTED_LANGUAGES[language]['linter']
                        missing_linters.add(f"{SUPPORTED_LANGUAGES[language]['language_name']} ({linter_name})")
                    
                    update_progress(filepath)
                    
                except Exception as e:
                    _log(f"Error processing {filepath}: {e}")
                    update_progress(filepath)
        
        # Force garbage collection after each batch to prevent memory buildup
        import gc
        gc.collect()
        
        # Small delay between batches to prevent system overload
        time.sleep(0.3)  # Increased delay for single thread

    if progress_callback: 
        progress_callback(total_files, total_files, "Analysis complete.")
    
    # Generate comprehensive summary
    try:
        _log("Starting summary generation...")
        # Convert issues back to CodeIssue objects for summary
        code_issues = []
        for i, issue in enumerate(all_issues):
            try:
                # Fix the IssueType conversion - use the string value directly
                issue_type_str = issue['issue_type']
                _log(f"Processing issue {i+1}/{len(all_issues)}: {issue_type_str}")
                
                # Map string values to IssueType enum
                issue_type_mapping = {
                    'performance_issue': IssueType.PERFORMANCE_ISSUE,
                    'security_vulnerability': IssueType.SECURITY_VULNERABILITY,
                    'code_smell': IssueType.CODE_SMELL,
                    'maintainability_issue': IssueType.MAINTAINABILITY_ISSUE,
                    'documentation_issue': IssueType.DOCUMENTATION_ISSUE,
                    'best_practice_violation': IssueType.BEST_PRACTICE_VIOLATION,
                    'linter_error': IssueType.LINTER_ERROR,
                    'architectural_issue': IssueType.ARCHITECTURAL_ISSUE,
                    'dependency_issue': IssueType.DEPENDENCY_ISSUE,
                    'semantic_issue': IssueType.SEMANTIC_ISSUE,
                    'data_flow_issue': IssueType.DATA_FLOW_ISSUE,
                    'code_quality': IssueType.CODE_QUALITY,
                    'logic_error': IssueType.LOGIC_ERROR
                }
                
                issue_type = issue_type_mapping.get(issue_type_str, IssueType.CODE_QUALITY)
                
                code_issues.append(CodeIssue(
                    file_path=issue['file_path'],
                    line_number=issue['line_number'] + 1,  # Convert back to 1-based
                    issue_type=issue_type,
                    severity=issue['severity'],
                    description=issue['description'],
                    code_snippet=issue['code_snippet'],
                    suggestion=issue['suggested_improvement'],
                    context=issue['context']
                ))
            except Exception as e:
                _log(f"Error converting issue {i+1}: {e}")
                continue
        
        _log(f"Successfully converted {len(code_issues)} issues for summary")
        
        summary = analyzer.generate_summary(code_issues)
        _log(f"\n=== INTELLIGENT ANALYSIS SUMMARY ===")
        _log(f"Total issues found: {summary['total_issues']}")
        _log(f"Issues by type: {summary['by_type']}")
        _log(f"Issues by severity: {summary['by_severity']}")
        
        if summary['critical_issues']:
            _log(f"Critical issues: {len(summary['critical_issues'])}")
            for issue in summary['critical_issues'][:3]:  # Show first 3
                _log(f"  - {issue['file']}:{issue['line']} - {issue['description']}")
        
        if summary['recommendations']:
            _log(f"Recommendations:")
            for rec in summary['recommendations']:
                _log(f"  - {rec}")
        
    except Exception as e:
        _log(f"Error generating summary: {e}")
        import traceback
        _log(f"Traceback: {traceback.format_exc()}")
    
    # Report missing linters
    if missing_linters:
        _log(f"\nMissing linters: {', '.join(missing_linters)}")
        _log("Install missing linters for better analysis results.")
    
    return all_issues