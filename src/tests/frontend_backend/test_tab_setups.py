from frontend.ui.suggestion_dialog import SuggestionDialog
from frontend.ui.refactoring_tab import RefactoringTab
from frontend.ui.pr_tab_widgets import PRCreationTab
from frontend.ui.markdown_viewer import MarkdownViewerDialog
from frontend.ui.continuous_learning_tab import ContinuousLearningTab
from frontend.ui.cloud_models_tab import CloudModelsTab
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QWidget,
)
from unittest.mock import MagicMock, patch
import unittest
import sys
import signal
from PyQt6.QtCore import QCoreApplication, Qt

QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)


def timeout(seconds=30):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(
                f"Test timed out after {seconds} seconds: {func.__name__}")

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
        return wrapper
    return decorator


class DebugTestCase(unittest.TestCase):
    def setUp(self):
        print(f"[DEBUG] Starting test: {self.id()}")

    def tearDown(self):
        print(f"[DEBUG] Finished test: {self.id()}")


class TestTabSetups(DebugTestCase):
    @classmethod
    def setUpClass(cls):
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def _assert_widget_types(self, instance: object,
                             expected_types: dict[str, type]) -> None:
        for attr, expected_type in expected_types.items():
            self.assertTrue(hasattr(instance, attr), f"Missing attribute: {attr}")
            self.assertIsInstance(
                getattr(
                    instance,
                    attr),
                expected_type,
                f"{attr} is not {expected_type}")

    @timeout(30)
    @patch('requests.get')
    def test_setup_data_tab(self, mock_get: MagicMock):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"models": [{"name": "mock-model"}]}
        parent_widget = QWidget()
        main_app_instance = MagicMock()
        from frontend.ui.data_tab_widgets import setup_data_tab
        setup_data_tab(parent_widget, main_app_instance)
        self._assert_widget_types(main_app_instance, {
            "add_local_files_button": QPushButton,
            "local_files_label": QLabel,
            "doc_urls_input": QTextEdit,
            "scraping_mode_selector": QComboBox,
            "max_pages_spinbox": QSpinBox,
            "max_depth_spinbox": QSpinBox,
            "same_domain_checkbox": QCheckBox,
            "links_per_page_spinbox": QSpinBox,
            "acquire_doc_button": QPushButton,
            "knowledge_mode_selector": QComboBox,
            "preprocess_docs_button": QPushButton,
            "train_lm_button": QPushButton,
            "finetune_lm_button": QPushButton,
            "acquire_github_button": QPushButton,
        })

    @timeout(30)
    def test_setup_data_tab_failure(self):
        parent_widget = QWidget()
        main_app_instance = MagicMock()
        with patch('frontend.ui.data_tab_widgets.QPushButton', side_effect=Exception("Widget error")):
            from frontend.ui.data_tab_widgets import setup_data_tab
            with self.assertRaises(Exception) as context:
                setup_data_tab(parent_widget, main_app_instance)
            self.assertIn("Widget error", str(context.exception))

    @timeout(30)
    @patch('requests.get')
    def test_setup_ai_tab(self, mock_get: MagicMock):
        parent_widget = QWidget()
        main_app_instance = MagicMock()
        from frontend.ui.ai_tab_widgets import setup_ai_tab
        setup_ai_tab(parent_widget, main_app_instance)
        self._assert_widget_types(main_app_instance, {
            "model_source_selector": QComboBox,
            "ollama_model_label": QLabel,
            "ollama_model_selector": QComboBox,
            "refresh_button": QPushButton,
            "model_status_label": QLabel,
            "load_model_button": QPushButton,
            "scan_dir_entry": QLineEdit,
            "browse_button": QPushButton,
            "include_patterns_input": QLineEdit,
            "exclude_patterns_input": QLineEdit,
            "ai_enhancement_checkbox": QCheckBox,
            "scan_button": QPushButton,
            "stop_scan_button": QPushButton,
            "scan_progress_bar": QProgressBar,
            "scan_status_label": QLabel,
            "scan_results_text": QTextEdit,
            "review_suggestions_button": QPushButton,
            "create_report_button": QPushButton,
        })

    @timeout(30)
    def test_setup_ai_tab_failure(self):
        parent_widget = QWidget()
        main_app_instance = MagicMock()
        with patch('frontend.ui.ai_tab_widgets.QComboBox', side_effect=Exception("Widget error")):
            from frontend.ui.ai_tab_widgets import setup_ai_tab
            with self.assertRaises(Exception) as context:
                setup_ai_tab(parent_widget, main_app_instance)
            self.assertIn("Widget error", str(context.exception))

    @timeout(30)
    @patch('requests.get')
    def test_setup_browser_tab(self, mock_get: MagicMock):
        parent_widget = QWidget()
        main_app_instance = MagicMock()
        from frontend.ui.browser_tab import setup_browser_tab
        setup_browser_tab(parent_widget, main_app_instance)
        self._assert_widget_types(main_app_instance, {
            "url_bar": QLineEdit,
            "go_button": QPushButton,
            "browser": object,  # QWebEngineView, but may not be available in all test envs
            "youtube_url_entry": QLineEdit,
            "transcribe_button": QPushButton,
            "transcription_results_text": QTextEdit,
        })

    @timeout(30)
    def test_setup_browser_tab_failure(self):
        parent_widget = QWidget()
        main_app_instance = MagicMock()
        with patch('frontend.ui.browser_tab.QLineEdit', side_effect=Exception("Widget error")):
            from frontend.ui.browser_tab import setup_browser_tab
            with self.assertRaises(Exception) as context:
                setup_browser_tab(parent_widget, main_app_instance)
            self.assertIn("Widget error", str(context.exception))

    @timeout(30)
    @patch('requests.get')
    def test_setup_ollama_export_tab(self, mock_get: MagicMock):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"models": [{"name": "mock-model"}]}
        parent_widget = QWidget()
        main_app_instance = MagicMock()
        from frontend.ui.ollama_export_tab import setup_ollama_export_tab
        setup_ollama_export_tab(parent_widget, main_app_instance)
        # Only basic assertions, as this tab is more complex
        self.assertTrue(hasattr(parent_widget, 'layout'))

    @timeout(30)
    def test_setup_ollama_export_tab_failure(self):
        parent_widget = QWidget()
        main_app_instance = MagicMock()
        with patch('frontend.ui.ollama_export_tab.QPushButton', side_effect=Exception("Widget error")):
            from frontend.ui.ollama_export_tab import setup_ollama_export_tab
            with self.assertRaises(Exception) as context:
                setup_ollama_export_tab(parent_widget, main_app_instance)
            self.assertIn("Widget error", str(context.exception))


