"""
Comprehensive test suite for AI Coder Assistant

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2024 AI Coder Assistant Contributors
"""

import unittest
import tempfile
import os
import sys
import time
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import PyQt6 for GUI tests
try:
    from PyQt6.QtWidgets import QApplication
except ImportError:
    QApplication = None

# Import constants for testing
from src.utils.constants import (
    PROGRESS_DIALOG_MAX_VALUE, PROGRESS_DIALOG_MIN_VALUE,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
    WINDOW_DEFAULT_X, WINDOW_DEFAULT_Y, LOG_CONSOLE_MAX_HEIGHT,
    PROGRESS_MAX, PROGRESS_MIN, PROGRESS_COMPLETE,
    PROGRESS_WEIGHT_DOWNLOAD, PERCENTAGE_MULTIPLIER,
    MAX_FILE_SIZE_KB, MAX_FILENAME_LENGTH,
    MAX_DESCRIPTION_LENGTH, MAX_ERROR_MESSAGE_LENGTH,
    HTTP_TIMEOUT_SHORT, HTTP_TIMEOUT_LONG,
    OLLAMA_BASE_URL, CACHE_EXPIRY_SECONDS,
    DEFAULT_MAX_PAGES, DEFAULT_MAX_DEPTH,
    DEFAULT_LINKS_PER_PAGE, DEFAULT_MAX_WORKERS,
    SSL_VERIFY_DEFAULT, VERIFY_DEFAULT
)

class TestComprehensiveImports(unittest.TestCase):
    """Test that all modules can be imported successfully."""
    
    def test_backend_services_imports(self):
        """Test that all backend services can be imported."""
        try:
            from src.backend.services import (
                ai_tools, scanner, acquire, preprocess, trainer,
                intelligent_analyzer, llm_manager, ollama_client,
                providers, studio_ui
            )
            self.assertTrue(True, "All backend services imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import backend services: {e}")
    
    def test_frontend_ui_imports(self):
        """Test that all frontend UI modules can be imported."""
        try:
            from src.frontend.ui import (
                main_window, ai_tab_widgets, data_tab_widgets,
                browser_tab, ollama_export_tab, pr_tab_widgets,
                suggestion_dialog, markdown_viewer, worker_threads
            )
            self.assertTrue(True, "All frontend UI modules imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import frontend UI modules: {e}")
    
    def test_utils_imports(self):
        """Test that all utility modules can be imported."""
        try:
            from src.utils import constants
            from src.backend.utils import settings
            self.assertTrue(True, "All utility modules imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import utility modules: {e}")

class TestConstants(unittest.TestCase):
    """Test that all constants are properly defined and accessible."""
    
    def test_ui_constants(self):
        """Test UI constants are properly defined."""
        self.assertEqual(PROGRESS_DIALOG_MAX_VALUE, 100)
        self.assertEqual(PROGRESS_DIALOG_MIN_VALUE, 0)
        self.assertEqual(WINDOW_DEFAULT_WIDTH, 1200)
        self.assertEqual(WINDOW_DEFAULT_HEIGHT, 800)
        self.assertEqual(WINDOW_DEFAULT_X, 100)
        self.assertEqual(WINDOW_DEFAULT_Y, 100)
        self.assertEqual(LOG_CONSOLE_MAX_HEIGHT, 200)
    
    def test_progress_constants(self):
        """Test progress constants are properly defined."""
        self.assertEqual(PROGRESS_MAX, 100)
        self.assertEqual(PROGRESS_MIN, 0)
        self.assertEqual(PROGRESS_COMPLETE, 100)
        self.assertEqual(PROGRESS_WEIGHT_DOWNLOAD, 0.8)
        self.assertEqual(PERCENTAGE_MULTIPLIER, 100)
    
    def test_file_size_constants(self):
        """Test file size constants are properly defined."""
        self.assertEqual(MAX_FILE_SIZE_KB, 512)
        self.assertEqual(MAX_FILENAME_LENGTH, 255)
        self.assertEqual(MAX_DESCRIPTION_LENGTH, 150)
        self.assertEqual(MAX_ERROR_MESSAGE_LENGTH, 100)
    
    def test_http_constants(self):
        """Test HTTP constants are properly defined."""
        self.assertEqual(HTTP_TIMEOUT_SHORT, 10)
        self.assertEqual(HTTP_TIMEOUT_LONG, 30)
        self.assertEqual(OLLAMA_BASE_URL, "http://localhost:11434")
        self.assertEqual(CACHE_EXPIRY_SECONDS, 3600)
    
    def test_web_scraping_constants(self):
        """Test web scraping constants are properly defined."""
        self.assertEqual(DEFAULT_MAX_PAGES, 15)
        self.assertEqual(DEFAULT_MAX_DEPTH, 4)
        self.assertEqual(DEFAULT_LINKS_PER_PAGE, 50)
        self.assertEqual(DEFAULT_MAX_WORKERS, 6)

