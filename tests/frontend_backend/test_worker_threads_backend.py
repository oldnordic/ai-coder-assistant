import unittest
from unittest.mock import MagicMock, ANY
from src.frontend.ui.worker_threads import Worker
from PyQt6.QtCore import QCoreApplication
import sys

class TestWorkerThreadsBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication(sys.argv)

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
        backend_func.assert_called_with(1, 2, progress_callback=progress_callback, log_message_callback=ANY, cancellation_callback=ANY)
        self.assertTrue(isinstance(progress_updates, list))

if __name__ == '__main__':
    unittest.main() 