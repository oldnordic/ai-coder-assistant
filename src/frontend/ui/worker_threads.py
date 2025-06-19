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

# worker_threads.py
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QMetaObject, Qt
import traceback
import gc

from backend.utils.constants import WORKER_WAIT_TIME, WAIT_TIMEOUT_SHORT_MS

class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int, str)
    log_message = pyqtSignal(str)

class Worker(QThread):
    """
    A generic worker thread that can run any function in the background.
    This is the final, clean version with proper memory management and thread safety.
    """
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int, str)  # current, total, message
    log_message = pyqtSignal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.progress_callback = kwargs.pop('progress_callback', None)
        self.log_callback = kwargs.pop('log_message_callback', None)
        self._cancelled = False

    def cancel(self):
        """Cancel the worker thread."""
        self._cancelled = True
        self.quit()
        self.wait(WORKER_WAIT_TIME)  # Wait up to 2 seconds
        if self.isRunning():
            self.terminate()
            self.wait(WAIT_TIMEOUT_SHORT_MS)

    def run(self):
        """
        Runs the provided function with its arguments and standardized callbacks.
        """
        try:
            self.log_message.emit(f"Worker thread started")

            # Create thread-safe callbacks that emit signals
            def safe_progress_callback(current, total, message):
                if not self._cancelled:
                    self.progress.emit(current, total, message)

            def safe_log_callback(message):
                if not self._cancelled:
                    self.log_message.emit(message)

            # Add progress callback to kwargs if provided
            if self.progress_callback:
                self.kwargs['progress_callback'] = safe_progress_callback
            else:
                # Default progress callback that emits signals
                self.kwargs['progress_callback'] = safe_progress_callback
            
            # Add log callback to kwargs if provided
            if self.log_callback:
                self.kwargs['log_message_callback'] = safe_log_callback
            else:
                # Default log callback that emits signals
                self.kwargs['log_message_callback'] = safe_log_callback

            # Add cancellation callback
            self.kwargs['cancellation_callback'] = lambda: self._cancelled

            # Execute the function
            result = self.func(*self.args, **self.kwargs)
            
            # Check if cancelled
            if self._cancelled:
                self.log_message.emit("Worker thread cancelled")
                return
            
            # Announce completion
            self.finished.emit(result)
            
        except Exception as e:
            if not self._cancelled:
                error_msg = f"Worker error: {str(e)}\n{traceback.format_exc()}"
                self.error.emit(error_msg)
        finally:
            # Force garbage collection to prevent memory leaks
            try:
                gc.collect()
            except:
                pass  # Ignore garbage collection errors