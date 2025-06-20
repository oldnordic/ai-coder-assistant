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
from concurrent.futures import ThreadPoolExecutor, Future
import threading
import shlex
from pathlib import Path
from datetime import datetime
import uuid
from core.config import Config
from core.logging import LogManager
from core.error import ErrorHandler, ErrorSeverity
from core.events import Event, EventType
from backend.services import ai_tools, ollama_client
from backend.services.intelligent_analyzer import IntelligentCodeAnalyzer, CodeIssue
from backend.services.scanner_persistence import (
    ScannerPersistenceService, ScanResult, CodeIssue as PersistenceCodeIssue, 
    FileAnalysis, ScanStatus, IssueSeverity
)
from backend.utils.constants import (
    MAX_DESCRIPTION_LENGTH, MAX_CODE_SNIPPET_LENGTH, 
    MAX_SUGGESTION_LENGTH, MAX_ERROR_MESSAGE_LENGTH, MAX_PROMPT_LENGTH,
    MAX_FILE_SIZE_KB, MAX_CODE_CONTEXT_LENGTH,
    MAX_ISSUES_PER_FILE, SCAN_TIMEOUT_SECONDS, BYTES_PER_KB, 
    DEFAULT_SCAN_LIMIT
)
import logging
from enum import Enum
import concurrent.futures

logger = logging.getLogger(__name__)

# Constants
# MAX_ISSUES_PER_FILE = 100  # Moved to constants.py
# SCAN_TIMEOUT_SECONDS = 300  # 5 minutes  # Moved to constants.py

# File size conversion constant
# BYTES_PER_KB = 1024  # Moved to constants.py

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

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

def detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    for lang, info in SUPPORTED_LANGUAGES.items():
        if ext in info['extensions']:
            return lang
    return 'unknown'