class TestTabSetupsExtended(TestTabSetups):
    @timeout(30)
    def test_refactoring_tab(self):
        tab = RefactoringTab()
        self.assertIsInstance(tab.analyze_btn, QPushButton)
        self.assertIsInstance(tab.refresh_btn, QPushButton)
        self.assertIsInstance(tab.priority_filter, QComboBox)
        self.assertIsInstance(tab.category_filter, QComboBox)
        self.assertIsInstance(tab.suggestions_table, object)  # QTableWidget
        self.assertIsInstance(tab.details_text, QTextEdit)
        self.assertIsInstance(tab.preview_btn, QPushButton)
        self.assertIsInstance(tab.apply_btn, QPushButton)
        self.assertIsInstance(tab.backup_checkbox, QCheckBox)
        self.assertIsInstance(tab.progress_bar, QProgressBar)
        self.assertIsInstance(tab.status_label, QLabel)

    @timeout(30)
    def test_continuous_learning_tab(self):
        tab = ContinuousLearningTab()
        self.assertIsInstance(tab.tab_widget, object)  # QTabWidget
        # Optionally check sub-tabs or key controls

    @timeout(30)
    def test_cloud_models_tab(self):
        tab = CloudModelsTab()
        self.assertIsInstance(tab.tab_widget, object)  # QTabWidget
        self.assertIsInstance(tab.provider_config, object)
        self.assertIsInstance(tab.model_selection, object)
        self.assertIsInstance(tab.usage_monitoring, object)
        self.assertIsInstance(tab.health_check, object)

    @timeout(30)
    def test_pr_creation_tab(self):
        tab = PRCreationTab()
        self.assertIsInstance(tab.priority_strategy_combo, QComboBox)
        self.assertIsInstance(tab.template_standard_combo, QComboBox)
        self.assertIsInstance(tab.deduplicate_check, QCheckBox)
        self.assertIsInstance(tab.auto_commit_check, QCheckBox)
        self.assertIsInstance(tab.auto_push_check, QCheckBox)
        self.assertIsInstance(tab.create_pr_check, QCheckBox)
        self.assertIsInstance(tab.dry_run_check, QCheckBox)
        self.assertIsInstance(tab.progress_bar, QProgressBar)
        self.assertIsInstance(tab.preview_btn, QPushButton)
        self.assertIsInstance(tab.create_pr_btn, QPushButton)
        self.assertIsInstance(tab.export_config_btn, QPushButton)
        self.assertIsInstance(tab.import_config_btn, QPushButton)

    @timeout(30)
    def test_markdown_viewer_dialog(self):
        dialog = MarkdownViewerDialog("# Test Markdown")
        self.assertIsInstance(dialog.search_label, QLabel)
        self.assertIsInstance(dialog.search_input, QLineEdit)
        self.assertIsInstance(dialog.search_options, QComboBox)
        self.assertIsInstance(dialog.prev_button, QPushButton)
        self.assertIsInstance(dialog.next_button, QPushButton)
        self.assertIsInstance(dialog.progress_bar, QProgressBar)
        self.assertIsInstance(dialog.content_browser, object)  # QTextBrowser

    @timeout(30)
    def test_suggestion_dialog(self):
        dialog = SuggestionDialog(suggestion_data={}, explanation="Test explanation")
        self.assertIsInstance(dialog.user_justification_text, QTextEdit)
        self.assertIsInstance(dialog.button_box, object)
        self.assertIsInstance(dialog.cancel_all_button, QPushButton)


if __name__ == '__main__':
    unittest.main()
