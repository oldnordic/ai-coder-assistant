import traceback
from PyQt5.QtCore import QObject, pyqtSignal

class Worker(QObject):
    finished = pyqtSignal()
    error_signal = pyqtSignal(str, str)
    progress = pyqtSignal(int, int, str)
    log_message = pyqtSignal(str)
    scan_results_signal = pyqtSignal(dict)

    def __init__(self, task_type, func, args):
        super().__init__()
        self.task_type = task_type
        self.func = func
        self.args = args

    def run(self):
        try:
            result = self.func(
                *self.args,
                log_message_callback=self.log_message.emit,
                progress_callback=self.progress.emit
            )
            if self.task_type == 'scan_code':
                self.scan_results_signal.emit(result)
        except Exception as e:
            tb_str = traceback.format_exc()
            error_message = f"An error occurred in the worker thread for task '{self.task_type}':\n{tb_str}"
            self.log_message.emit(error_message)
            self.error_signal.emit(f"Error in '{self.task_type}' task", f"An exception occurred: {e}")
        finally:
            self.finished.emit()