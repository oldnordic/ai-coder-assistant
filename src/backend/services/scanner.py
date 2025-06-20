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

import concurrent.futures
import logging

# src/core/scanner.py
import os
import re
import shlex
import subprocess
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import pathspec

from src.backend.services import ai_tools, ollama_client
from src.backend.services.intelligent_analyzer import CodeIssue, IntelligentCodeAnalyzer
from src.backend.services.scanner_persistence import CodeIssue as PersistenceCodeIssue
from src.backend.services.scanner_persistence import (
    FileAnalysis,
    IssueSeverity,
    ScannerPersistenceService,
    ScanResult,
    ScanStatus,
)
from src.backend.utils.constants import (
    AI_SUGGESTION_TIMEOUT_SECONDS,
    BYTES_PER_KB,
    DEFAULT_SCAN_LIMIT,
    LINTER_TIMEOUT_SECONDS,
    MAX_CODE_CONTEXT_LENGTH,
    MAX_CODE_SNIPPET_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_ERROR_MESSAGE_LENGTH,
    MAX_FILE_SIZE_KB,
    MAX_ISSUES_PER_FILE,
    MAX_PROMPT_LENGTH,
    MAX_SUGGESTION_LENGTH,
    SCAN_TIMEOUT_SECONDS,
)
from src.core.config import Config
from src.core.error import ErrorHandler, ErrorSeverity
from src.core.events import Event, EventType
from src.core.logging import LogManager

logger = logging.getLogger(__name__)

# Constants
# MAX_ISSUES_PER_FILE = 100  # Moved to constants.py
# SCAN_TIMEOUT_SECONDS = 300  # 5 minutes  # Moved to constants.py

# File size conversion constant
# BYTES_PER_KB = 1024  # Moved to constants.py

# Define the 20 most used programming languages with their file extensions and linters
SUPPORTED_LANGUAGES = {
    "python": {
        "extensions": [".py", ".pyw", ".pyx", ".pyi"],
        "linter": "flake8",
        "linter_args": [],
        "language_name": "Python",
    },
    "javascript": {
        "extensions": [".js", ".jsx", ".mjs"],
        "linter": "eslint",
        "linter_args": ["--format=compact"],
        "language_name": "JavaScript",
    },
    "typescript": {
        "extensions": [".ts", ".tsx"],
        "linter": "eslint",
        "linter_args": ["--format=compact"],
        "language_name": "TypeScript",
    },
    "java": {
        "extensions": [".java"],
        "linter": "checkstyle",
        "linter_args": ["-c", "google_checks.xml"],
        "language_name": "Java",
    },
    "c": {
        "extensions": [".c", ".h"],
        "linter": "cppcheck",
        "linter_args": ["--enable=all", "--xml"],
        "language_name": "C",
    },
    "cpp": {
        "extensions": [".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"],
        "linter": "cppcheck",
        "linter_args": ["--enable=all", "--xml"],
        "language_name": "C++",
    },
    "csharp": {
        "extensions": [".cs"],
        "linter": "dotnet",
        "linter_args": ["format", "--verify-no-changes"],
        "language_name": "C#",
    },
    "go": {
        "extensions": [".go"],
        "linter": "golangci-lint",
        "linter_args": ["run"],
        "language_name": "Go",
    },
    "rust": {
        "extensions": [".rs"],
        "linter": "cargo",
        "linter_args": ["clippy", "--message-format=short"],
        "language_name": "Rust",
    },
    "php": {
        "extensions": [".php"],
        "linter": "phpcs",
        "linter_args": ["--standard=PSR12"],
        "language_name": "PHP",
    },
    "ruby": {
        "extensions": [".rb"],
        "linter": "rubocop",
        "linter_args": ["--format=simple"],
        "language_name": "Ruby",
    },
    "swift": {
        "extensions": [".swift"],
        "linter": "swiftlint",
        "linter_args": ["lint"],
        "language_name": "Swift",
    },
    "kotlin": {
        "extensions": [".kt", ".kts"],
        "linter": "ktlint",
        "linter_args": ["--format=plain"],
        "language_name": "Kotlin",
    },
    "scala": {
        "extensions": [".scala"],
        "linter": "scalafmt",
        "linter_args": ["--test"],
        "language_name": "Scala",
    },
    "dart": {
        "extensions": [".dart"],
        "linter": "dart",
        "linter_args": ["analyze"],
        "language_name": "Dart",
    },
    "r": {
        "extensions": [".r", ".R"],
        "linter": "lintr",
        "linter_args": [],
        "language_name": "R",
    },
    "matlab": {
        "extensions": [".m"],
        "linter": "mlint",
        "linter_args": [],
        "language_name": "MATLAB",
    },
    "shell": {
        "extensions": [".sh", ".bash", ".zsh", ".fish"],
        "linter": "shellcheck",
        "linter_args": ["--format=gcc"],
        "language_name": "Shell",
    },
    "sql": {
        "extensions": [".sql"],
        "linter": "sqlfluff",
        "linter_args": ["lint"],
        "language_name": "SQL",
    },
    "html": {
        "extensions": [".html", ".htm"],
        "linter": "htmlhint",
        "linter_args": [],
        "language_name": "HTML",
    },
}

