# worker_threads.py
from PyQt6.QtCore import QObject, QThread, pyqtSignal

class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int, str)
    log_message = pyqtSignal(str)

class Worker(QThread):
    """
    A generic worker thread that can run any function in the background.
    This is the final, clean version.
    """
    def __init__(self, task_type, func, *args, **kwargs):
        super().__init__()
        self.signals = WorkerSignals()
        self.task_type = task_type
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """
        Runs the provided function with its arguments and standardized callbacks.
        """
        try:
            self.signals.log_message.emit(f"Worker thread started for task: {self.task_type}")

            # Prepare standardized callbacks to pass to the target function
            self.kwargs['progress_callback'] = self.signals.progress.emit
            self.kwargs['log_message_callback'] = self.signals.log_message.emit

            # Execute the function
            result = self.func(*self.args, **self.kwargs)
            
            # Announce completion
            self.signals.finished.emit(result)
        except Exception as e:
            # Propagate any errors that occur
            self.signals.error.emit(f"{self.task_type} Error: {e}")