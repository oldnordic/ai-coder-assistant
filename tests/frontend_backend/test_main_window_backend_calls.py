import unittest
from unittest.mock import patch, MagicMock
from src.frontend.ui.main_window import AICoderAssistant
from PyQt6.QtWidgets import QApplication
import sys

class TestMainWindowBackendCalls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    @patch('src.backend.services.ai_tools.generate_report_and_training_data')
    def test_generate_report_and_training_data_called(self, mock_generate_report):
        # Arrange
        mock_generate_report.return_value = ("# Report", "{}")
        window = AICoderAssistant()
        window.suggestion_list = [{"issue_type": "test", "description": "desc"}]
        window.model_source_selector.setCurrentIndex(0)
        window.current_model_ref = MagicMock()
        window.current_tokenizer_ref = MagicMock()
        
        # Act
        window.start_report_generation()
        
        # Assert
        mock_generate_report.assert_called()

if __name__ == '__main__':
    unittest.main() 