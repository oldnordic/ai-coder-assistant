"""Scanner persistence service for AI Coder Assistant."""

import json
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.backend.services.performance_optimization import PersistencePerformanceMonitor
from src.backend.services.task_management import DatabaseConnectionPool
from src.core.config import Config
from src.core.error import ErrorHandler, ErrorSeverity
from src.core.events import Event, EventBus, EventType
from src.core.logging import LogManager

logger = LogManager().get_logger("scanner_persistence")


class ScanStatus(Enum):
    """Scan status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IssueSeverity(Enum):
    """Issue severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ScanResult:
    """Scan result data."""

    scan_id: str
    scan_type: str
    target_path: str
    model_used: str
    status: ScanStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    total_files: int = 0
    processed_files: int = 0
    issues_found: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CodeIssue:
    """Code issue data."""

    issue_id: str
    scan_id: str
    file_path: str
    line_number: int
    severity: IssueSeverity
    category: str
    description: str
    column_number: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    context: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class FileAnalysis:
    """File analysis data."""

    file_id: str
    scan_id: str
    file_path: str
    file_size: int
    lines_of_code: int
    language: str
    complexity_score: Optional[float] = None
    issues_count: int = 0
    analysis_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class ScannerPersistenceService:
    """Scanner persistence service with robust database operations."""

    def __init__(self, data_dir: str = "data", db_name: str = "scanner.db"):
        """Initialize scanner persistence service."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.data_dir / db_name
        self._lock = threading.Lock()

        # Initialize database and connection pool
        self._init_database()
        self.connection_pool = DatabaseConnectionPool(self.db_path)

        # Initialize core services
        self.config = Config()
        self.logger = LogManager().get_logger("scanner_persistence")
        self.error_handler = ErrorHandler()
        self.event_bus = EventBus()

        # Initialize performance monitor
        self.performance_monitor = PersistencePerformanceMonitor()

        logger.info("Scanner Persistence Service initialized")

    def _init_database(self):
        """Initialize database with enhanced schema and indexes."""
        with sqlite3.connect(self.db_path) as conn:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys=ON")

            # Create scan results table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_results (
                    scan_id TEXT PRIMARY KEY,
                    scan_type TEXT NOT NULL,
                    target_path TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    total_files INTEGER DEFAULT 0,
                    processed_files INTEGER DEFAULT 0,
                    issues_found INTEGER DEFAULT 0,
                    metadata TEXT,
                    created_at TEXT NOT NULL
                )
            """
            )

            # Create code issues table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS code_issues (
                    issue_id TEXT PRIMARY KEY,
                    scan_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    line_number INTEGER NOT NULL,
                    column_number INTEGER,
                    severity TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    suggestion TEXT,
                    code_snippet TEXT,
                    context TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (scan_id) REFERENCES scan_results (scan_id) ON DELETE CASCADE
                )
            """
            )

            # Create file analysis table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS file_analysis (
                    file_id TEXT PRIMARY KEY,
                    scan_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    lines_of_code INTEGER NOT NULL,
                    language TEXT NOT NULL,
                    complexity_score REAL,
                    issues_count INTEGER DEFAULT 0,
                    analysis_data TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (scan_id) REFERENCES scan_results (scan_id) ON DELETE CASCADE
                )
            """
            )

            # Create indexes for better performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_scan_results_status ON scan_results(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_scan_results_created_at ON scan_results(created_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_scan_results_scan_type ON scan_results(scan_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_code_issues_scan_id ON code_issues(scan_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_code_issues_severity ON code_issues(severity)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_code_issues_file_path ON code_issues(file_path)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_file_analysis_scan_id ON file_analysis(scan_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_file_analysis_language ON file_analysis(language)"
            )

            conn.commit()

    def _execute_with_retry(self, operation: callable, max_retries: int = 3) -> Any:
        """Execute database operation with retry logic."""
        last_exception = None
        for attempt in range(max_retries):
            try:
                with self.connection_pool.get_connection() as conn:
                    return operation(conn)
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    time.sleep(0.1 * (2**attempt))  # Exponential backoff
                    last_exception = e
                    continue
                raise
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (2**attempt))
                    continue
                raise
        if last_exception:
            raise last_exception
        raise Exception("Unknown error in database operation")

    def save_scan_result(self, scan_result: ScanResult) -> bool:
        """Save scan result to database."""

        def save_operation(conn: sqlite3.Connection) -> bool:
            conn.execute(
                """
                INSERT OR REPLACE INTO scan_results (
                    scan_id, scan_type, target_path, model_used, status,
                    start_time, end_time, total_files, processed_files,
                    issues_found, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    scan_result.scan_id,
                    scan_result.scan_type,
                    scan_result.target_path,
                    scan_result.model_used,
                    scan_result.status.value,
                    scan_result.start_time.isoformat(),
                    scan_result.end_time.isoformat() if scan_result.end_time else None,
                    scan_result.total_files,
                    scan_result.processed_files,
                    scan_result.issues_found,
                    json.dumps(scan_result.metadata),
                    scan_result.created_at.isoformat(),
                ),
            )
            conn.commit()
            return True

        try:
            success = self._execute_with_retry(save_operation)
            if success:
                self.event_bus.publish(
                    Event(
                        type=(
                            EventType.SCAN_COMPLETED
                            if scan_result.status == ScanStatus.COMPLETED
                            else EventType.SCAN_STARTED
                        ),
                        data={
                            "scan_id": scan_result.scan_id,
                            "status": scan_result.status.value,
                        },
                    )
                )
                self.logger.info(f"Saved scan result: {scan_result.scan_id}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to save scan result {scan_result.scan_id}: {e}")
            self.error_handler.handle_error(
                f"Scan result save failed: {e}", ErrorSeverity.ERROR
            )
            return False

    def get_scan_result(self, scan_id: str) -> Optional[ScanResult]:
        """Get scan result from database."""

        def get_operation(conn: sqlite3.Connection) -> Optional[ScanResult]:
            cursor = conn.execute(
                "SELECT * FROM scan_results WHERE scan_id = ?", (scan_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            return ScanResult(
                scan_id=row[0],
                scan_type=row[1],
                target_path=row[2],
                model_used=row[3],
                status=ScanStatus(row[4]),
                start_time=datetime.fromisoformat(row[5]),
                end_time=datetime.fromisoformat(row[6]) if row[6] else None,
                total_files=row[7],
                processed_files=row[8],
                issues_found=row[9],
                metadata=json.loads(row[10]) if row[10] else {},
                created_at=datetime.fromisoformat(row[11]),
            )

        try:
            return self._execute_with_retry(get_operation)
        except Exception as e:
            self.logger.error(f"Failed to get scan result {scan_id}: {e}")
            return None

    def get_all_scan_results(
        self, status: Optional[ScanStatus] = None, limit: int = 100
    ) -> List[ScanResult]:
        """Get all scan results with optional filtering."""

        def get_all_operation(conn: sqlite3.Connection) -> List[ScanResult]:
            query = "SELECT * FROM scan_results"
            params = []

            if status:
                query += " WHERE status = ?"
                params.append(status.value)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            results = []

            for row in cursor.fetchall():
                results.append(
                    ScanResult(
                        scan_id=row[0],
                        scan_type=row[1],
                        target_path=row[2],
                        model_used=row[3],
                        status=ScanStatus(row[4]),
                        start_time=datetime.fromisoformat(row[5]),
                        end_time=datetime.fromisoformat(row[6]) if row[6] else None,
                        total_files=row[7],
                        processed_files=row[8],
                        issues_found=row[9],
                        metadata=json.loads(row[10]) if row[10] else {},
                        created_at=datetime.fromisoformat(row[11]),
                    )
                )

            return results

        try:
            return self._execute_with_retry(get_all_operation)
        except Exception as e:
            self.logger.error(f"Failed to get scan results: {e}")
            return []

    def save_code_issue(self, issue: CodeIssue) -> bool:
        """Save code issue to database."""

        def save_operation(conn: sqlite3.Connection) -> bool:
            conn.execute(
                """
                INSERT INTO code_issues (
                    issue_id, scan_id, file_path, line_number, column_number,
                    severity, category, description, suggestion, code_snippet,
                    context, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    issue.issue_id,
                    issue.scan_id,
                    issue.file_path,
                    issue.line_number,
                    issue.column_number,
                    issue.severity.value,
                    issue.category,
                    issue.description,
                    issue.suggestion,
                    issue.code_snippet,
                    issue.context,
                    issue.created_at.isoformat(),
                ),
            )
            conn.commit()
            return True

        try:
            success = self._execute_with_retry(save_operation)
            if success:
                self.logger.info(f"Saved code issue: {issue.issue_id}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to save code issue {issue.issue_id}: {e}")
            return False

    def get_code_issues(
        self, scan_id: str, severity: Optional[IssueSeverity] = None
    ) -> List[CodeIssue]:
        """Get code issues for a scan with optional severity filtering."""

        def get_issues_operation(conn: sqlite3.Connection) -> List[CodeIssue]:
            query = "SELECT * FROM code_issues WHERE scan_id = ?"
            params = [scan_id]

            if severity:
                query += " AND severity = ?"
                params.append(severity.value)

            query += " ORDER BY line_number ASC"

            cursor = conn.execute(query, params)
            issues = []

            for row in cursor.fetchall():
                issues.append(
                    CodeIssue(
                        issue_id=row[0],
                        scan_id=row[1],
                        file_path=row[2],
                        line_number=row[3],
                        column_number=row[4],
                        severity=IssueSeverity(row[5]),
                        category=row[6],
                        description=row[7],
                        suggestion=row[8],
                        code_snippet=row[9],
                        context=row[10],
                        created_at=datetime.fromisoformat(row[11]),
                    )
                )

            return issues

        try:
            return self._execute_with_retry(get_issues_operation)
        except Exception as e:
            self.logger.error(f"Failed to get code issues for scan {scan_id}: {e}")
            return []

    def save_file_analysis(self, analysis: FileAnalysis) -> bool:
        """Save file analysis to database."""

        def save_operation(conn: sqlite3.Connection) -> bool:
            conn.execute(
                """
                INSERT INTO file_analysis (
                    file_id, scan_id, file_path, file_size, lines_of_code,
                    language, complexity_score, issues_count, analysis_data, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    analysis.file_id,
                    analysis.scan_id,
                    analysis.file_path,
                    analysis.file_size,
                    analysis.lines_of_code,
                    analysis.language,
                    analysis.complexity_score,
                    analysis.issues_count,
                    json.dumps(analysis.analysis_data),
                    analysis.created_at.isoformat(),
                ),
            )
            conn.commit()
            return True

        try:
            success = self._execute_with_retry(save_operation)
            if success:
                self.logger.info(f"Saved file analysis: {analysis.file_id}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to save file analysis {analysis.file_id}: {e}")
            return False

    def get_file_analysis(self, scan_id: str) -> List[FileAnalysis]:
        """Get file analysis for a scan."""

        def get_analysis_operation(conn: sqlite3.Connection) -> List[FileAnalysis]:
            cursor = conn.execute(
                """
                SELECT * FROM file_analysis
                WHERE scan_id = ?
                ORDER BY file_path ASC
            """,
                (scan_id,),
            )

            analyses = []
            for row in cursor.fetchall():
                analyses.append(
                    FileAnalysis(
                        file_id=row[0],
                        scan_id=row[1],
                        file_path=row[2],
                        file_size=row[3],
                        lines_of_code=row[4],
                        language=row[5],
                        complexity_score=row[6],
                        issues_count=row[7],
                        analysis_data=json.loads(row[8]) if row[8] else {},
                        created_at=datetime.fromisoformat(row[9]),
                    )
                )

            return analyses

        try:
            return self._execute_with_retry(get_analysis_operation)
        except Exception as e:
            self.logger.error(f"Failed to get file analysis for scan {scan_id}: {e}")
            return []

    def get_scanner_analytics(self) -> Dict[str, Any]:
        """Get scanner analytics and statistics."""

        def analytics_operation(conn: sqlite3.Connection) -> Dict[str, Any]:
            # Get total scans
            cursor = conn.execute("SELECT COUNT(*) FROM scan_results")
            total_scans = cursor.fetchone()[0]

            # Get scans by status
            cursor = conn.execute(
                """
                SELECT status, COUNT(*)
                FROM scan_results
                GROUP BY status
            """
            )
            scans_by_status = dict(cursor.fetchall())

            # Get total issues
            cursor = conn.execute("SELECT COUNT(*) FROM code_issues")
            total_issues = cursor.fetchone()[0]

            # Get issues by severity
            cursor = conn.execute(
                """
                SELECT severity, COUNT(*)
                FROM code_issues
                GROUP BY severity
            """
            )
            issues_by_severity = dict(cursor.fetchall())

            # Get recent scans
            cursor = conn.execute(
                """
                SELECT COUNT(*)
                FROM scan_results
                WHERE created_at > datetime('now', '-24 hours')
            """
            )
            recent_scans = cursor.fetchone()[0]

            return {
                "total_scans": total_scans,
                "scans_by_status": scans_by_status,
                "total_issues": total_issues,
                "issues_by_severity": issues_by_severity,
                "recent_scans_24h": recent_scans,
                "last_updated": datetime.now().isoformat(),
            }

        try:
            return self._execute_with_retry(analytics_operation)
        except Exception as e:
            self.logger.error(f"Failed to get scanner analytics: {e}")
            return {}

    def delete_scan_result(self, scan_id: str) -> bool:
        """Delete scan result and all associated data."""

        def delete_operation(conn: sqlite3.Connection) -> bool:
            conn.execute("DELETE FROM scan_results WHERE scan_id = ?", (scan_id,))
            conn.commit()
            return True

        try:
            success = self._execute_with_retry(delete_operation)
            if success:
                self.logger.info(f"Deleted scan result: {scan_id}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to delete scan result {scan_id}: {e}")
            return False

    def __del__(self):
        """Cleanup connection pool on destruction."""
        if hasattr(self, "connection_pool"):
            self.connection_pool.close_all()


# Global instance for easy access
_scanner_persistence_service = None


def get_scanner_persistence_service() -> ScannerPersistenceService:
    """Get the global scanner persistence service instance."""
    global _scanner_persistence_service
    if _scanner_persistence_service is None:
        _scanner_persistence_service = ScannerPersistenceService()
    return _scanner_persistence_service
