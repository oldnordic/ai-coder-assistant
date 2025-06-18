import unittest
from src.frontend.ui.markdown_viewer import MarkdownViewerDialog
from PyQt6.QtWidgets import QApplication
import sys

class TestMarkdownViewerBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    def test_markdown_viewer_uses_backend_constants(self):
        # Should not raise
        dialog = MarkdownViewerDialog("# Test Report\nSome content.")
        self.assertIsNotNone(dialog)

if __name__ == '__main__':
    unittest.main() 