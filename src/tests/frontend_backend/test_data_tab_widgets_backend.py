import sys
import unittest

from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QWidget,
)

from frontend.ui.data_tab_widgets import setup_data_tab
from frontend.ui.main_window import AICoderAssistant


class TestDataTabWidgetsBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("[TEST] Before QApplication")
        if QApplication.instance() is None:
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
        print("[TEST] After QApplication")

    def test_setup_data_tab_uses_backend(self):
        print("[TEST] Before QWidget")
        parent_widget: QWidget = QWidget()
        print("[TEST] After QWidget")
        print("[TEST] Before AICoderAssistant")
        main_app_instance: AICoderAssistant = AICoderAssistant()
        print("[TEST] After AICoderAssistant")
        print("[TEST] Before setup_data_tab")
        setup_data_tab(parent_widget, main_app_instance)
        print("[TEST] After setup_data_tab")
        # Assertions for expected attributes and types
        self.assertIsInstance(main_app_instance.add_local_files_button, QPushButton)
        self.assertIsInstance(main_app_instance.local_files_label, QLabel)
        self.assertIsInstance(main_app_instance.doc_urls_input, QTextEdit)
        self.assertIsInstance(main_app_instance.scraping_mode_selector, QComboBox)
        self.assertIsInstance(main_app_instance.max_pages_spinbox, QSpinBox)
        self.assertIsInstance(main_app_instance.max_depth_spinbox, QSpinBox)
        self.assertIsInstance(main_app_instance.same_domain_checkbox, QCheckBox)
        self.assertIsInstance(main_app_instance.links_per_page_spinbox, QSpinBox)
        self.assertIsInstance(main_app_instance.acquire_doc_button, QPushButton)
        self.assertIsInstance(main_app_instance.knowledge_mode_selector, QComboBox)
        self.assertIsInstance(main_app_instance.preprocess_docs_button, QPushButton)
        self.assertIsInstance(main_app_instance.train_lm_button, QPushButton)
        self.assertIsInstance(main_app_instance.finetune_lm_button, QPushButton)
        self.assertIsInstance(main_app_instance.acquire_github_button, QPushButton)
        print("[TEST] End of test")


if __name__ == '__main__':
    unittest.main()
