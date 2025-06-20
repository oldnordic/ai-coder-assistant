"""
task_management.py

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

"""
Task Management Service
Provides persistent task management with advanced features including:
- Task creation, editing, and deletion
- Status tracking and workflow management
- Priority management and filtering
- Team collaboration features
- Task analytics and reporting
"""

from src.core.logging import LogManager
from src.core.events import Event, EventBus, EventType
from src.core.error import ErrorHandler, ErrorSeverity
from src.core.config import Config
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, TypeVar
from pathlib import Path
from enum import Enum, auto
from datetime import datetime, timedelta
from dataclasses import asdict, dataclass, field
from contextlib import contextmanager
import time
import threading
import sqlite3
import queue
import logging
import json
import concurrent.futures
import heapq


# Define our own TaskStatus enum since we removed the core.threading module


class TaskStatus(Enum):
    """Canonical task status values."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"
    FAILED = "failed"
    BLOCKED = "blocked"


# Mapping from various string representations to the canonical enum value
STATUS_MAP = {
    # Variants for 'todo'
    "Pending": "todo",
    "pending": "todo",
    "PENDING": "todo",
    "To Do": "todo",
    "to do": "todo",
    "TODO": "todo",
    # Variants for 'in_progress'
    "In Progress": "in_progress",
    "in progress": "in_progress",
    "IN_PROGRESS": "in_progress",
    "Running": "in_progress",
    "running": "in_progress",
    "RUNNING": "in_progress",
    # Variants for 'done'
    "Done": "done",
    "done": "done",
    "DONE": "done",
    "Completed": "done",
    "completed": "done",
    "COMPLETED": "done",
    # Variants for other statuses
    "Cancelled": "cancelled",
    "cancelled": "cancelled",
    "CANCELLED": "cancelled",
    "Failed": "failed",
    "failed": "failed",
    "FAILED": "failed",
    "Blocked": "blocked",
    "blocked": "blocked",
    "BLOCKED": "blocked",
    "Review": "review",
    "review": "review",
    "REVIEW": "review",
}


def _normalize_status(status_str: str) -> TaskStatus:
    """Normalizes a status string and returns a TaskStatus enum member."""
    if not isinstance(status_str, str):
        # If it's already an enum or something else, return it as is if valid
        if isinstance(status_str, TaskStatus):
            return status_str
        # Otherwise, it's an unknown type, try to convert to string
        status_str = str(status_str)

    normalized_value = STATUS_MAP.get(status_str, status_str.lower())
    try:
        return TaskStatus(normalized_value)
    except ValueError:
        logger.warning(
            f"'{status_str}' normalized to '{normalized_value}' which is not a valid TaskStatus. Defaulting to TODO."
        )
        return TaskStatus.TODO


class TaskResult:
    """Task result class."""

    def __init__(self, task_id: str, status: TaskStatus, result=None, error=None):
        self.task_id = task_id
        self.status = status
        self.result = result
        self.error = error
        self.completed_at = datetime.now()


logger = logging.getLogger(__name__)

T = TypeVar("T")


class TaskPriority(Enum):
    """Task priority levels."""

    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class TaskCategory(Enum):
    """Task categories."""

    SCAN = auto()
    MODEL = auto()
    ANALYSIS = auto()
    REFACTOR = auto()
    MAINTENANCE = auto()
    OTHER = auto()


@dataclass
class TaskMetadata:
    """Task metadata."""

    category: TaskCategory
    priority: TaskPriority
    description: str
    created_at: float
    tags: Set[str]
    dependencies: Set[str]