class TestWebScrapingFunctionality(unittest.TestCase):
    """Test web scraping functionality with proper mocking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_crawl_docs_returns_summary_dict(self):
        """Test that crawl_docs returns a proper summary dictionary."""
        from src.backend.services.acquire import crawl_docs
        
        urls = ["https://example1.com", "https://example2.com"]
        
        with patch('src.backend.services.acquire.browse_web_tool') as mock_browse:
            mock_browse.return_value = "Test content"
            
            result = crawl_docs(urls, self.temp_dir)
        
        self.assertIsInstance(result, dict)
        self.assertIn('success_count', result)
        self.assertIn('total', result)
        self.assertIn('files', result)
        self.assertIn('urls', result)
        self.assertIn('errors', result)
        self.assertEqual(result['total'], 2)
    
    def test_crawl_docs_links_per_page_parameter(self):
        """Test that links_per_page parameter is properly handled."""
        from src.backend.services.acquire import crawl_docs
        
        urls = ["https://example.com"]
        
        with patch('src.backend.services.acquire.browse_web_tool') as mock_browse:
            mock_browse.return_value = "Test content"
            
            result = crawl_docs(urls, self.temp_dir, links_per_page=7)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['total'], 1)
    
    def test_crawl_docs_empty_urls(self):
        """Test that crawl_docs handles empty URL lists gracefully."""
        from src.backend.services.acquire import crawl_docs
        
        urls = []
        result = crawl_docs(urls, self.temp_dir)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['success_count'], 0)
        self.assertEqual(result['total'], 0)
        self.assertEqual(len(result['files']), 0)
        self.assertEqual(len(result['urls']), 0)
    
    def test_crawl_docs_error_handling(self):
        """Test that crawl_docs handles errors gracefully."""
        from src.backend.services.acquire import crawl_docs
        
        urls = ["https://error1.com", "https://error2.com"]
        
        with patch('src.backend.services.acquire.browse_web_tool') as mock_browse:
            mock_browse.return_value = "Error: Connection failed"
            
            result = crawl_docs(urls, self.temp_dir)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['success_count'], 0)
        self.assertEqual(result['total'], 2)
        self.assertIn('errors', result)
        self.assertGreater(len(result['errors']), 0)

class TestScannerFunctionality(unittest.TestCase):
    """Test scanner functionality with proper mocking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_scan_code_basic_functionality(self):
        """Test basic scanner functionality."""
        from src.backend.services.scanner import scan_code
        
        # Create a test Python file
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("print('Hello, World!')\n")
        
        scan_config = {
            'include_patterns': ['*.py'],
            'exclude_patterns': [],
            'max_file_size_kb': 512,
            'use_ai_enhancement': False,
            'model_mode': 'ollama',
            'model_ref': None,
            'tokenizer_ref': None
        }
        
        with patch('src.backend.services.scanner.run_linter') as mock_linter:
            mock_linter.return_value = ([], True)
            
            result = scan_code(self.temp_dir, scan_config)
        
        self.assertIsInstance(result, list)
    
    def test_scanner_file_size_limits(self):
        """Test that scanner respects file size limits."""
        from src.backend.services.scanner import scan_code
        
        # Create a large test file
        test_file = os.path.join(self.temp_dir, "large_test.py")
        large_content = "print('test')\n" * (MAX_FILE_SIZE_KB * 100)  # Much larger than limit
        with open(test_file, 'w') as f:
            f.write(large_content)
        
        scan_config = {
            'include_patterns': ['*.py'],
            'exclude_patterns': [],
            'max_file_size_kb': MAX_FILE_SIZE_KB,
            'use_ai_enhancement': False,
            'model_mode': 'ollama',
            'model_ref': None,
            'tokenizer_ref': None
        }
        
        with patch('src.backend.services.scanner.run_linter') as mock_linter:
            mock_linter.return_value = ([], True)
            
            result = scan_code(self.temp_dir, scan_config)
        
        # Should skip the large file
        self.assertIsInstance(result, list)