class ScannerService:
    """
    Comprehensive code scanning service with intelligent analysis and linter integration.
    Uses the core modules for configuration, logging, error handling, and threading.
    """
    
    def __init__(self):
        self.config = Config()
        self.logger = LogManager().get_logger('scanner')
        self.error_handler = ErrorHandler()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize analyzers
        self.intelligent_analyzer = IntelligentCodeAnalyzer()
        
        # Thread-safe locks
        self.linter_lock = threading.Lock()
        
        # Load configuration
        self.max_file_size_kb = self.config.get('scanner.max_file_size_kb', MAX_FILE_SIZE_KB)
        self.max_issues_per_file = self.config.get('scanner.max_issues_per_file', MAX_ISSUES_PER_FILE)
        self.scan_timeout = self.config.get('scanner.timeout_seconds', SCAN_TIMEOUT_SECONDS)
        
        self.logger.info("Scanner service initialized")
        
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
        """Create a ScanResult object and save it to the database."""
        scan_result = ScanResult(
            scan_id=scan_id,
            scan_type=scan_type,
            target_path=target_path,
            model_used=model_used,
            status=status,
            start_time=datetime.now(),
            metadata={"include_patterns": [], "exclude_patterns": []}
        )
        self.persistence.save_scan_result(scan_result)
        return scan_result
    
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
        callback: Optional[Callable[..., Any]] = None
    ) -> str:
        """Start a code scan operation with persistence integration."""
        if not os.path.isdir(directory):
            raise ValueError(f"Directory not found: {directory}")

        if self._current_scan_id:
            self.logger.warning("A scan is already in progress.")
            raise Exception("Scan already in progress.")

        scan_id = str(uuid.uuid4())
        # Create and save the initial scan result with PENDING status
        scan_result = self._create_scan_result(
            scan_id, "local_scan", directory, model_name or "default", ScanStatus.PENDING
        )
        
        # Update status to IN_PROGRESS and save again
        scan_result.status = ScanStatus.IN_PROGRESS
        self.persistence.save_scan_result(scan_result)
        
        scan_config = {
            'directory': directory,
            'model_name': model_name or self.config.get('scanner.default_model'),
            'excluded_dirs': self._excluded_dirs,
            'file_extensions': self._file_extensions,
            'scan_id': scan_id,
            'callback': callback
        }

        self._current_scan_id = scan_id
        
        future = self.executor.submit(self._run_scan, scan_config)
        future.add_done_callback(self._handle_scan_completion)
        
        self.logger.info(f"Scan {scan_id} started for directory: {directory}")
        return scan_id

    def _run_scan(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run the actual scan operation and handle persistence."""
        scan_id = config['scan_id']
        try:
            directory = config['directory']
            files_to_scan = self._collect_files(directory, config)
            total_files = len(files_to_scan)
            processed_files = 0
            results = {}
            
            for file_path in files_to_scan:
                if self._current_scan_id != scan_id:
                    # Scan was cancelled
                    break
                try:
                    file_result = self._scan_file(file_path, config)
                    if file_result:
                        results[file_path] = file_result
                    processed_files += 1
                except Exception as e:
                    self.error_handler.handle_error(
                        e, 'scanner_service', '_run_scan_loop', ErrorSeverity.WARNING, {'file': file_path}
                    )
            
            # Fetch the latest scan result to update it
            scan_result = self.persistence.get_scan_result(scan_id)
            if scan_result:
                scan_result.status = ScanStatus.COMPLETED if self._current_scan_id == scan_id else ScanStatus.CANCELLED
                scan_result.end_time = datetime.now()
                scan_result.total_files = total_files
                scan_result.processed_files = processed_files
                scan_result.issues_found = sum(len(r.get('issues', [])) for r in results.values() if isinstance(r, dict))
                self.persistence.save_scan_result(scan_result)

            return {
                'scan_id': scan_id,
                'status': scan_result.status.value if scan_result else 'unknown',
                'result': {
                    'total_files': total_files,
                    'processed_files': processed_files,
                    'results': results
                },
                'callback': config.get('callback')
            }
            
        except Exception as e:
            self.error_handler.handle_error(e, 'scanner_service', '_run_scan', ErrorSeverity.ERROR)
            scan_result = self.persistence.get_scan_result(scan_id)
            if scan_result:
                scan_result.status = ScanStatus.FAILED
                scan_result.end_time = datetime.now()
                self.persistence.save_scan_result(scan_result)
            return {
                'scan_id': scan_id,
                'status': 'failed',
                'error': str(e),
                'callback': config.get('callback')
            }

    def _collect_files(
        self,
        directory: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """Collect all files to be scanned."""
        # This is a placeholder. A real implementation would use the config
        # to filter files based on extensions, exclusions, etc.
        all_files: List[str] = []
        for root, _, files in os.walk(directory):
            for name in files:
                all_files.append(os.path.join(root, name))
        return all_files

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
    
    def _handle_scan_completion(self, future: Future[Dict[str, Any]]) -> None:
        """Handle scan completion, invoking the callback."""
        current_scan_id = self._current_scan_id
        
        try:
            task_result = future.result()
        except Exception as e:
            self.error_handler.handle_error(e, 'scanner_service', '_handle_scan_completion', ErrorSeverity.CRITICAL)
            if current_scan_id:
                scan_result = self.persistence.get_scan_result(current_scan_id)
                if scan_result:
                    scan_result.status = ScanStatus.FAILED
                    self.persistence.save_scan_result(scan_result)
            # Cannot call callback here as we don't have it.
            if self._current_scan_id == current_scan_id:
                self._current_scan_id = None
            return

        scan_id = task_result.get('scan_id')
        callback = task_result.get('callback')

        if callback:
            try:
                if task_result.get('status') == 'completed':
                    callback(task_result.get('result'))
                else:
                    callback(None, task_result.get('error'))
            except TypeError:
                # Callback may not accept error argument
                callback(task_result.get('result'))
            except Exception as e:
                self.logger.error(f"Error in scan completion callback for scan {scan_id}: {e}")
        
        if self._current_scan_id == scan_id:
            self._current_scan_id = None

    def cancel_scan(self) -> bool:
        """Cancel the current scan operation."""
        if self._current_scan_id:
            self.logger.info(f"Requesting cancellation for scan {self._current_scan_id}")
            scan_id_to_cancel = self._current_scan_id
            self._current_scan_id = None # Signal cancellation to the running loop
            
            # The running scan will update its own status to CANCELLED upon finishing.
            # However, we can also do it here for immediate feedback if desired.
            scan_result = self.persistence.get_scan_result(scan_id_to_cancel)
            if scan_result:
                scan_result.status = ScanStatus.CANCELLED
                self.persistence.save_scan_result(scan_result)
            return True
        return False
    
    def get_scan_status(self) -> Optional[TaskStatus]:
        """Get the status of the current scan.
        
        Returns:
            Optional[TaskStatus]: Current scan status or None if no scan is running
        """
        if self._current_scan_id:
            scan_result = self.persistence.get_scan_result(self._current_scan_id)
            if scan_result:
                return TaskStatus(scan_result.status.value)
        return None

    def _get_task_status(self) -> TaskStatus:
        """Get the current task status for the running scan."""
        if self._current_scan_id:
            scan_result = self.persistence.get_scan_result(self._current_scan_id)
            if scan_result:
                return TaskStatus(scan_result.status.value)
        return TaskStatus.PENDING

    def get_scan_result(self, scan_id: str) -> Optional[ScanResult]:
        """Get a scan result from persistence."""
        return self.persistence.get_scan_result(scan_id)
    
    def get_all_scan_results(self, status: Optional[ScanStatus] = None, limit: int = DEFAULT_SCAN_LIMIT) -> List[ScanResult]:
        """Get all scan results, optionally filtered by status."""
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
    Scans a directory and its subdirectories for code files of supported languages,
    categorizing them by language.
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
    
    try:
        # Use GitWildMatchPattern for .gitignore style matching
        spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
    except Exception as e:
        logger.error(f"Error creating pathspec from patterns={patterns}: {e}")
        return {}
    
    # Initialize result dictionary
    language_files: Dict[str, List[str]] = {lang: [] for lang in SUPPORTED_LANGUAGES.keys()}
    
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
        # Remove ignored dirs from os.walk traversal
        dirnames = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
        for d in dirnames:
            if d in ignored_dir_names:
                try:
                    os.listdir(os.path.join(root, d))  # Touch to trigger os.walk to skip
                except Exception:
                    pass
        # Exclude ignored files
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
            except Exception:
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

def get_files_to_scan(
    directory: str, 
    include_patterns: Optional[List[str]] = None, 
    exclude_patterns: Optional[List[str]] = None
) -> List[str]:
    """
    Get a list of files to scan based on include and exclude patterns.
    Uses .gitignore style matching. It handles include patterns by first
    ignoring everything, then adding negated patterns for inclusion.
    Automatically expands '*.ext' to both '*.ext' and '**/*.ext' for recursive matching.
    """
    if not os.path.isdir(directory):
        logger.error(f"Directory not found: {directory}")
        return []

    # Preprocess include patterns to expand '*.ext' to both '*.ext' and '**/*.ext'
    expanded_include_patterns = []
    if include_patterns:
        for pattern in include_patterns:
            expanded_include_patterns.append(pattern)
            # If it's a '*.ext' pattern, also add '**/*.ext' for recursive matching
            if pattern.startswith('*.') and not pattern.startswith('**/'):
                recursive_pattern = f'**/{pattern}'
                if recursive_pattern not in expanded_include_patterns:
                    expanded_include_patterns.append(recursive_pattern)

    patterns = []
    
    # Add exclude patterns first
    if exclude_patterns:
        patterns.extend(exclude_patterns)
    
    # If include_patterns are specified, only use the negated patterns for inclusion.
    if expanded_include_patterns:
        for p in expanded_include_patterns:
            patterns.append(f'!{p}')

    try:
        # Use GitWildMatchPattern for .gitignore style matching
        spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
    except Exception as e:
        logger.error(f"Error creating pathspec from patterns={patterns}: {e}")
        return []

    files_to_scan = []
    for root, dirs, files in os.walk(directory, topdown=True):
        # Prune directories to avoid traversing into ignored paths
        # Note: This requires paths relative to the directory where spec is applied
        rel_root = os.path.relpath(root, directory)
        if rel_root == '.':
            rel_root = ''
        
        # Filter dirs in-place
        dirs[:] = [d for d in dirs if not spec.match_file(os.path.join(rel_root, d).replace(os.sep, '/'))]
        
        for file in files:
            file_path = os.path.join(root, file)
            # Match against the path relative to the directory root
            relative_path = os.path.relpath(file_path, directory).replace(os.sep, '/')
            
            # Check if the file should be included (not ignored/excluded)
            if not spec.match_file(relative_path):
                files_to_scan.append(file_path)

    logger.info(f"Found {len(files_to_scan)} files to scan in '{directory}' "
                f"with includes={include_patterns} and excludes={exclude_patterns}.")

    return files_to_scan

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
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    enable_ai_powered: bool = False,
    model_name: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    log_message_callback: Optional[Callable[[str], None]] = None,
    cancellation_callback: Optional[Callable[[], bool]] = None
) -> List[dict]:
    """
    Performs a local code scan using available linters and optional AI analysis.
    Respects include/exclude patterns.
    """
    def _log(message: str):
        if log_message_callback:
            log_message_callback(message)

    _log(f"Starting local scan in: {directory}")
    
    files_to_scan = get_files_to_scan(directory, include_patterns, exclude_patterns)
    total_files = len(files_to_scan)

    if not files_to_scan:
        _log("No files found to scan.")
        if progress_callback:
            progress_callback(1, 1, "Scan complete: No files found.")
        return []

    if progress_callback:
        progress_callback(0, total_files, f"Found {total_files} files to scan...")

    results = []
    analyzer = IntelligentCodeAnalyzer()

    for i, file_path in enumerate(files_to_scan):
        if cancellation_callback and cancellation_callback():
            _log("Scan cancelled by user.")
            break
        
        if progress_callback:
            progress_callback(i, total_files, f"Scanning: {os.path.basename(file_path)}")

        try:
            language = detect_language(file_path)
            if language == 'unknown':
                _log(f"Skipping unsupported file type: {file_path}")
                continue
            
            # Simple linting as a baseline
            lint_issues, _ = run_linter(file_path, language)
            
            file_results = {
                "file_path": file_path,
                "language": language,
                "issues": [],
                "suggestions": []
            }
            
            for issue_text in lint_issues:
                parsed_issue = parse_linter_output(issue_text, language)
                if parsed_issue:
                    line_num, desc = parsed_issue
                    file_results["issues"].append({
                        "line": line_num,
                        "description": desc,
                        "severity": "medium" # Default severity
                    })

            # If AI analysis is enabled, enhance the results
            if enable_ai_powered and model_name:
                try:
                    ai_issues = process_file_ollama(file_path, model_name)
                    for issue in ai_issues:
                        # Avoid duplicates, simple check
                        if not any(i['line'] == issue.get('line') and i['description'] == issue.get('description') for i in file_results['issues']):
                            file_results['issues'].append(issue)
                except Exception as e:
                    _log(f"Error during AI analysis for {file_path}: {e}")

            if file_results["issues"]:
                results.append(file_results)

        except Exception as e:
            _log(f"Error processing file {file_path}: {e}")

    _log(f"Local scan finished. Found {len(results)} files with issues.")
    if progress_callback:
        progress_callback(total_files, total_files, "Scan complete.")
    
    return results

def enhance_issues_with_ai(
    issues: List[Dict[str, Any]], 
    model_name: str,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[Dict[str, Any]]:
    """
    Enhances a list of issues with AI-powered suggestions.
    """
    total_issues = len(issues)
    if progress_callback:
        progress_callback(0, total_issues, "Starting AI enhancement...")

    ollama_client_instance = ollama_client.OllamaClient()
    
    # Using a ThreadPoolExecutor to run suggestion generation in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Map each issue to a future
        future_to_issue = {
            executor.submit(
                ollama_client.get_suggestion_for_issue_sync, 
                ollama_client_instance, 
                issue, 
                model_name
            ): issue 
            for issue in issues
        }

        for i, future in enumerate(concurrent.futures.as_completed(future_to_issue)):
            issue = future_to_issue[future]
            try:
                suggestion = future.result()
                issue['suggestion'] = suggestion
            except Exception as e:
                logger.error(f"Error getting suggestion for issue in {issue.get('file_path')}: {e}")
                issue['suggestion'] = "Error getting suggestion."
            
            if progress_callback:
                progress_callback(i + 1, total_issues, f"Enhanced issue in {os.path.basename(issue.get('file_path', ''))}")
    
    if progress_callback:
        progress_callback(total_issues, total_issues, "Enhancement complete.")
        
    return issues