import traceback
from PyQt5.QtCore import QObject, pyqtSignal

class Worker(QObject):
    """
    A worker object that runs a given function in a separate thread.
    Emits signals for progress, logging, errors, and results.
    """
    finished = pyqtSignal()
    error_signal = pyqtSignal(str, str)
    progress = pyqtSignal(int, int, str)
    log_message = pyqtSignal(str)
    scan_results_signal = pyqtSignal(dict)

    def __init__(self, task_type, func, args, log_callback, progress_callback):
        super().__init__()
        self.task_type = task_type
        self.func = func
        self.args = args
        self.log_callback = log_callback
        self.progress_callback = progress_callback

    def run(self):
        """
        Executes the function and handles signals.
        """
        try:
            # Pass the callback functions to the target function
            result = self.func(
                *self.args,
                log_message_callback=self.log_message.emit,
                progress_callback=self.progress.emit
            )
            
            # If the task was scanning, emit the results
            if self.task_type == 'scan_code':
                self.scan_results_signal.emit(result)

        except Exception as e:
            tb = traceback.format_exc()
            error_message = f"An error occurred in the worker thread for task '{self.task_type}':\n{tb}"
            self.log_message.emit(error_message)
            self.error_signal.emit(f"Error: {self.task_type}", str(e))
        finally:
            self.finished.emit()