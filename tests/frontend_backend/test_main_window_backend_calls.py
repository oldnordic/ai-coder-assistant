import unittest
from unittest.mock import patch, MagicMock
from src.frontend.ui.main_window import AICoderAssistant
from PyQt6.QtWidgets import QApplication
import sys
from src.backend.utils import settings
from src.backend.services import ai_tools

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

    def test_docker_imports_and_detection(self):
        # Test that Docker detection function is importable and callable
        self.assertTrue(hasattr(settings, 'is_docker_available'))
        # Should return a bool
        result = settings.is_docker_available()
        self.assertIsInstance(result, bool)

    @patch('src.backend.services.ai_tools.run_build_and_test_in_docker')
    def test_docker_build_test_call_from_gui(self, mock_run_docker):
        # Arrange
        mock_run_docker.return_value = {"success": True, "stage": "test", "output": "All tests passed"}
        window = AICoderAssistant()
        window.docker_enable_checkbox.setChecked(True)
        window.dockerfile_path_edit.setText("")
        window.build_args_edit.setText("")
        window.run_opts_edit.setText("")
        # Act
        window.on_test_docker_btn_clicked()
        # Assert
        mock_run_docker.assert_called()

    @patch('src.backend.services.ai_tools.run_build_and_test_in_docker')
    def test_docker_integration_triggers_backend_on_scan_complete(self, mock_run_docker):
        # Arrange
        mock_run_docker.return_value = {"success": True, "stage": "test", "output": "All tests passed"}
        window = AICoderAssistant()
        window.docker_enable_checkbox.setChecked(True)
        window.dockerfile_path_edit.setText("")
        window.build_args_edit.setText("")
        window.run_opts_edit.setText("")
        # Act
        window.handle_scan_complete({"dummy": "result"})
        # Assert
        mock_run_docker.assert_called()

if __name__ == '__main__':
    unittest.main() 