@dataclass
class Task:
    """Task data structure."""

    id: int
    title: str
    description: str
    assignee: str
    status: TaskStatus
    priority: TaskPriority
    created_date: datetime
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[int] = field(default_factory=list)
    parent_task_id: Optional[int] = None
    project: str = "Default"
    created_by: str = "System"
    last_modified: Optional[datetime] = None

    def __post_init__(self):
        if self.last_modified is None:
            self.last_modified = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data["status"] = self.status.value
        data["priority"] = self.priority.value
        data["created_date"] = (
            self.created_date.isoformat() if self.created_date else None
        )
        data["due_date"] = self.due_date.isoformat() if self.due_date else None
        data["completed_date"] = (
            self.completed_date.isoformat() if self.completed_date else None
        )
        data["last_modified"] = (
            self.last_modified.isoformat() if self.last_modified else None
        )
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create Task from dictionary."""
        # Map legacy/alternate status values to enum
        status_map = {
            "Pending": "To Do",
            "pending": "To Do",
            "PENDING": "To Do",
            "Running": "In Progress",
            "running": "In Progress",
            "RUNNING": "In Progress",
            "Completed": "Completed",
            "completed": "Completed",
            "COMPLETED": "Completed",
            "Done": "Done",
            "done": "Done",
            "DONE": "Done",
            "Cancelled": "Cancelled",
            "cancelled": "Cancelled",
            "CANCELLED": "Cancelled",
            "Failed": "Failed",
            "failed": "Failed",
            "FAILED": "Failed",
            "Blocked": "Blocked",
            "blocked": "Blocked",
            "BLOCKED": "Blocked",
            "To Do": "To Do",
            "to do": "To Do",
            "TODO": "To Do",
            "In Progress": "In Progress",
            "in progress": "In Progress",
            "IN_PROGRESS": "In Progress",
            "Review": "Review",
            "review": "Review",
            "REVIEW": "Review",
        }

        # Map legacy/alternate priority values to enum
        priority_map = {
            "Low": TaskPriority.LOW,
            "low": TaskPriority.LOW,
            "LOW": TaskPriority.LOW,
            "Medium": TaskPriority.MEDIUM,
            "medium": TaskPriority.MEDIUM,
            "MEDIUM": TaskPriority.MEDIUM,
            "High": TaskPriority.HIGH,
            "high": TaskPriority.HIGH,
            "HIGH": TaskPriority.HIGH,
            "Critical": TaskPriority.CRITICAL,
            "critical": TaskPriority.CRITICAL,
            "CRITICAL": TaskPriority.CRITICAL,
        }

        status_str = data["status"]
        status_str = status_map.get(status_str, status_str)
        data["status"] = _normalize_status(status_str)

        # Handle priority conversion
        priority_value = data["priority"]
        if isinstance(priority_value, str):
            data["priority"] = priority_map.get(priority_value, TaskPriority.MEDIUM)
        else:
            data["priority"] = TaskPriority(priority_value)

        # Convert ISO strings back to datetime objects
        if isinstance(data["created_date"], str):
            data["created_date"] = datetime.fromisoformat(data["created_date"])
        if data.get("due_date") and isinstance(data["due_date"], str):
            data["due_date"] = datetime.fromisoformat(data["due_date"])
        if data.get("completed_date") and isinstance(data["completed_date"], str):
            data["completed_date"] = datetime.fromisoformat(data["completed_date"])
        if data.get("last_modified") and isinstance(data["last_modified"], str):
            data["last_modified"] = datetime.fromisoformat(data["last_modified"])
        return cls(**data)


@dataclass
class TaskAnalytics:
    """Task analytics data."""

    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    overdue_tasks: int
    completion_rate: float
    average_completion_time: Optional[float] = None
    tasks_by_priority: Dict[str, int] = field(default_factory=dict)
    tasks_by_assignee: Dict[str, int] = field(default_factory=dict)


class DatabaseConnectionPool:
    """Thread-safe database connection pool for better concurrency."""

    def __init__(self, db_path: Path, max_connections: int = 10):
        self.db_path = db_path
        self.max_connections = max_connections
        self._connections: queue.Queue[sqlite3.Connection] = queue.Queue(
            maxsize=max_connections
        )
        self._lock = threading.Lock()

        # Initialize connections
        for _ in range(max_connections):
            conn = sqlite3.connect(str(db_path), check_same_thread=False)
            conn.execute(
                "PRAGMA journal_mode=WAL"
            )  # Enable WAL mode for better concurrency
            conn.execute(
                "PRAGMA synchronous=NORMAL"
            )  # Balance between safety and performance
            conn.execute("PRAGMA cache_size=10000")  # Increase cache size
            conn.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
            self._connections.put(conn)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection from the pool."""
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = self._connections.get(timeout=5.0)  # 5 second timeout
            yield conn
        except queue.Empty:
            raise Exception("Database connection pool exhausted")
        finally:
            if conn:
                try:
                    self._connections.put(conn, timeout=1.0)
                except queue.Full:
                    conn.close()  # Close if pool is full

    def close_all(self) -> None:
        """Close all connections in the pool."""
        while not self._connections.empty():
            try:
                conn = self._connections.get_nowait()
                conn.close()
            except queue.Empty:
                break


