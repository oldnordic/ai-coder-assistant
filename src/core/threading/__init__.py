"""Thread management for AI Coder Assistant."""

from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
from enum import Enum, auto
from queue import Queue
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, TypeVar
from core.config import Config
from core.logging import LogManager
from core.error import ErrorHandler, ErrorSeverity

T = TypeVar('T')

class TaskStatus(Enum):
    """Task execution status."""
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    REVIEW = "Review"
    DONE = "Done"
    BLOCKED = "Blocked"
    CANCELLED = "Cancelled"
    FAILED = "Failed"
    COMPLETED = "Completed"

@dataclass
class TaskResult:
    """Result of a task execution."""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[Exception] = None

class Task:
    """Represents a task to be executed."""
    
    def __init__(
        self,
        task_id: str,
        func: Callable[..., T],
        args: tuple = (),
        kwargs: dict = None,
        callback: Optional[Callable[[TaskResult], None]] = None
    ):
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.callback = callback
        self.status = TaskStatus.TODO
        self.future: Optional[Future] = None

class ThreadManager:
    """Thread pool and task management.
    
    Provides centralized thread management and task execution across the application.
    Uses a singleton pattern to ensure consistent thread management state.
    """
    
    _instance: Optional['ThreadManager'] = None
    _lock = Lock()
    
    def __new__(cls) -> 'ThreadManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._config = Config()
            self.logger = LogManager().get_logger('thread_manager')
            self.error_handler = ErrorHandler()
            
            self._tasks: Dict[str, Task] = {}
            self._results: Dict[str, TaskResult] = {}
            self._task_queue: Queue[Task] = Queue()
            
            max_workers = self._config.get('app.max_threads', 4)
            self._executor = ThreadPoolExecutor(max_workers=max_workers)
            
            self._initialized = True
    
    def submit_task(
        self,
        task_id: str,
        func: Callable[..., T],
        args: tuple = (),
        kwargs: dict = None,
        callback: Optional[Callable[[TaskResult], None]] = None
    ) -> Task:
        """Submit a task for execution."""
        if task_id in self._tasks:
            raise ValueError(f"Task with ID {task_id} already exists")
        
        task = Task(task_id, func, args, kwargs, callback)
        self._tasks[task_id] = task
        
        future = self._executor.submit(self._execute_task, task)
        task.future = future
        
        self.logger.debug(f"Submitted task {task_id}")
        return task
    
    def _execute_task(self, task: Task) -> None:
        """Execute a task and handle its result."""
        task.status = TaskStatus.IN_PROGRESS
        
        try:
            result = task.func(*task.args, **(task.kwargs or {}))
            task.status = TaskStatus.COMPLETED
            task_result = TaskResult(task.task_id, TaskStatus.COMPLETED, result=result)
        except Exception as e:
            task.status = TaskStatus.FAILED
            self.error_handler.handle_error(
                e,
                'thread_manager',
                '_execute_task',
                ErrorSeverity.ERROR,
                {'task_id': task.task_id}
            )
            task_result = TaskResult(task.task_id, TaskStatus.FAILED, error=e)
        
        self._results[task.task_id] = task_result
        
        if task.callback:
            try:
                task.callback(task_result)
            except Exception as e:
                self.error_handler.handle_error(
                    e,
                    'thread_manager',
                    '_execute_task',
                    ErrorSeverity.WARNING,
                    {'task_id': task.task_id, 'stage': 'callback'}
                )
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task if possible."""
        task = self._tasks.get(task_id)
        if not task or not task.future:
            return False
        
        cancelled = task.future.cancel()
        if cancelled:
            task.status = TaskStatus.CANCELLED
            self._results[task_id] = TaskResult(task_id, TaskStatus.CANCELLED)
        
        return cancelled
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a task."""
        task = self._tasks.get(task_id)
        return task.status if task else None
    
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get the result of a completed task."""
        return self._results.get(task_id)
    
    def get_active_tasks(self) -> List[Task]:
        """Get all active tasks."""
        return [task for task in self._tasks.values()
                if task.status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS)]
    
    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the thread pool."""
        self._executor.shutdown(wait=wait)
        self.logger.info("Thread manager shutdown complete") 