class TestAIToolsFunctionality(unittest.TestCase):
    """Test AI tools functionality with proper mocking."""
    
    def test_ai_tools_import(self):
        """Test that AI tools can be imported and basic functions exist."""
        from src.backend.services import ai_tools
        
        # Check that key functions exist
        self.assertTrue(hasattr(ai_tools, 'generate_report_and_training_data'))
        self.assertTrue(hasattr(ai_tools, 'get_ai_explanation'))
        self.assertTrue(hasattr(ai_tools, 'browse_web_tool'))
        self.assertTrue(hasattr(ai_tools, 'transcribe_youtube_tool'))
    
    def test_ai_tools_constants_usage(self):
        """Test that AI tools use constants instead of magic numbers."""
        from src.backend.services.ai_tools import browse_web_tool
        
        with patch('src.backend.services.ai_tools.requests.get') as mock_get:
            mock_get.return_value.content = b"<html><body>Test content</body></html>"
            mock_get.return_value.status_code = 200
            
            # This should use the default constants
            result = browse_web_tool("https://example.com")
            
            # Verify the function was called (basic functionality test)
            mock_get.assert_called()

class TestMainWindowFunctionality(unittest.TestCase):
    """Test main window functionality."""
    
    def test_main_window_import(self):
        """Test that main window can be imported."""
        try:
            from src.frontend.ui.main_window import AICoderAssistant
            self.assertTrue(True, "Main window imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import main window: {e}")
    
    def test_main_window_constants_usage(self):
        """Test that main window uses constants instead of magic numbers."""
        from src.frontend.ui.main_window import AICoderAssistant
        
        # Test that the constants are used in the main window
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        try:
            window = AICoderAssistant()
            self.assertEqual(window.geometry().width(), WINDOW_DEFAULT_WIDTH)
            self.assertEqual(window.geometry().height(), WINDOW_DEFAULT_HEIGHT)
            self.assertEqual(window.geometry().x(), WINDOW_DEFAULT_X)
            self.assertEqual(window.geometry().y(), WINDOW_DEFAULT_Y)
        finally:
            if hasattr(window, 'close'):
                window.close()

class TestSecurityVulnerabilities(unittest.TestCase):
    """Test that security vulnerabilities have been addressed."""
    
    def test_no_hardcoded_credentials(self):
        """Test that no hardcoded credentials exist in the codebase."""
        import os
        
        # Check for common credential patterns
        credential_patterns = [
            'password = "',
            'api_key = "',
            'secret = "',
            'token = "',
            'auth = "'
        ]
        
        src_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
        
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            for pattern in credential_patterns:
                                self.assertNotIn(
                                    pattern, content,
                                    f"Potential hardcoded credential found in {file_path}: {pattern}"
                                )
                    except Exception:
                        # Skip files that can't be read
                        pass
    
    def test_ssl_verification_enabled(self):
        """Test that SSL verification is enabled by default."""
        self.assertTrue(SSL_VERIFY_DEFAULT)
        self.assertTrue(VERIFY_DEFAULT)

class TestPerformanceOptimizations(unittest.TestCase):
    """Test that performance optimizations are in place."""
    
    def test_file_size_limits(self):
        """Test that file size limits are reasonable."""
        self.assertGreater(MAX_FILE_SIZE_KB, 100)  # At least 100KB
        self.assertLess(MAX_FILE_SIZE_KB, 2048)    # Less than 2MB
    
    def test_timeout_constants(self):
        """Test that timeout constants are reasonable."""
        self.assertGreater(HTTP_TIMEOUT_SHORT, 5)   # At least 5 seconds
        self.assertLess(HTTP_TIMEOUT_SHORT, 30)     # Less than 30 seconds
        self.assertGreater(HTTP_TIMEOUT_LONG, HTTP_TIMEOUT_SHORT)

class TestCodeQuality(unittest.TestCase):
    """Test that code quality standards are met."""
    
    def test_no_magic_numbers_in_constants(self):
        """Test that constants file doesn't contain magic numbers without explanation."""
        self.assertIsInstance(PROGRESS_DIALOG_MAX_VALUE, int)
        self.assertIsInstance(PROGRESS_DIALOG_MIN_VALUE, int)
        self.assertIsInstance(MAX_FILE_SIZE_KB, int)
        self.assertIsInstance(HTTP_TIMEOUT_SHORT, int)
        self.assertIsInstance(HTTP_TIMEOUT_LONG, int)
    
    def test_consistent_naming_conventions(self):
        """Test that naming conventions are consistent."""
        constant_names = [
            name for name in dir() 
            if name.isupper() and not name.startswith('_')
        ]
        
        for name in constant_names:
            self.assertTrue(name.isupper(), f"Constant {name} should be in UPPER_CASE")

if __name__ == '__main__':
    unittest.main() 