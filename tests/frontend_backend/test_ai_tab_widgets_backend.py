import unittest
from unittest.mock import patch, MagicMock
from src.frontend.ui.ai_tab_widgets import setup_ai_tab
from PyQt6.QtWidgets import QWidget, QApplication
import sys

class TestAITabWidgetsBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    @patch('src.backend.utils.settings.PROJECT_ROOT', '/tmp/project_root')
    def test_setup_ai_tab_uses_backend(self, _):
        parent_widget = QWidget()
        main_app_instance = MagicMock()
        # Should not raise
        setup_ai_tab(parent_widget, main_app_instance)

if __name__ == '__main__':
    unittest.main() 