class TaskManagementService:
    """
    Main task management service with persistence and advanced features.
    Now includes thread-safe priority scheduling and dependency resolution.
    Enhanced with connection pooling and better error handling.
    """

    def __init__(self, data_dir: str = "data", db_name: str = "tasks.db"):
        """
        Initialize task management service.

        Args:
            data_dir: Directory for storing task data
            db_name: SQLite database filename
        """
        try:
            self.data_dir = Path(data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)

            self.db_path = self.data_dir / db_name
            self._lock = threading.Lock()

            # Initialize connection pool
            self._init_database()
            self.connection_pool = DatabaseConnectionPool(self.db_path)

            # Load initial data
            self._load_sample_tasks()

            logger.info("Task Management Service initialized with connection pool")

            # Try to import optional dependencies
            try:
                from src.core.config import Config

                self.config = Config()
            except ImportError:
                logger.warning(
                    "Config module not available, using default configuration"
                )
                self.config = None

            try:
                from src.core.logging import LogManager

                self.logger = LogManager().get_logger("task_service")
            except ImportError:
                logger.warning("LogManager not available, using default logger")
                self.logger = logger

            try:
                from src.core.error import ErrorHandler

                self.error_handler = ErrorHandler()
            except ImportError:
                logger.warning("ErrorHandler not available")
                self.error_handler = None

            try:
                from src.core.events import EventBus

                self.event_bus = EventBus()
            except ImportError:
                logger.warning("EventBus not available")
                self.event_bus = None

            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

            self._tasks: Dict[str, TaskMetadata] = {}
            self._dependencies: Dict[str, Set[str]] = {}
            self._blocked_tasks: Set[str] = set()
            self._completed_tasks: Set[str] = set()
            self._priority_queue = []  # (priority, created_date, task_id)
            self._queue_lock = threading.Lock()
            self._scheduled_tasks: Set[int] = set()

        except Exception as e:
            logger.error(f"Failed to initialize TaskManagementService: {e}")
            # Set minimal attributes to prevent further crashes
            self.data_dir = Path(data_dir)
            self.db_path = self.data_dir / db_name
            self._lock = threading.Lock()
            self.config = None
            self.logger = logger
            self.error_handler = None
            self.event_bus = None
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
            self._tasks = {}
            self._dependencies = {}
            self._blocked_tasks = set()
            self._completed_tasks = set()
            self._priority_queue = []
            self._queue_lock = threading.Lock()
            self._scheduled_tasks = set()

    def _init_database(self):
        """Initialize database with enhanced schema and indexes."""
        with sqlite3.connect(self.db_path) as conn:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys=ON")

            # Create tasks table with indexes for better performance
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    assignee TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    created_date TEXT NOT NULL,
                    due_date TEXT,
                    completed_date TEXT,
                    estimated_hours REAL,
                    actual_hours REAL,
                    tags TEXT,
                    dependencies TEXT,
                    parent_task_id INTEGER,
                    project TEXT DEFAULT 'Default',
                    created_by TEXT DEFAULT 'System',
                    last_modified TEXT NOT NULL
                )
            """
            )

            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)"
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    timestamp TEXT NOT NULL,
                    user TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
                )
            """
            )

            # Create index for task history
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON task_history(task_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_history_timestamp ON task_history(timestamp)"
            )

            conn.commit()

    def _execute_with_retry(
        self, operation: Callable[[sqlite3.Connection], Any], max_retries: int = 3
    ) -> Any:
        """Execute database operation with retry logic."""
        last_exception: Optional[Exception] = None
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

    def _load_sample_tasks(self) -> None:
        """Load sample tasks if database is empty."""
        try:

            def load_operation(conn: sqlite3.Connection) -> None:
                cursor = conn.execute("SELECT COUNT(*) FROM tasks")
                if cursor.fetchone()[0] == 0:
                    sample_tasks = [
                        {
                            "title": "Implement user authentication system",
                            "description": "Create a secure user authentication system with JWT tokens",
                            "assignee": "Alice",
                            "status": TaskStatus.IN_PROGRESS,
                            "priority": TaskPriority.HIGH,
                            "created_date": datetime.now() - timedelta(days=2),
                            "due_date": datetime.now() + timedelta(days=5),
                            "estimated_hours": 16.0,
                            "tags": ["backend", "security", "authentication"],
                            "project": "User Management",
                            "created_by": "Project Manager",
                        },
                        {
                            "title": "Fix database connection timeout issue",
                            "description": "Resolve intermittent database connection timeouts",
                            "assignee": "Bob",
                            "status": TaskStatus.DONE,
                            "priority": TaskPriority.MEDIUM,
                            "created_date": datetime.now() - timedelta(days=3),
                            "completed_date": datetime.now() - timedelta(days=1),
                            "estimated_hours": 4.0,
                            "actual_hours": 3.5,
                            "tags": ["database", "bug-fix"],
                            "project": "Infrastructure",
                            "created_by": "System Admin",
                        },
                    ]

                    for task_data in sample_tasks:
                        try:
                            self._insert_task(task_data)
                        except Exception as e:
                            logger.warning(
                                f"Failed to insert sample task '{task_data['title']}': {e}"
                            )
                            continue

                    logger.info("Loaded sample tasks")

            self._execute_with_retry(load_operation)
        except Exception as e:
            logger.warning(f"Failed to load sample tasks: {e}")
            # Don't raise the exception - continue without sample tasks

    def _insert_task(self, task_data: Dict[str, Any]) -> int:
        """Insert a task into the database with retry logic."""

        def insert_operation(conn: sqlite3.Connection) -> int:
            cursor = conn.execute(
                """
                INSERT INTO tasks (
                    title, description, assignee, status, priority, created_date,
                    due_date, completed_date, estimated_hours, actual_hours,
                    tags, dependencies, parent_task_id, project, created_by, last_modified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    task_data["title"],
                    task_data.get("description", ""),
                    task_data["assignee"],
                    task_data["status"].value,
                    task_data["priority"].value,
                    (
                        task_data["created_date"].isoformat()
                        if task_data.get("created_date")
                        else None
                    ),
                    (
                        task_data.get("due_date").isoformat()
                        if task_data.get("due_date")
                        else None
                    ),
                    (
                        task_data.get("completed_date").isoformat()
                        if task_data.get("completed_date")
                        else None
                    ),
                    task_data.get("estimated_hours"),
                    task_data.get("actual_hours"),
                    json.dumps(task_data.get("tags", [])),
                    json.dumps(task_data.get("dependencies", [])),
                    task_data.get("parent_task_id"),
                    task_data.get("project", "Default"),
                    task_data.get("created_by", "System"),
                    datetime.now().isoformat(),
                ),
            )
            task_id = cursor.lastrowid
            return int(task_id) if task_id is not None else -1

        return self._execute_with_retry(insert_operation)

    def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID with retry logic."""

        def get_operation(conn: sqlite3.Connection) -> Optional[Task]:
            cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            return self._row_to_task(row) if row else None

        return self._execute_with_retry(get_operation)

    def get_all_tasks(
        self,
        project: Optional[str] = None,
        assignee: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
    ) -> List[Task]:
        """Get all tasks with filtering and retry logic."""

        def get_all_operation(conn: sqlite3.Connection) -> List[Task]:
            query = "SELECT * FROM tasks WHERE 1=1"
            params = []

            if project:
                query += " AND project = ?"
                params.append(project)
            if assignee:
                query += " AND assignee = ?"
                params.append(assignee)
            if status:
                query += " AND status = ?"
                params.append(status.value)
            if priority:
                query += " AND priority = ?"
                params.append(priority.value)

            query += " ORDER BY priority DESC, created_date ASC"

            cursor = conn.execute(query, params)
            return [self._row_to_task(row) for row in cursor.fetchall()]

        return self._execute_with_retry(get_all_operation)

    def __del__(self):
        """Cleanup connection pool on destruction."""
        if hasattr(self, "connection_pool"):
            self.connection_pool.close_all()

    def create_task(
        self,
        title: str,
        description: str,
        assignee: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[datetime] = None,
        estimated_hours: Optional[float] = None,
        tags: Optional[List[str]] = None,
        project: str = "Default",
        created_by: str = "System",
    ) -> Task:
        """
        Create a new task.

        Args:
            title: Task title
            description: Task description
            assignee: Task assignee
            priority: Task priority
            due_date: Due date
            estimated_hours: Estimated hours to complete
            tags: Task tags
            project: Project name
            created_by: User who created the task

        Returns:
            Created Task object
        """
        with self._lock:
            task_data = {
                "title": title,
                "description": description,
                "assignee": assignee,
                "status": TaskStatus.TODO,
                "priority": priority,
                "created_date": datetime.now(),
                "due_date": due_date,
                "estimated_hours": estimated_hours,
                "tags": tags or [],
                "project": project,
                "created_by": created_by,
            }

            task_id = self._insert_task(task_data)
            task_data["id"] = task_id

            # Log task creation
            self._log_task_action(task_id, "created", None, None, created_by)

            logger.info(f"Created task: {title} (ID: {task_id})")
            return Task.from_dict(task_data)

    def update_task(self, task_id: int, **kwargs) -> Optional[Task]:
        """
        Update a task.

        Args:
            task_id: Task ID to update
            **kwargs: Fields to update

        Returns:
            Updated Task object or None if not found
        """
        with self._lock:
            task = self.get_task(task_id)
            if not task:
                return None

            # Track changes for logging
            changes = {}

            # Update fields
            for field, value in kwargs.items():
                if hasattr(task, field) and getattr(task, field) != value:
                    old_value = getattr(task, field)
                    setattr(task, field, value)
                    changes[field] = (old_value, value)

            if not changes:
                return task

            # Update database
            with sqlite3.connect(self.db_path) as conn:
                # Build dynamic update query
                set_clauses = []
                params = []

                for field, value in kwargs.items():
                    if field in ["status", "priority"]:
                        set_clauses.append(f"{field} = ?")
                        params.append(value.value if hasattr(value, "value") else value)
                    elif field in ["due_date", "completed_date"]:
                        set_clauses.append(f"{field} = ?")
                        params.append(value.isoformat() if value else None)
                    elif field in ["tags", "dependencies"]:
                        set_clauses.append(f"{field} = ?")
                        params.append(json.dumps(value) if value else "[]")
                    else:
                        set_clauses.append(f"{field} = ?")
                        params.append(value)

                set_clauses.append("last_modified = ?")
                params.append(datetime.now().isoformat())
                params.append(task_id)

                query = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?"
                conn.execute(query, params)

            # Log changes
            for field, (old_val, new_val) in changes.items():
                self._log_task_action(
                    task_id, f"updated_{field}", str(old_val), str(new_val), "System"
                )

            logger.info(f"Updated task {task_id}: {list(changes.keys())}")
            return task

    def delete_task(self, task_id: int) -> bool:
        """
        Delete a task.

        Args:
            task_id: Task ID to delete

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            task = self.get_task(task_id)
            if not task:
                return False

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.execute("DELETE FROM task_history WHERE task_id = ?", (task_id,))

            # Log deletion
            self._log_task_action(task_id, "deleted", None, None, "System")

            logger.info(f"Deleted task {task_id}: {task.title}")
            return True

    def complete_task(
        self, task_id: int, actual_hours: Optional[float] = None
    ) -> Optional[Task]:
        """
        Mark a task as completed.

        Args:
            task_id: Task ID to complete
            actual_hours: Actual hours spent on the task

        Returns:
            Updated Task object or None if not found
        """
        update_data = {"status": TaskStatus.DONE, "completed_date": datetime.now()}

        if actual_hours is not None:
            update_data["actual_hours"] = actual_hours

        return self.update_task(task_id, **update_data)

    def get_analytics(self, project: Optional[str] = None) -> TaskAnalytics:
        """
        Get task analytics.

        Args:
            project: Filter analytics by project

        Returns:
            TaskAnalytics object
        """
        tasks = self.get_all_tasks(project=project)

        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status == TaskStatus.DONE)
        in_progress_tasks = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        overdue_tasks = sum(
            1
            for t in tasks
            if t.due_date
            and t.due_date < datetime.now()
            and t.status != TaskStatus.DONE
        )

        completion_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        # Calculate average completion time
        completed_with_dates = [
            t
            for t in tasks
            if t.status == TaskStatus.DONE and t.completed_date and t.created_date
        ]
        if completed_with_dates:
            completion_times = [
                (t.completed_date - t.created_date).total_seconds() / 3600
                for t in completed_with_dates
            ]
            average_completion_time = sum(completion_times) / len(completion_times)
        else:
            average_completion_time = None

        # Tasks by priority
        tasks_by_priority = {}
        for priority in TaskPriority:
            tasks_by_priority[priority.value] = sum(
                1 for t in tasks if t.priority == priority
            )

        # Tasks by assignee
        tasks_by_assignee = {}
        for task in tasks:
            assignee = task.assignee
            tasks_by_assignee[assignee] = tasks_by_assignee.get(assignee, 0) + 1

        return TaskAnalytics(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            overdue_tasks=overdue_tasks,
            completion_rate=completion_rate,
            average_completion_time=average_completion_time,
            tasks_by_priority=tasks_by_priority,
            tasks_by_assignee=tasks_by_assignee,
        )

    def _row_to_task(self, row: Tuple[Any, ...]) -> Task:
        """Convert database row to Task object."""
        # Map legacy/alternate priority values to enum
        priority_map = {
            "Low": TaskPriority.LOW,
            "low": TaskPriority.LOW,
            "LOW": TaskPriority.LOW,
            "Medium": TaskPriority.MEDIUM,
            "medium": TaskPriority.MEDIUM,
            "MEDIUM": TaskPriority.MEDIUM,
            "High": TaskPriority.HIGH,
            "high": TaskPriority.HIGH,
            "HIGH": TaskPriority.HIGH,
            "Critical": TaskPriority.CRITICAL,
            "critical": TaskPriority.CRITICAL,
            "CRITICAL": TaskPriority.CRITICAL,
        }

        # Handle priority conversion
        priority_value = row[5]
        if isinstance(priority_value, str):
            priority = priority_map.get(priority_value, TaskPriority.MEDIUM)
        else:
            priority = TaskPriority(priority_value)

        return Task(
            id=row[0],
            title=row[1],
            description=row[2],
            assignee=row[3],
            status=_normalize_status(row[4]),
            priority=priority,
            created_date=datetime.fromisoformat(row[6]) if row[6] else None,
            due_date=datetime.fromisoformat(row[7]) if row[7] else None,
            completed_date=datetime.fromisoformat(row[8]) if row[8] else None,
            estimated_hours=row[9],
            actual_hours=row[10],
            tags=json.loads(row[11]) if row[11] else [],
            dependencies=json.loads(row[12]) if row[12] else [],
            parent_task_id=row[13],
            project=row[14],
            created_by=row[15],
            last_modified=datetime.fromisoformat(row[16]) if row[16] else None,
        )

    def _log_task_action(
        self,
        task_id: int,
        action: str,
        old_value: Optional[str],
        new_value: Optional[str],
        user: str,
    ):
        """Log a task action to history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO task_history (task_id, action, old_value, new_value, timestamp, user)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    task_id,
                    action,
                    old_value,
                    new_value,
                    datetime.now().isoformat(),
                    user,
                ),
            )

    def submit_task(
        self,
        task_id: str,
        func: Callable[..., T],
        category: TaskCategory,
        priority: TaskPriority = TaskPriority.MEDIUM,
        description: str = "",
        tags: Set[str] = None,
        dependencies: Set[str] = None,
        args: tuple = (),
        kwargs: dict = None,
        callback: Optional[Callable[[Any], None]] = None,
    ) -> bool:
        """Submit a task for execution.

        Args:
            task_id: Unique task identifier
            func: Function to execute
            category: Task category
            priority: Task priority
            description: Task description
            tags: Task tags
            dependencies: Task dependencies
            args: Function arguments
            kwargs: Function keyword arguments
            callback: Completion callback

        Returns:
            bool: True if task was submitted
        """
        try:
            if task_id in self._tasks:
                return False

            # Create task metadata
            metadata = TaskMetadata(
                category=category,
                priority=priority,
                description=description,
                created_at=time.time(),
                tags=tags or set(),
                dependencies=dependencies or set(),
            )

            # Check dependencies
            if metadata.dependencies:
                for dep in metadata.dependencies:
                    if dep not in self._completed_tasks:
                        self._blocked_tasks.add(task_id)
                        break

            # Store task metadata
            self._tasks[task_id] = metadata

            # Update dependency tracking
            for dep in metadata.dependencies:
                if dep not in self._dependencies:
                    self._dependencies[dep] = set()
                self._dependencies[dep].add(task_id)

            # Submit task if not blocked
            if task_id not in self._blocked_tasks:
                self._submit_to_executor(task_id, func, args, kwargs, callback)

            self.event_bus.publish(
                Event(
                    EventType.TASK_STARTED,
                    data={
                        "task_id": task_id,
                        "category": category.name,
                        "priority": priority.name,
                    },
                )
            )

            return True

        except Exception as e:
            self.error_handler.handle_error(
                e,
                "task_service",
                "submit_task",
                ErrorSeverity.ERROR,
                {"task_id": task_id},
            )
            return False

    def _submit_to_executor(
        self,
        task_id: str,
        func: Callable[..., T],
        args: tuple,
        kwargs: dict,
        callback: Optional[Callable[[Any], None]],
    ) -> None:
        """Submit task to thread executor.

        Args:
            task_id: Task identifier
            func: Function to execute
            args: Function arguments
            kwargs: Function keyword arguments
            callback: Completion callback
        """
        future = self.executor.submit(func, *args, **kwargs)
        future.add_done_callback(
            lambda f: self._handle_task_completion(task_id, f, callback)
        )

    def _handle_task_completion(
        self,
        task_id: str,
        future: concurrent.futures.Future,
        callback: Optional[Callable[[Any], None]],
    ):
        """Handle task completion.

        Args:
            task_id: Task identifier
            future: Future object containing the result
            callback: Optional callback function
        """
        try:
            result = future.result()
            task_result = {
                "task_id": task_id,
                "status": TaskStatus.COMPLETED,
                "result": result,
            }
        except Exception as e:
            task_result = {"task_id": task_id, "status": TaskStatus.FAILED, "error": e}

        if task_result["status"] == TaskStatus.COMPLETED:
            # Mark task as completed
            self._completed_tasks.add(task_id)

            # Check dependent tasks
            self._check_dependent_tasks(task_id)

            self.event_bus.publish(
                Event(
                    EventType.TASK_COMPLETED,
                    data={"task_id": task_id, "result": task_result["result"]},
                )
            )
        else:
            self.event_bus.publish(
                Event(
                    EventType.TASK_FAILED,
                    data={"task_id": task_id, "error": task_result.get("error")},
                )
            )

        if callback:
            callback(task_result)

    def _check_dependent_tasks(self, completed_task_id: str) -> None:
        """Check and potentially unblock dependent tasks.

        Args:
            completed_task_id: ID of completed task
        """
        if completed_task_id in self._dependencies:
            for dependent_id in self._dependencies[completed_task_id]:
                metadata = self._tasks[dependent_id]

                # Check if all dependencies are completed
                if all(dep in self._completed_tasks for dep in metadata.dependencies):
                    self._blocked_tasks.discard(dependent_id)

                    # Submit now-unblocked task
                    self._submit_to_executor(
                        dependent_id, lambda: None, (), {}, None  # Placeholder
                    )

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task.

        Args:
            task_id: Task identifier

        Returns:
            bool: True if task was cancelled
        """
        if task_id not in self._tasks:
            return False

        # Remove from blocked tasks if present
        self._blocked_tasks.discard(task_id)

        # Cancel in thread manager if running
        cancelled = self.executor.submit(lambda: None).cancel()

        if cancelled:
            self.event_bus.publish(
                Event(EventType.TASK_CANCELLED, data={"task_id": task_id})
            )

        return cancelled

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status.

        Args:
            task_id: Task identifier

        Returns:
            Optional[TaskStatus]: Task status if found
        """
        if task_id in self._completed_tasks:
            return TaskStatus.DONE
        elif task_id in self._blocked_tasks:
            return TaskStatus.PENDING
        else:
            return None

    def get_task_metadata(self, task_id: str) -> Optional[TaskMetadata]:
        """Get task metadata.

        Args:
            task_id: Task identifier

        Returns:
            Optional[TaskMetadata]: Task metadata if found
        """
        return self._tasks.get(task_id)

    def get_tasks_by_category(self, category: TaskCategory) -> List[str]:
        """Get tasks by category.

        Args:
            category: Task category

        Returns:
            List[str]: List of task IDs
        """
        return [
            task_id
            for task_id, metadata in self._tasks.items()
            if metadata.category == category
        ]

    def get_tasks_by_priority(self, priority: TaskPriority) -> List[str]:
        """Get tasks by priority.

        Args:
            priority: Task priority

        Returns:
            List[str]: List of task IDs
        """
        return [
            task_id
            for task_id, metadata in self._tasks.items()
            if metadata.priority == priority
        ]

    def get_tasks_by_tag(self, tag: str) -> List[str]:
        """Get tasks by tag.

        Args:
            tag: Task tag

        Returns:
            List[str]: List of task IDs
        """
        return [
            task_id for task_id, metadata in self._tasks.items() if tag in metadata.tags
        ]

    def get_blocked_tasks(self) -> List[str]:
        """Get blocked tasks.

        Returns:
            List[str]: List of blocked task IDs
        """
        return list(self._blocked_tasks)

    def get_completed_tasks(self) -> List[str]:
        """Get completed tasks.

        Returns:
            List[str]: List of completed task IDs
        """
        return list(self._completed_tasks)

    def schedule_tasks(self):
        """Schedule tasks based on priority and dependencies."""
        with self._queue_lock:
            all_tasks = self.get_all_tasks()
            for task in all_tasks:
                if task.id in self._scheduled_tasks:
                    continue
                if self._can_schedule(task):
                    heapq.heappush(
                        self._priority_queue,
                        (task.priority.value, task.created_date.timestamp(), task.id),
                    )
                    self._scheduled_tasks.add(task.id)

    def _can_schedule(self, task: Task) -> bool:
        """Check if a task can be scheduled (all dependencies completed)."""
        if not task.dependencies:
            return True
        for dep_id in task.dependencies:
            dep_task = self.get_task(dep_id)
            if not dep_task or dep_task.status != TaskStatus.DONE:
                return False
        return True

    def run_next_task(self):
        """Run the next task in the priority queue."""
        with self._queue_lock:
            if not self._priority_queue:
                return None
            _, _, task_id = heapq.heappop(self._priority_queue)
            task = self.get_task(task_id)
            if not task:
                return None
            # Mark as in progress
            self.update_task(task_id, status=TaskStatus.IN_PROGRESS)
            # Submit to thread manager (simulate execution)
            self.executor.submit(
                lambda: self._execute_task(task_id),
                callback=lambda result: self._on_task_complete(task_id, result),
            )
            return task

    def _execute_task(self, task_id: int):
        """Simulate task execution (replace with real logic)."""
        import time

        time.sleep(1)  # Simulate work
        return True

    def _on_task_complete(self, task_id: int, result: Any):
        """Callback for when a task completes."""
        self.update_task(task_id, status=TaskStatus.DONE)
        self._scheduled_tasks.discard(task_id)
        # After completion, try to schedule more tasks
        self.schedule_tasks()

    def submit_task_with_scheduling(self, *args, **kwargs):
        """Create a task and schedule it for execution."""
        task = self.create_task(*args, **kwargs)
        self.schedule_tasks()
        self.run_next_task()
        return task


# Global instance for easy access
_task_management_service: Optional[TaskManagementService] = None


def get_task_management_service() -> TaskManagementService:
    """Get or create global task management service instance."""
    global _task_management_service
    if _task_management_service is None:
        _task_management_service = TaskManagementService()
    return _task_management_service
