import unittest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QWidget, QApplication, QComboBox, QLabel, QPushButton, QLineEdit, QTextEdit, QCheckBox, QProgressBar
from frontend.ui.ai_tab_widgets import setup_ai_tab
import sys
import tempfile
import os

class TestAITabWidgetsBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    @patch('backend.utils.settings.PROJECT_ROOT', tempfile.mkdtemp())
    def test_setup_ai_tab_uses_backend(self, *_):
        parent_widget = QWidget()
        main_app_instance = MagicMock()
        # Should not raise
        setup_ai_tab(parent_widget, main_app_instance)
        # Assertions for expected attributes and types
        self.assertIsInstance(main_app_instance.model_source_selector, QComboBox)
        self.assertIsInstance(main_app_instance.ollama_model_label, QLabel)
        self.assertIsInstance(main_app_instance.ollama_model_selector, QComboBox)
        self.assertIsInstance(main_app_instance.refresh_button, QPushButton)
        self.assertIsInstance(main_app_instance.model_status_label, QLabel)
        self.assertIsInstance(main_app_instance.load_model_button, QPushButton)
        self.assertIsInstance(main_app_instance.scan_dir_entry, QLineEdit)
        self.assertIsInstance(main_app_instance.browse_button, QPushButton)
        self.assertIsInstance(main_app_instance.include_patterns_input, QLineEdit)
        self.assertIsInstance(main_app_instance.exclude_patterns_input, QLineEdit)
        self.assertIsInstance(main_app_instance.ai_enhancement_checkbox, QCheckBox)
        self.assertIsInstance(main_app_instance.scan_button, QPushButton)
        self.assertIsInstance(main_app_instance.stop_scan_button, QPushButton)
        self.assertIsInstance(main_app_instance.scan_progress_bar, QProgressBar)
        self.assertIsInstance(main_app_instance.scan_status_label, QLabel)
        self.assertIsInstance(main_app_instance.scan_results_text, QTextEdit)
        self.assertIsInstance(main_app_instance.review_suggestions_button, QPushButton)
        self.assertIsInstance(main_app_instance.create_report_button, QPushButton)

    def test_setup_ai_tab_failure(self):
        parent_widget = QWidget()
        main_app_instance = MagicMock()
        # Simulate a failure by patching a method to raise
        with patch('frontend.ui.ai_tab_widgets.QComboBox', side_effect=Exception("Widget error")):
            with self.assertRaises(Exception) as context:
                setup_ai_tab(parent_widget, main_app_instance)
            self.assertIn("Widget error", str(context.exception))

if __name__ == '__main__':
    unittest.main() 