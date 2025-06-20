"""
worker_threads.py

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

import sys
import time
import traceback
import logging
from typing import Any, Callable, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import gc
from datetime import datetime, timedelta
import asyncio

from PyQt6.QtCore import (
    QObject, QThread, pyqtSignal, pyqtSlot, QMutex, QMutexLocker, QCoreApplication
)
from PyQt6.QtWidgets import QApplication

from backend.utils.constants import WORKER_WAIT_TIME

logger = logging.getLogger(__name__)


class WorkerThread(QThread):
    """Worker thread for running long operations without blocking the UI."""
    
    finished = pyqtSignal(str, object)  # worker_id, result
    error = pyqtSignal(str, str)  # worker_id, error message
    progress = pyqtSignal(str, int, int, str)  # worker_id, current, total, message
    log_message = pyqtSignal(str)  # message

    def __init__(self, worker_id: str, func: Callable[..., Any], *args: Any, **kwargs: Any):
        super().__init__()
        self.worker_id = worker_id
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.is_cancelled = False
        self.result: Optional[Any] = None
        self._start_time: Optional[datetime] = None
        self._mutex = QMutex()

    def run(self) -> None:
        """Execute the worker's function and handle signals."""
        self._start_time = datetime.now()
        logger.info(f"Worker '{self.worker_id}' started.")
        
        try:
            # Prepare callbacks
            def progress_callback(current: int, total: int, message: str = "") -> None:
                if not self.is_cancelled:
                    self.progress.emit(self.worker_id, current, total, message)

            def log_message_callback(message: str) -> None:
                if not self.is_cancelled:
                    self.log_message.emit(message)
            
            def cancellation_callback() -> bool:
                return self.is_cancelled

            # Add callbacks to kwargs
            self.kwargs['progress_callback'] = progress_callback
            self.kwargs['log_message_callback'] = log_message_callback
            self.kwargs['cancellation_callback'] = cancellation_callback

            # Execute the function
            if asyncio.iscoroutinefunction(self.func):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self.result = loop.run_until_complete(self.func(*self.args, **self.kwargs))
                loop.close()
            else:
                self.result = self.func(*self.args, **self.kwargs)

            if self.is_cancelled:
                self.result = None

        except Exception as e:
            if not self.is_cancelled:
                error_str = f"Error in worker '{self.worker_id}': {e}\n{traceback.format_exc()}"
                logger.error(error_str)
                self.error.emit(self.worker_id, error_str)
        finally:
            logger.info(f"Worker '{self.worker_id}' finished.")
            self.finished.emit(self.worker_id, self.result)

    def cancel(self) -> None:
        """Signal the worker to cancel its operation."""
        with QMutexLocker(self._mutex):
            logger.info(f"Cancelling worker '{self.worker_id}'")
            self.is_cancelled = True

    def get_runtime(self) -> Optional[timedelta]:
        """Get the current runtime of the worker."""
        if self._start_time:
            return datetime.now() - self._start_time
        return None

class ThreadManager(QObject):
    """Manages worker threads and provides a centralized interface."""
    
    worker_started = pyqtSignal(str)  # worker_id
    worker_finished = pyqtSignal(str)  # worker_id
    worker_error = pyqtSignal(str, str)  # worker_id, error message
    
    def __init__(self):
        super().__init__()
        self.workers: Dict[str, WorkerThread] = {}
        self.mutex = QMutex()

    def start_worker(self, worker_id: str, func: Callable[..., Any], *args: Any, **kwargs: Any) -> WorkerThread:
        """Create, configure, and start a new worker thread."""
        with QMutexLocker(self.mutex):
            if worker_id in self.workers and self.workers[worker_id].isRunning():
                logger.warning(f"Worker with ID '{worker_id}' is already running. Cannot start another.")
                return self.workers[worker_id]

            callback = kwargs.pop('callback', None)
            error_callback = kwargs.pop('error_callback', None)
            
            worker = WorkerThread(worker_id, func, *args, **kwargs)
            worker.finished.connect(self._on_worker_finished)
            worker.error.connect(self._on_worker_error)
            
            if callback:
                worker.finished.connect(lambda w_id, result: callback(result) if w_id == worker_id else None)
            if error_callback:
                worker.error.connect(lambda w_id, err: error_callback(err) if w_id == worker_id else None)
            
            self.workers[worker_id] = worker
            worker.start()
            logger.info(f"Started worker: {worker_id}")
            self.worker_started.emit(worker_id)
            return worker

    def cancel_worker(self, worker_id: str) -> bool:
        """Cancel a running worker by its ID."""
        with QMutexLocker(self.mutex):
            worker = self.workers.get(worker_id)
            if worker and worker.isRunning():
                worker.cancel()
                return True
            return False

    @pyqtSlot(str, object)
    def _on_worker_finished(self, worker_id: str, result: Any) -> None:
        """Handle worker finished signal."""
        logger.info(f"Worker '{worker_id}' finished signal received.")
        self.worker_finished.emit(worker_id)
        self._cleanup_worker(worker_id)

    @pyqtSlot(str, str)
    def _on_worker_error(self, worker_id: str, error: str) -> None:
        """Handle worker error signal."""
        logger.error(f"Worker '{worker_id}' error signal received: {error}")
        self.worker_error.emit(worker_id, error)
        self._cleanup_worker(worker_id)
        
    def _cleanup_worker(self, worker_id: str):
        """Remove worker from the manager."""
        with QMutexLocker(self.mutex):
            if worker_id in self.workers:
                worker = self.workers.pop(worker_id)
                worker.deleteLater()

    def shutdown(self) -> None:
        """Cancel all running workers and wait for them to terminate."""
        logger.info("Shutting down ThreadManager, cancelling all workers...")
        with QMutexLocker(self.mutex):
            worker_ids = list(self.workers.keys())

        for worker_id in worker_ids:
            worker = self.workers.get(worker_id)
            if worker:
                logger.info(f"Cancelling worker during shutdown: {worker_id}")
                worker.cancel()
        
        # Wait for all threads to finish
        for worker_id in worker_ids:
             worker = self.workers.get(worker_id)
             if worker and worker.isRunning():
                logger.info(f"Waiting for worker '{worker_id}' to terminate...")
                if not worker.wait(WORKER_WAIT_TIME):
                    logger.warning(f"Worker '{worker_id}' did not terminate gracefully.")
        
        logger.info("ThreadManager shutdown complete")

_thread_manager_instance: Optional[ThreadManager] = None
_thread_manager_lock = QMutex()

def get_thread_manager() -> ThreadManager:
    """Get the global thread manager instance, creating it if necessary."""
    global _thread_manager_instance
    with QMutexLocker(_thread_manager_lock):
        if _thread_manager_instance is None:
            _thread_manager_instance = ThreadManager()
        return _thread_manager_instance

def shutdown_thread_manager() -> None:
    """Shutdown the global thread manager."""
    with QMutexLocker(_thread_manager_lock):
        if _thread_manager_instance:
            _thread_manager_instance.shutdown()
            _thread_manager_instance = None