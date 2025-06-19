import unittest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QWidget, QApplication
from frontend.ui.ollama_export_tab import setup_ollama_export_tab

class TestOllamaExportTabBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    @patch('backend.utils.settings.MODEL_SAVE_PATH', '/tmp/model_dir')
    @patch('backend.utils.constants.HTTP_TIMEOUT_SHORT', 5)
    @patch('backend.utils.constants.HTTP_TIMEOUT_LONG', 30)
    @patch('backend.utils.constants.HTTP_OK', 200)
    def test_setup_ollama_export_tab_uses_backend(self, *_):
        parent_widget = QWidget()
        main_app_instance = MagicMock()
        # Should not raise
        setup_ollama_export_tab(parent_widget, main_app_instance)

if __name__ == '__main__':
    unittest.main() 