# Add thread lock for linter execution at the top of the file
linter_lock = threading.Lock()

# Global cache for available linters
_available_linters_cache = None
_available_linters_cache_time = 0
_CACHE_DURATION = 300  # 5 minutes


def check_linter_available(linter_name: str) -> bool:
    """
    Check if a specific linter is available in the system.
    """
    try:
        # Use 'which' command to check if linter exists
        result = subprocess.run(
            ["which", linter_name], capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False


def get_available_linters() -> Dict[str, bool]:
    """
    Get a dictionary of all supported linters and their availability.
    Uses caching to avoid repeated checks.
    """
    global _available_linters_cache, _available_linters_cache_time

    current_time = datetime.now().timestamp()

    # Return cached result if still valid
    if (
        _available_linters_cache is not None
        and current_time - _available_linters_cache_time < _CACHE_DURATION
    ):
        return _available_linters_cache

    # Check all linters
    available_linters = {}
    unique_linters = set()

    # Collect unique linters from SUPPORTED_LANGUAGES
    for lang_config in SUPPORTED_LANGUAGES.values():
        unique_linters.add(lang_config["linter"])

    logger.info("Checking available linters...")

    for linter in unique_linters:
        is_available = check_linter_available(linter)
        available_linters[linter] = is_available
        if is_available:
            logger.info(f"✓ Linter available: {linter}")
        else:
            logger.info(f"✗ Linter not available: {linter}")

    # Cache the result
    _available_linters_cache = available_linters
    _available_linters_cache_time = current_time

    return available_linters


def get_supported_languages_with_available_linters() -> Dict[str, Dict[str, Any]]:
    """
    Get a filtered version of SUPPORTED_LANGUAGES that only includes
    languages with available linters.
    """
    available_linters = get_available_linters()
    filtered_languages = {}

    for lang, config in SUPPORTED_LANGUAGES.items():
        linter = config["linter"]
        if available_linters.get(linter, False):
            filtered_languages[lang] = config
        else:
            logger.debug(f"Skipping {lang} - linter {linter} not available")

    return filtered_languages


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
        if ext in info["extensions"]:
            return lang
    return "unknown"


class ScannerService:
    """
    Comprehensive code scanning service with intelligent analysis and linter integration.
    Uses the core modules for configuration, logging, error handling, and threading.
    """

    def __init__(self):
        self.config = Config()
        self.logger = LogManager().get_logger("scanner")
        self.error_handler = ErrorHandler()
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Initialize analyzers
        self.intelligent_analyzer = IntelligentCodeAnalyzer()

        # Thread-safe locks
        self.linter_lock = threading.Lock()

        # Load configuration
        self.max_file_size_kb = self.config.get(
            "scanner.max_file_size_kb", MAX_FILE_SIZE_KB
        )
        self.max_issues_per_file = self.config.get(
            "scanner.max_issues_per_file", MAX_ISSUES_PER_FILE
        )
        self.scan_timeout = self.config.get(
            "scanner.timeout_seconds", SCAN_TIMEOUT_SECONDS
        )

        self.logger.info("Scanner service initialized")

        # Initialize persistence service
        self.persistence = ScannerPersistenceService()

        self._current_scan_id: Optional[str] = None
        self._excluded_dirs: Set[str] = set(
            self.config.get("scanner.excluded_dirs", [])
        )
        self._file_extensions: Set[str] = set(
            self.config.get("scanner.file_extensions", [])
        )

        # Detect available linters during initialization
        self._available_linters = get_available_linters()
        self._supported_languages = get_supported_languages_with_available_linters()

        logger.info(
            f"Scanner service initialized with {len(self._supported_languages)} supported languages"
        )
        logger.info(
            f"Available linters: {[linter for linter, available in self._available_linters.items() if available]}"
        )

        # Initialize thread manager
        self.thread_manager = ThreadPoolExecutor(max_workers=4)

    def _convert_issue_severity(self, severity: str) -> IssueSeverity:
        """Convert internal issue severity to persistence severity."""
        severity_map = {
            "low": IssueSeverity.LOW,
            "medium": IssueSeverity.MEDIUM,
            "high": IssueSeverity.HIGH,
            "critical": IssueSeverity.CRITICAL,
        }
        return severity_map.get(severity.lower(), IssueSeverity.MEDIUM)

    def _convert_scan_status(self, status: str) -> ScanStatus:
        """Convert internal scan status to persistence status."""
        status_map = {
            "pending": ScanStatus.PENDING,
            "in_progress": ScanStatus.IN_PROGRESS,
            "completed": ScanStatus.COMPLETED,
            "failed": ScanStatus.FAILED,
            "cancelled": ScanStatus.CANCELLED,
        }
        return status_map.get(status.lower(), ScanStatus.PENDING)

    def _create_scan_result(
        self,
        scan_id: str,
        scan_type: str,
        target_path: str,
        model_used: str,
        status: ScanStatus = ScanStatus.PENDING,
    ) -> ScanResult:
        """Create a ScanResult object and save it to the database."""
        scan_result = ScanResult(
            scan_id=scan_id,
            scan_type=scan_type,
            target_path=target_path,
            model_used=model_used,
            status=status,
            start_time=datetime.now(),
            metadata={"include_patterns": [], "exclude_patterns": []},
        )
        self.persistence.save_scan_result(scan_result)
        return scan_result

    def _create_persistence_issue(
        self, issue: CodeIssue, scan_id: str, file_path: str
    ) -> PersistenceCodeIssue:
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
            description=(
                issue.description[:MAX_DESCRIPTION_LENGTH]
                if len(issue.description) > MAX_DESCRIPTION_LENGTH
                else issue.description
            ),
            suggestion=(
                issue.suggestion[:MAX_SUGGESTION_LENGTH]
                if issue.suggestion and len(issue.suggestion) > MAX_SUGGESTION_LENGTH
                else issue.suggestion
            ),
            code_snippet=(
                issue.code_snippet[:MAX_CODE_SNIPPET_LENGTH]
                if issue.code_snippet
                and len(issue.code_snippet) > MAX_CODE_SNIPPET_LENGTH
                else issue.code_snippet
            ),
            context=(
                context_str[:MAX_CODE_CONTEXT_LENGTH]
                if context_str and len(context_str) > MAX_CODE_CONTEXT_LENGTH
                else context_str
            ),
        )

    def _create_file_analysis(
        self,
        file_path: str,
        scan_id: str,
        language: str,
        file_size: int,
        lines_of_code: int,
        issues_count: int = 0,
        complexity_score: Optional[float] = None,
    ) -> FileAnalysis:
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
            analysis_data={
                "language": language,
                "analyzed_at": datetime.now().isoformat(),
            },
        )

    def start_scan(
        self,
        directory: str,
        model_name: Optional[str] = None,
        callback: Optional[Callable[..., Any]] = None,
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
            scan_id,
            "local_scan",
            directory,
            model_name or "default",
            ScanStatus.PENDING,
        )

        # Update status to IN_PROGRESS and save again
        scan_result.status = ScanStatus.IN_PROGRESS
        self.persistence.save_scan_result(scan_result)

        scan_config = {
            "directory": directory,
            "model_name": model_name or self.config.get("scanner.default_model"),
            "excluded_dirs": self._excluded_dirs,
            "file_extensions": self._file_extensions,
            "scan_id": scan_id,
            "callback": callback,
        }

        self._current_scan_id = scan_id

        future = self.executor.submit(self._run_scan, scan_config)
        future.add_done_callback(self._handle_scan_completion)

        self.logger.info(f"Scan {scan_id} started for directory: {directory}")
        return scan_id

    def _run_scan(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run the actual scan operation and handle persistence."""
        scan_id = config["scan_id"]
        try:
            directory = config["directory"]
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
                        e,
                        "scanner_service",
                        "_run_scan_loop",
                        ErrorSeverity.WARNING,
                        {"file": file_path},
                    )

            # Fetch the latest scan result to update it
            scan_result = self.persistence.get_scan_result(scan_id)
            if scan_result:
                scan_result.status = (
                    ScanStatus.COMPLETED
                    if self._current_scan_id == scan_id
                    else ScanStatus.CANCELLED
                )
                scan_result.end_time = datetime.now()
                scan_result.total_files = total_files
                scan_result.processed_files = processed_files
                scan_result.issues_found = sum(
                    len(r.get("issues", []))
                    for r in results.values()
                    if isinstance(r, dict)
                )
                self.persistence.save_scan_result(scan_result)

            return {
                "scan_id": scan_id,
                "status": scan_result.status.value if scan_result else "unknown",
                "result": {
                    "total_files": total_files,
                    "processed_files": processed_files,
                    "results": results,
                },
                "callback": config.get("callback"),
            }

        except Exception as e:
            self.error_handler.handle_error(
                e, "scanner_service", "_run_scan", ErrorSeverity.ERROR
            )
            scan_result = self.persistence.get_scan_result(scan_id)
            if scan_result:
                scan_result.status = ScanStatus.FAILED
                scan_result.end_time = datetime.now()
                self.persistence.save_scan_result(scan_result)
            return {
                "scan_id": scan_id,
                "status": "failed",
                "error": str(e),
                "callback": config.get("callback"),
            }

    def _collect_files(self, directory: str, config: Dict[str, Any]) -> List[str]:
        """Collect all files to be scanned, only for languages with available linters."""
        files_to_scan = []

        # Get file extensions for languages with available linters
        supported_extensions = set()
        for lang_config in self._supported_languages.values():
            supported_extensions.update(lang_config["extensions"])

        if not supported_extensions:
            self.logger.warning("No linters available - no files will be scanned")
            return files_to_scan

        # Walk through directory and collect files with supported extensions
        for root, dirs, files in os.walk(directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self._excluded_dirs]

            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()

                # Only include files with supported extensions
                if file_ext in supported_extensions:
                    files_to_scan.append(file_path)

        self.logger.info(
            f"Found {len(files_to_scan)} files to scan in '{directory}' with available linters"
        )
        return files_to_scan

    def _scan_file(
        self, file_path: str, config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Scan a single file using available linters.

        Args:
            file_path: Path to the file to scan
            config: Scan configuration

        Returns:
            Optional[Dict[str, Any]]: Scan results for the file
        """
        try:
            # Detect language from file extension
            language = detect_language(file_path)
            if language not in self._supported_languages:
                self.logger.debug(
                    f"Skipping {file_path} - language {language} not supported or linter not available"
                )
                return None

            # Get language configuration
            lang_config = self._supported_languages[language]
            linter = lang_config["linter"]

            # Check if linter is available
            if not self._available_linters.get(linter, False):
                self.logger.debug(
                    f"Skipping {file_path} - linter {linter} not available"
                )
                return None

            # Run the linter
            linter_output, success = self._run_linter(file_path, language)

            if not success:
                self.logger.warning(f"Linter {linter} failed for {file_path}")
                return None

            # Parse linter output
            issues = []
            for line in linter_output:
                parsed_issue = self._parse_linter_output(line, language)
                if parsed_issue:
                    line_num, description = parsed_issue
                    issues.append(
                        {
                            "line": line_num,
                            "description": description,
                            "severity": "medium",  # Default severity
                            "linter": linter,
                        }
                    )

            # Get file info
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            return {
                "path": file_path,
                "language": language,
                "size": len(content),
                "lines": len(content.splitlines()),
                "issues": issues,
                "linter_used": linter,
            }

        except Exception as e:
            self.error_handler.handle_error(
                e,
                "scanner_service",
                "_scan_file",
                ErrorSeverity.WARNING,
                {"file": file_path},
            )
            return None

    def _run_linter(self, filepath: str, language: str) -> tuple[list[str], bool]:
        """
        Run the appropriate linter for the given file and language.
        Returns (output_lines, success).
        """
        # Validate and sanitize inputs
        if not filepath or not language:
            return [], False

        # Sanitize filepath to prevent command injection
        try:
            filepath = os.path.abspath(filepath)  # Get absolute path
            if not os.path.exists(filepath):
                return [], False

            # Additional validation: ensure filepath is within allowed directories
            # This prevents directory traversal attacks
            real_filepath = os.path.realpath(filepath)
            if not real_filepath.startswith(os.path.realpath(os.getcwd())):
                self.logger.warning(
                    f"Attempted to access file outside current directory: {filepath}"
                )
                return [], False

        except (OSError, ValueError) as e:
            self.logger.error(f"Invalid filepath: {filepath}, error: {e}")
            return [], False

        # Get linter configuration
        if language not in self._supported_languages:
            self.logger.warning(f"Unsupported language: {language}")
            return [], False

        config = self._supported_languages[language]
        linter = config["linter"]
        args = config["linter_args"]

        # Validate linter command
        if not linter or not linter.strip():
            self.logger.error(f"Invalid linter command: {linter}")
            return [], False

        # Sanitize arguments to prevent command injection
        sanitized_args = []
        for arg in args:
            # Use shlex.quote for proper shell escaping
            sanitized_args.append(shlex.quote(str(arg)))

        # Use thread lock to prevent concurrent linter execution
        with linter_lock:
            try:
                # Special handling for different linters
                if linter == "flake8":
                    # flake8 is safe as it only takes the filepath
                    result = subprocess.run(
                        ["flake8", filepath],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=LINTER_TIMEOUT_SECONDS,
                    )
                elif linter == "eslint":
                    # Use shlex.split for safer command construction
                    cmd = shlex.split(f"eslint {shlex.quote(filepath)}") + [
                        arg for arg in sanitized_args if arg
                    ]
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=LINTER_TIMEOUT_SECONDS,
                    )
                elif linter == "cppcheck":
                    cmd = shlex.split(f"cppcheck {shlex.quote(filepath)}") + [
                        arg for arg in sanitized_args if arg
                    ]
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=LINTER_TIMEOUT_SECONDS,
                    )
                elif linter == "shellcheck":
                    cmd = shlex.split(f"shellcheck {shlex.quote(filepath)}") + [
                        arg for arg in sanitized_args if arg
                    ]
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=LINTER_TIMEOUT_SECONDS,
                    )
                else:
                    self.logger.warning(f"Unsupported linter: {linter}")
                    return [], False

                # Linter ran successfully
                if result.stdout:
                    return result.stdout.strip().split("\n"), True
                elif result.stderr:
                    return result.stderr.strip().split("\n"), True
                else:
                    return [], True

            except FileNotFoundError:
                self.logger.error(f"Linter not found: {linter}")
                return [], False
            except subprocess.TimeoutExpired:
                self.logger.warning(f"Linter {linter} timed out for {filepath}")
                return [f"Linter {linter} timed out for {filepath}"], False
            except Exception as e:
                self.logger.error(f"An error occurred while running {linter}: {e}")
                return [f"An error occurred while running {linter}: {e}"], False

    def _parse_linter_output(
        self, line: str, language: str
    ) -> Optional[Tuple[int, str]]:
        """
        Parse linter output to extract line number and issue description.
        Handles different output formats for different linters.
        """
        if language == "python":
            # flake8 format: file:line:col: code message
            match = re.match(r".*:(\d+):\d+: (.*)", line)
        elif language in ["javascript", "typescript"]:
            # eslint format: file:line:col: message
            match = re.match(r".*:(\d+):\d+: (.*)", line)
        elif language in ["c", "cpp"]:
            # cppcheck format: file:line: severity: message
            match = re.match(r".*:(\d+): (.*)", line)
        elif language == "shell":
            # shellcheck format: file:line:col: severity: message
            match = re.match(r".*:(\d+):\d+: (.*)", line)
        else:
            # Generic format: try to extract line number
            match = re.match(r".*:(\d+).*: (.*)", line)

        if match:
            return int(match.group(1)), match.group(2).strip()
        return None

    def _handle_scan_completion(self, future: Future[Dict[str, Any]]) -> None:
        """Handle scan completion, invoking the callback."""
        current_scan_id = self._current_scan_id

        try:
            task_result = future.result()
        except Exception as e:
            self.error_handler.handle_error(
                e, "scanner_service", "_handle_scan_completion", ErrorSeverity.CRITICAL
            )
            if current_scan_id:
                scan_result = self.persistence.get_scan_result(current_scan_id)
                if scan_result:
                    scan_result.status = ScanStatus.FAILED
                    self.persistence.save_scan_result(scan_result)
            # Cannot call callback here as we don't have it.
            if self._current_scan_id == current_scan_id:
                self._current_scan_id = None
            return

        scan_id = task_result.get("scan_id")
        callback = task_result.get("callback")

        if callback:
            try:
                if task_result.get("status") == "completed":
                    callback(task_result.get("result"))
                else:
                    callback(None, task_result.get("error"))
            except TypeError:
                # Callback may not accept error argument
                callback(task_result.get("result"))
            except Exception as e:
                self.logger.error(
                    f"Error in scan completion callback for scan {scan_id}: {e}"
                )

        if self._current_scan_id == scan_id:
            self._current_scan_id = None

    def cancel_scan(self) -> bool:
        """Cancel the current scan operation."""
        if self._current_scan_id:
            self.logger.info(
                f"Requesting cancellation for scan {self._current_scan_id}"
            )
            scan_id_to_cancel = self._current_scan_id
            self._current_scan_id = None  # Signal cancellation to the running loop

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

    def get_all_scan_results(
        self, status: Optional[ScanStatus] = None, limit: int = DEFAULT_SCAN_LIMIT
    ) -> List[ScanResult]:
        """Get all scan results, optionally filtered by status."""
        return self.persistence.get_all_scan_results(status, limit)

    def get_code_issues(
        self, scan_id: str, severity: Optional[IssueSeverity] = None
    ) -> List[PersistenceCodeIssue]:
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
