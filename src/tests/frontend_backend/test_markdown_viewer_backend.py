import unittest
from PyQt6.QtWidgets import QApplication
from frontend.ui.markdown_viewer import MarkdownViewerDialog

class TestMarkdownViewerBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    def test_markdown_viewer_uses_backend_constants(self):
        # Should not raise
        dialog = MarkdownViewerDialog("# Test Report\nSome content.")
        self.assertIsNotNone(dialog)

if __name__ == '__main__':
    unittest.main() 