import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import tempfile
from typing import Callable, Any, TypeVar, ParamSpec, Dict, List
import signal
from functools import wraps
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from backend.utils import settings
from PyQt6.QtWidgets import QApplication, QComboBox
from frontend.ui.main_window import AICoderAssistant
from frontend.ui.ai_tab_widgets import setup_ai_tab  # type: ignore

os.environ["QT_QPA_PLATFORM"] = "offscreen"

P = ParamSpec('P')
R = TypeVar('R')

def timeout(seconds: int) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            def handler(signum: int, frame: Any) -> None:
                raise TimeoutError(f"Test timed out after {seconds} seconds")
            old_handler = signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds)
            try:
                print(f"[DEBUG] Starting {func.__name__}")
                result = func(*args, **kwargs)
                print(f"[DEBUG] Finished {func.__name__}")
                return result
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        return wrapper
    return decorator

class TestMainWindowBackendCalls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = QApplication.instance()
        if app is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = app

    @patch('backend.services.ai_tools.generate_report_and_training_data')
    def test_generate_report_and_training_data_called(self, mock_generate_report: MagicMock):
        # Arrange
        mock_generate_report.return_value = ("# Report", "{}")
        window = AICoderAssistant()
        setup_ai_tab(window.ai_tab, window)
        window.suggestion_list = [{"issue_type": "test", "description": "desc"}]  # type: List[Dict[str, str]]
        window.model_source_selector = QComboBox()  # type: ignore
        window.model_source_selector.addItem("Local Model")
        window.current_model_ref = MagicMock()
        window.current_tokenizer_ref = MagicMock()
        print(f"[DEBUG] Before start_report_generation: suggestion_list={window.suggestion_list}, model_source_selector={window.model_source_selector.currentIndex()}, input_file_path={getattr(window, 'input_file_path', None)}")  # type: ignore
        
        # Patch start_worker to call the backend directly and verify arguments
        def fake_start_worker(task_type: str, func: Callable[..., Any], *args: tuple[Any, ...], **kwargs: dict[str, Any]):
            # Verify task type
            self.assertEqual(task_type, 'generate_report')
            # Call the function with args
            func(*args, **kwargs)
        
        window.start_worker = fake_start_worker
        
        # Act
        window.start_report_generation()
        print(f"[DEBUG] After start_report_generation: mock_generate_report.call_count={mock_generate_report.call_count}")
        
        # Assert
        mock_generate_report.assert_called_once_with(
            window.suggestion_list,
            window.model_source_selector.currentText().lower().replace(" ", "_"),
            window.current_model_ref,
            window.current_tokenizer_ref,
            progress_callback=window.update_report_progress
        )

    def test_docker_imports_and_detection(self):
        # Test that Docker detection function is importable and callable
        self.assertTrue(hasattr(settings, 'is_docker_available'))
        # Should return a bool
        result = settings.is_docker_available()
        self.assertIsInstance(result, bool)

    @timeout(20)
    @patch('frontend.ui.main_window.run_build_and_test_in_docker')
    @patch('backend.services.docker_utils.build_docker_image', return_value=(True, 'mock output'))
    @patch('backend.services.docker_utils.run_docker_container', return_value=(True, 'mock output'))
    @patch('PyQt6.QtWidgets.QMessageBox.information', return_value=None)
    @patch('PyQt6.QtWidgets.QMessageBox.critical', return_value=None)
    @patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName', return_value=("", ""))
    @patch('PyQt6.QtWidgets.QFileDialog.getExistingDirectory', return_value="")
    @patch('os.getcwd')
    def test_docker_build_test_call_from_gui(self, mock_getcwd: MagicMock, mock_get_existing_dir: MagicMock, mock_get_open_file: MagicMock, mock_critical: MagicMock, mock_info: MagicMock, mock_run_container: MagicMock, mock_build_image: MagicMock, mock_run_build_and_test: MagicMock):
        print("[DEBUG] Enter test_docker_build_test_call_from_gui")
        mock_run_build_and_test.return_value = {"success": True, "stage": "test", "output": "All tests passed"}
        with tempfile.TemporaryDirectory() as temp_dir:
            window = AICoderAssistant()
            print("[DEBUG] Created AICoderAssistant")
            window.docker_enable_checkbox.setChecked(True)
            window.dockerfile_path_edit.setText("")
            window.build_args_edit.setText("")
            window.run_opts_edit.setText("")
            window.scan_directory = temp_dir
            print("[DEBUG] Set up window fields and scan_directory")
            with patch('os.getcwd', return_value=temp_dir):
                print("[DEBUG] About to call on_test_docker_btn_clicked")
                window.on_test_docker_btn_clicked()
                print("[DEBUG] Called on_test_docker_btn_clicked")
            # Assert only the entry point was called
            print(f"[DEBUG] mock_run_build_and_test.call_count={mock_run_build_and_test.call_count}")
            mock_run_build_and_test.assert_called()
            print("[DEBUG] Exit test_docker_build_test_call_from_gui")

    @patch('frontend.ui.main_window.run_build_and_test_in_docker')
    @patch('backend.services.docker_utils.build_docker_image', return_value=(True, 'mock output'))
    @patch('backend.services.docker_utils.run_docker_container', return_value=(True, 'mock output'))
    @patch('PyQt6.QtWidgets.QMessageBox.information', return_value=None)
    @patch('PyQt6.QtWidgets.QMessageBox.critical', return_value=None)
    @patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName', return_value=("", ""))
    @patch('PyQt6.QtWidgets.QFileDialog.getExistingDirectory', return_value="")
    @patch('os.getcwd')
    def test_docker_integration_triggers_backend_on_scan_complete(self, mock_getcwd: MagicMock, mock_get_existing_dir: MagicMock, mock_get_open_file: MagicMock, mock_critical: MagicMock, mock_info: MagicMock, mock_run_container: MagicMock, mock_build_image: MagicMock, mock_run_build_and_test: MagicMock):
        print("[DEBUG] Start test_docker_integration_triggers_backend_on_scan_complete")
        mock_run_build_and_test.return_value = {"success": True, "stage": "test", "output": "All tests passed"}
        with tempfile.TemporaryDirectory() as temp_dir:
            window = AICoderAssistant()
            print("[DEBUG] Created AICoderAssistant")
            window.docker_enable_checkbox.setChecked(True)
            window.dockerfile_path_edit.setText("")
            window.build_args_edit.setText("")
            window.run_opts_edit.setText("")
            window.scan_directory = temp_dir
            print("[DEBUG] Set up window fields and scan_directory")
            suggestions = [{"issue_type": "test_issue", "description": "desc"}]
            with patch('os.getcwd', return_value=temp_dir):
                print("[DEBUG] About to call handle_scan_complete")
                window.handle_scan_complete(suggestions)  # type: ignore
                print("[DEBUG] Called handle_scan_complete")
            # Assert only the entry point was called
            print(f"[DEBUG] mock_run_build_and_test.call_count={mock_run_build_and_test.call_count}")
            mock_run_build_and_test.assert_called()
            print("[DEBUG] End test_docker_integration_triggers_backend_on_scan_complete")

if __name__ == '__main__':
    unittest.main() 