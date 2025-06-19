import unittest
from unittest.mock import MagicMock, ANY
from PyQt6.QtWidgets import QApplication
from frontend.ui.worker_threads import Worker
import sys

class TestWorkerThreadsBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_worker_calls_backend_and_emits_progress(self):
        # Arrange
        backend_func = MagicMock()
        backend_func.return_value = 'done'
        progress_updates = []
        def progress_callback(current, total, message):
            progress_updates.append((current, total, message))
        worker = Worker(backend_func, 1, 2, progress_callback=progress_callback)
        # Connect progress signal
        worker.progress.connect(lambda c, t, m: progress_updates.append((c, t, m)))
        # Act
        worker.run()
        # Assert
        backend_func.assert_called_with(1, 2, progress_callback=ANY, log_message_callback=ANY, cancellation_callback=ANY)

if __name__ == '__main__':
    unittest.main() 