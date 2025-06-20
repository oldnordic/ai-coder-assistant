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
from typing import List, Tuple, Optional, Dict, Callable, Any, Set
import pathspec
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import shlex
from pathlib import Path
from datetime import datetime
import uuid
from core.config import Config
from core.logging import LogManager
from core.error import ErrorHandler, ErrorSeverity
from core.events import EventBus, Event, EventType
from core.threading import ThreadManager, TaskStatus

# --- FIXED: Use absolute imports for modules within the same package ---
from backend.utils import settings
from backend.services import ai_tools, ollama_client
from backend.services.intelligent_analyzer import IntelligentCodeAnalyzer, CodeIssue, IssueType
from backend.services.scanner_persistence import (
    ScannerPersistenceService, ScanResult, CodeIssue as PersistenceCodeIssue, 
    FileAnalysis, ScanStatus, IssueSeverity
)
from backend.utils.constants import (
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

def detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    for lang, info in SUPPORTED_LANGUAGES.items():
        if ext in info['extensions']:
            return lang
    return 'unknown'

class ScannerService:
    """Code scanning and analysis service.
    
    Provides functionality for scanning and analyzing code using different models.
    Uses the core modules for configuration, logging, error handling, and threading.
    Integrates with persistence service for data storage.
    """
    
    def __init__(self):
        """Initialize the scanner service."""
        self.config = Config()
        self.logger = LogManager().get_logger('scanner_service')
        self.error_handler = ErrorHandler()
        self.event_bus = EventBus()
        self.thread_manager = ThreadManager()
        
        # Initialize persistence service
        self.persistence = ScannerPersistenceService()
        
        self._current_scan_id: Optional[str] = None
        self._excluded_dirs: Set[str] = set(
            self.config.get('scanner.excluded_dirs', [])
        )
        self._file_extensions: Set[str] = set(
            self.config.get('scanner.file_extensions', [])
        )
    
    def _convert_issue_severity(self, severity: str) -> IssueSeverity:
        """Convert internal issue severity to persistence severity."""
        severity_map = {
            'low': IssueSeverity.LOW,
            'medium': IssueSeverity.MEDIUM,
            'high': IssueSeverity.HIGH,
            'critical': IssueSeverity.CRITICAL
        }
        return severity_map.get(severity.lower(), IssueSeverity.MEDIUM)
    
    def _convert_scan_status(self, status: str) -> ScanStatus:
        """Convert internal scan status to persistence status."""
        status_map = {
            'pending': ScanStatus.PENDING,
            'in_progress': ScanStatus.IN_PROGRESS,
            'completed': ScanStatus.COMPLETED,
            'failed': ScanStatus.FAILED,
            'cancelled': ScanStatus.CANCELLED
        }
        return status_map.get(status.lower(), ScanStatus.PENDING)
    
    def _create_scan_result(self, scan_id: str, scan_type: str, target_path: str, 
                           model_used: str, status: ScanStatus = ScanStatus.PENDING) -> ScanResult:
        """Create a scan result record."""
        return ScanResult(
            scan_id=scan_id,
            scan_type=scan_type,
            target_path=target_path,
            model_used=model_used,
            status=status,
            start_time=datetime.now(),
            metadata={"scanner_version": "1.0.0"}
        )
    
    def _create_persistence_issue(self, issue: CodeIssue, scan_id: str, file_path: str) -> PersistenceCodeIssue:
        """Convert internal code issue to persistence code issue."""
        # Convert context dict to string if it exists
        context_str = None
        if issue.context:
            context_str = str(issue.context)
        
        return PersistenceCodeIssue(
            issue_id=str(uuid.uuid4()),
            scan_id=scan_id,
            file_path=file_path,
            line_number=issue.line_number,
            column_number=None,  # CodeIssue doesn't have column_number
            severity=self._convert_issue_severity(issue.severity),
            category=issue.issue_type.value,
            description=issue.description[:MAX_DESCRIPTION_LENGTH] if len(issue.description) > MAX_DESCRIPTION_LENGTH else issue.description,
            suggestion=issue.suggestion[:MAX_SUGGESTION_LENGTH] if issue.suggestion and len(issue.suggestion) > MAX_SUGGESTION_LENGTH else issue.suggestion,
            code_snippet=issue.code_snippet[:MAX_CODE_SNIPPET_LENGTH] if issue.code_snippet and len(issue.code_snippet) > MAX_CODE_SNIPPET_LENGTH else issue.code_snippet,
            context=context_str[:MAX_CODE_CONTEXT_LENGTH] if context_str and len(context_str) > MAX_CODE_CONTEXT_LENGTH else context_str
        )
    
    def _create_file_analysis(self, file_path: str, scan_id: str, language: str, 
                             file_size: int, lines_of_code: int, issues_count: int = 0,
                             complexity_score: Optional[float] = None) -> FileAnalysis:
        """Create a file analysis record."""
        return FileAnalysis(
            file_id=str(uuid.uuid4()),
            scan_id=scan_id,
            file_path=file_path,
            file_size=file_size,
            lines_of_code=lines_of_code,
            language=language,
            complexity_score=complexity_score,
            issues_count=issues_count,
            analysis_data={"language": language, "analyzed_at": datetime.now().isoformat()}
        )

    def start_scan(
        self,
        directory: str,
        model_name: Optional[str] = None,
        callback: Optional[callable] = None
    ) -> str:
        """Start a code scan operation with persistence integration.
        
        Args:
            directory: Directory to scan
            model_name: Name of the model to use (optional)
            callback: Callback function for scan completion (optional)
        
        Returns:
            str: Scan task ID
        """
        if not os.path.isdir(directory):
            raise ValueError(f"Invalid directory: {directory}")
        
        scan_id = f"scan_{directory.replace(os.path.sep, '_')}"
        
        # Create scan result in persistence
        scan_result = self._create_scan_result(
            scan_id=scan_id,
            scan_type="directory_scan",
            target_path=directory,
            model_used=model_name or self.config.get('scanner.default_model', 'default'),
            status=ScanStatus.IN_PROGRESS
        )
        self.persistence.save_scan_result(scan_result)
        
        # Create scan configuration
        scan_config = {
            'directory': directory,
            'model_name': model_name or self.config.get('scanner.default_model'),
            'excluded_dirs': self._excluded_dirs,
            'file_extensions': self._file_extensions,
            'scan_id': scan_id  # Add scan_id to config for persistence
        }
        
        # Submit scan task
        self.thread_manager.submit_task(
            scan_id,
            self._run_scan,
            args=(scan_config,),
            callback=self._handle_scan_completion if callback is None else callback
        )
        
        self._current_scan_id = scan_id
        self.event_bus.publish(Event(
            EventType.SCAN_STARTED,
            data={'scan_id': scan_id, 'config': scan_config}
        ))
        
        return scan_id
    
    def _run_scan(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run the actual scan operation.
        
        Args:
            config: Scan configuration
        
        Returns:
            Dict[str, Any]: Scan results
        """
        try:
            directory = config['directory']
            files_to_scan = self._collect_files(directory, config)
            total_files = len(files_to_scan)
            processed_files = 0
            results = {}
            
            for file_path in files_to_scan:
                try:
                    file_result = self._scan_file(file_path, config)
                    if file_result:
                        results[file_path] = file_result
                    
                    processed_files += 1
                    progress = (processed_files / total_files) * 100
                    
                    self.event_bus.publish(Event(
                        EventType.SCAN_PROGRESS,
                        data={
                            'scan_id': self._current_scan_id,
                            'progress': progress,
                            'current_file': file_path
                        }
                    ))
                    
                except Exception as e:
                    self.error_handler.handle_error(
                        e,
                        'scanner_service',
                        '_run_scan',
                        ErrorSeverity.WARNING,
                        {'file': file_path}
                    )
            
            return {
                'total_files': total_files,
                'processed_files': processed_files,
                'results': results
            }
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                'scanner_service',
                '_run_scan',
                ErrorSeverity.ERROR
            )
            raise
    
    def _collect_files(
        self,
        directory: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """Collect files to scan based on configuration.
        
        Args:
            directory: Root directory to scan
            config: Scan configuration
        
        Returns:
            List[str]: List of file paths to scan
        """
        files_to_scan = []
        
        for root, dirs, files in os.walk(directory):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in config['excluded_dirs']]
            
            for file in files:
                if any(file.endswith(ext) for ext in config['file_extensions']):
                    files_to_scan.append(os.path.join(root, file))
        
        return files_to_scan
    
    def _scan_file(
        self,
        file_path: str,
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Scan a single file.
        
        Args:
            file_path: Path to the file to scan
            config: Scan configuration
        
        Returns:
            Optional[Dict[str, Any]]: Scan results for the file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # TODO: Implement actual file scanning using the specified model
            # This is a placeholder that should be replaced with actual model integration
            return {
                'path': file_path,
                'size': len(content),
                'lines': len(content.splitlines()),
                'analysis': {}  # To be filled with model analysis
            }
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                'scanner_service',
                '_scan_file',
                ErrorSeverity.WARNING,
                {'file': file_path}
            )
            return None
    
    def _handle_scan_completion(self, task_result: Dict[str, Any]) -> None:
        """Handle scan completion.
        
        Args:
            task_result: Result from the scan task
        """
        if task_result['status'] == TaskStatus.COMPLETED:
            self.event_bus.publish(Event(
                EventType.SCAN_COMPLETED,
                data={
                    'scan_id': self._current_scan_id,
                    'results': task_result['result']
                }
            ))
        else:
            self.event_bus.publish(Event(
                EventType.SCAN_FAILED,
                data={
                    'scan_id': self._current_scan_id,
                    'error': task_result.get('error')
                }
            ))
        
        self._current_scan_id = None
    
    def cancel_scan(self) -> bool:
        """Cancel the current scan operation.
        
        Returns:
            bool: True if scan was cancelled, False otherwise
        """
        if self._current_scan_id:
            cancelled = self.thread_manager.cancel_task(self._current_scan_id)
            if cancelled:
                self.event_bus.publish(Event(
                    EventType.SCAN_FAILED,
                    data={
                        'scan_id': self._current_scan_id,
                        'error': 'Scan cancelled by user'
                    }
                ))
                self._current_scan_id = None
            return cancelled
        return False
    
    def get_scan_status(self) -> Optional[TaskStatus]:
        """Get the status of the current scan.
        
        Returns:
            Optional[TaskStatus]: Current scan status or None if no scan is running
        """
        if self._current_scan_id:
            return self.thread_manager.get_task_status(self._current_scan_id)
        return None

    def get_scan_result(self, scan_id: str) -> Optional[ScanResult]:
        """Get scan result from persistence."""
        return self.persistence.get_scan_result(scan_id)
    
    def get_all_scan_results(self, status: Optional[ScanStatus] = None, limit: int = 100) -> List[ScanResult]:
        """Get all scan results from persistence."""
        return self.persistence.get_all_scan_results(status, limit)
    
    def get_code_issues(self, scan_id: str, severity: Optional[IssueSeverity] = None) -> List[PersistenceCodeIssue]:
        """Get code issues for a scan from persistence."""
        return self.persistence.get_code_issues(scan_id, severity)
    
    def get_file_analysis(self, scan_id: str) -> List[FileAnalysis]:
        """Get file analysis for a scan from persistence."""
        return self.persistence.get_file_analysis(scan_id)
    
    def get_scanner_analytics(self) -> Dict[str, Any]:
        """Get scanner analytics from persistence."""
        return self.persistence.get_scanner_analytics()
    
    def delete_scan_result(self, scan_id: str) -> bool:
        """Delete scan result and all associated data."""
        return self.persistence.delete_scan_result(scan_id)

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
    Returns (output_lines, success).
    """
    # Sanitize filepath to prevent command injection
    filepath = os.path.abspath(filepath)  # Get absolute path
    if not os.path.exists(filepath):
        return [], False
    
    # Get linter configuration
    if language not in SUPPORTED_LANGUAGES:
        return [], False
    
    config = SUPPORTED_LANGUAGES[language]
    linter = config['linter']
    args = config['linter_args']
    
    # Sanitize arguments to prevent command injection
    sanitized_args = []
    for arg in args:
        if isinstance(arg, str):
            # Quote arguments that might contain special characters
            sanitized_args.append(shlex.quote(arg))
        else:
            sanitized_args.append(str(arg))
    
    # Use thread lock to prevent concurrent linter execution
    with linter_lock:
        try:
            # Special handling for different linters
            if linter == 'flake8':
                # flake8 is safe as it only takes the filepath
                result = subprocess.run(['flake8', filepath], capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'eslint':
                # Sanitize filepath for eslint
                result = subprocess.run(['eslint', filepath] + sanitized_args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'cppcheck':
                # Sanitize filepath for cppcheck
                result = subprocess.run(['cppcheck', filepath] + sanitized_args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'dotnet':
                # dotnet format is safe as it only takes the filepath
                result = subprocess.run(['dotnet', 'format', filepath, '--verify-no-changes'], capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'golangci-lint':
                # Sanitize filepath for golangci-lint
                result = subprocess.run(['golangci-lint', 'run', filepath] + sanitized_args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'cargo':
                # cargo clippy is safe as it only takes predefined arguments
                result = subprocess.run(['cargo', 'clippy', '--message-format=short'], capture_output=True, text=True, check=False, cwd=os.path.dirname(filepath), timeout=30)
            elif linter == 'phpcs':
                # Sanitize filepath for phpcs
                result = subprocess.run(['phpcs', filepath] + sanitized_args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'rubocop':
                # Sanitize filepath for rubocop
                result = subprocess.run(['rubocop', filepath] + sanitized_args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'swiftlint':
                # Sanitize filepath for swiftlint
                result = subprocess.run(['swiftlint', 'lint', filepath] + sanitized_args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'ktlint':
                # Sanitize filepath for ktlint
                result = subprocess.run(['ktlint', filepath] + sanitized_args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'scalafmt':
                # Sanitize filepath for scalafmt
                result = subprocess.run(['scalafmt', '--test', filepath] + sanitized_args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'dart':
                # Sanitize filepath for dart analyze
                result = subprocess.run(['dart', 'analyze', filepath] + sanitized_args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'shellcheck':
                # Sanitize filepath for shellcheck
                result = subprocess.run(['shellcheck', filepath] + sanitized_args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'sqlfluff':
                # Sanitize filepath for sqlfluff
                result = subprocess.run(['sqlfluff', 'lint', filepath] + sanitized_args, capture_output=True, text=True, check=False, timeout=30)
            elif linter == 'htmlhint':
                # Sanitize filepath for htmlhint
                result = subprocess.run(['htmlhint', filepath] + sanitized_args, capture_output=True, text=True, check=False, timeout=30)
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
            # Check if Ollama service is available before attempting to use it
            try:
                from backend.services.ollama_client import get_available_models_sync
                available_models = get_available_models_sync()
                if not available_models:
                    return "No Ollama models available. Please install and configure Ollama first."
                
                if not model_ref:
                    return "No Ollama model selected. Please select a model in the AI tab."
                    
            except Exception as e:
                if log_message_callback:
                    log_message_callback(f"Ollama service not available: {str(e)[:MAX_ERROR_MESSAGE_LENGTH]}")
                return "Ollama service not available. Please check your Ollama installation."
            
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
                if log_message_callback:
                    log_message_callback(f"Error enhancing code: {str(e)[:MAX_ERROR_MESSAGE_LENGTH]}")
                return "Error generating AI suggestion"
        
        elif model_mode == "own_model":
            # Check if own model is available
            if not model_ref or not tokenizer_ref:
                return "No trained model available. Please train a model first."
                
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
    tokenizer_ref: Any = None,  # Make tokenizer optional
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    log_message_callback: Optional[Callable[[str], None]] = None,
    cancellation_callback: Optional[Callable[[], bool]] = None
) -> List[dict]:
    """
    Comprehensive code scan using intelligent analysis and linter integration with multi-threading.
    Optimized for memory efficiency and proper cancellation handling.
    """
    _log = log_message_callback if callable(log_message_callback) else print
    
    # Validate model settings
    if model_mode == "ollama":
        if not model_ref:
            _log("Error: No Ollama model selected")
            return []
        try:
            # Verify Ollama model is available
            from backend.services.ollama_client import get_available_models_sync
            available_models = get_available_models_sync()
            if model_ref not in available_models:
                _log(f"Error: Selected Ollama model '{model_ref}' is not available")
                return []
        except Exception as e:
            _log(f"Error: Failed to verify Ollama model availability: {e}")
            return []
    elif model_mode == "own_model":
        if not model_ref or not tokenizer_ref:  # Only check tokenizer for own models
            _log("Error: Own model or tokenizer not loaded")
            return []
    else:
        _log(f"Error: Unsupported model mode: {model_mode}")
        return []
    
    _log(f"Starting intelligent multi-language code scan in '{directory}' using '{model_mode}' model.")
    
    try:
        # Initialize progress
        if progress_callback:
            progress_callback(0, 100, "Initializing scan...")
        
        # Get list of files to scan
        files = get_files_to_scan(directory)
        if not files:
            _log("No files found to scan")
            return []
        
        total_files = len(files)
        _log(f"Found {total_files} files to scan")

        if progress_callback:
            # Initialize with total number of files
            progress_callback(0, total_files, "Initializing scan...")
        
        # Process files
        results = []
        for i, file_path in enumerate(files, 1):
            # Check for cancellation
            if cancellation_callback and cancellation_callback():
                _log("Scan cancelled by user")
                return results
            
            # Update progress
            if progress_callback:
                progress_callback(i, total_files, f"Scanning file {i}/{total_files}: {os.path.basename(file_path)}")
            
            try:
                # Process file based on model mode
                if model_mode == "ollama":
                    file_results = process_file_ollama(file_path, model_ref)
                else:  # own_model
                    file_results = process_file_own_model(file_path, model_ref, tokenizer_ref)
                
                if file_results:
                    results.extend(file_results)
            except Exception as e:
                _log(f"Error processing file {file_path}: {e}")
                continue
        
        # Final progress update
        if progress_callback:
            progress_callback(total_files, total_files, "Scan complete")
        
        return results
    except Exception as e:
        _log(f"Error during scan: {e}")
        return []

def get_files_to_scan(directory: str) -> List[str]:
    """Get list of files to scan in the directory, respecting .ai_coder_ignore patterns."""
    import pathspec
    files = []
    ignore_file = os.path.join(directory, '.ai_coder_ignore')
    patterns = []
    if os.path.exists(ignore_file):
        with open(ignore_file, 'r', encoding='utf-8') as f:
            patterns = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
    for root, _, filenames in os.walk(directory):
        rel_root = os.path.relpath(root, directory)
        if rel_root == '.':
            rel_root = ''
        # Exclude ignored directories
        dirs_to_check = {os.path.join(rel_root, d).replace(os.sep, '/') for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))}
        ignored_dirs = set(spec.match_files(dirs_to_check))
        ignored_dir_names = {os.path.basename(str(p).strip('/')) for p in ignored_dirs}
        # Remove ignored dirs from os.walk traversal
        dirnames = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
        for d in dirnames:
            if d in ignored_dir_names:
                try:
                    os.listdir(os.path.join(root, d))  # Touch to trigger os.walk to skip
                except Exception:
                    pass
        # Exclude ignored files
        for filename in filenames:
            rel_file_path = os.path.join(rel_root, filename).replace(os.sep, '/')
            if spec.match_file(rel_file_path):
                continue
            if filename.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp')):
                files.append(os.path.join(root, filename))
    return files

def process_file_ollama(file_path: str, model_ref: str) -> List[Dict[str, Any]]:
    """Process a file using Ollama model."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Call Ollama API to analyze code
        from backend.services.ollama_client import analyze_code, OllamaClient
        
        # Create Ollama client instance
        client = OllamaClient()
        
        # Use asyncio to run the async function
        import asyncio
        results = asyncio.run(analyze_code(client, content, model_ref))
        
        # Convert results to standard format
        issues = []
        for result in results:
            issues.append({
                'file_path': file_path,
                'line_number': result.get('line_number', 0),
                'description': result.get('description', ''),
                'severity': result.get('severity', 'medium'),
                'suggested_improvement': result.get('suggestion', ''),
                'code_snippet': result.get('code_snippet', ''),
                'context': result.get('context', ''),
                'issue_type': result.get('issue_type', 'code_quality'),
                'language': 'unknown'  # Will be set by the caller
            })
        return issues
    except Exception as e:
        print(f"Error processing file {file_path} with Ollama: {e}")
        return []

def process_file_own_model(file_path: str, model_ref: Any, tokenizer_ref: Any) -> List[Dict[str, Any]]:
    """Process a file using own trained model."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use own model to analyze code
        # This is a placeholder - implement your own model analysis here
        issues = []
        # TODO: Implement own model analysis
        return issues
    except Exception as e:
        print(f"Error processing file {file_path} with own model: {e}")
        return []

def scan_code_local(
    directory: str, 
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    log_message_callback: Optional[Callable[[str], None]] = None,
    cancellation_callback: Optional[Callable[[], bool]] = None
) -> List[dict]:
    """
    Performs a fast, local-only code scan using pattern matching.
    Workflow:
      1. File discovery (with .ai_coder_ignore support)
      2. Language detection
      3. Linter/static analysis (TODO)
      4. AI analysis (TODO)
      5. Aggregation and reporting
    """
    _log = log_message_callback if callable(log_message_callback) else print
    _log(f"Starting local code scan in '{directory}'.")

    try:
        # 1. File discovery
        if progress_callback:
            progress_callback(0, 100, "Initializing local scan...")

        files = get_files_to_scan(directory)
        if not files:
            _log("No files found to scan")
            if progress_callback:
                progress_callback(100, 100, "No files found.")
            return []

        total_files = len(files)
        _log(f"Found {total_files} files to scan")
        
        analyzer = IntelligentCodeAnalyzer()
        all_issues = []
        
        for i, file_path in enumerate(files, 1):
            if cancellation_callback and cancellation_callback():
                _log("Scan cancelled by user")
                break
            
            if progress_callback:
                progress_callback(i, total_files, f"Scanning file {i}/{total_files}: {os.path.basename(file_path)}")

            # 2. Language detection
            language = detect_language(file_path)
            if language == 'unknown':
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 3. Linter/static analysis (TODO: integrate linter here)
                # linter_issues = run_linter(file_path, language)
                # all_issues.extend(linter_issues)

                # 4. AI analysis (current: intelligent analyzer)
                issues = analyzer._analyze_content_intelligently(content, file_path, language)
                
                for issue in issues:
                    all_issues.append({
                        'file_path': issue.file_path,
                        'line_number': issue.line_number,
                        'description': issue.description,
                        'code_snippet': issue.code_snippet,
                        'suggested_improvement': '',
                        'language': language,
                        'issue_type': issue.issue_type.value,
                        'severity': issue.severity,
                        'context': issue.context or {}
                    })

            except Exception as e:
                _log(f"Error processing file {file_path} locally: {e}")
                continue

        # 5. Aggregation and reporting
        if progress_callback:
            progress_callback(total_files, total_files, "Local scan complete")

        _log(f"Local scan found {len(all_issues)} potential issues.")
        return all_issues

    except Exception as e:
        _log(f"Error during local scan: {e}")
        return []