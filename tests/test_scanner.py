"""
Unit tests for scanner.py

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
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.backend.services.scanner import (
    scan_code,
    process_file_parallel,
    _get_all_code_files,
    run_linter,
    parse_linter_output,
    get_code_context,
    enhance_code
)
from core.intelligent_analyzer import IntelligentCodeAnalyzer, IssueType


class TestScanner(unittest.TestCase):
    """Test scanner functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = IntelligentCodeAnalyzer()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_all_code_files(self):
        """Test getting all code files from directory."""
        # Create test files
        test_files = [
            "test.py",
            "test.js",
            "test.java",
            "test.txt",  # Should be ignored
            "test.md"    # Should be ignored
        ]
        
        for filename in test_files:
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write("test content")
        
        language_files = _get_all_code_files(self.temp_dir)
        
        self.assertIn('python', language_files)
        self.assertIn('javascript', language_files)
        self.assertIn('java', language_files)
        
        # Check that text and markdown files are not included
        all_files = []
        for files in language_files.values():
            all_files.extend(files)
        
        self.assertNotIn(os.path.join(self.temp_dir, "test.txt"), all_files)
        self.assertNotIn(os.path.join(self.temp_dir, "test.md"), all_files)
    
    def test_parse_linter_output_python(self):
        """Test parsing Python linter output."""
        # Test pylint format
        pylint_output = "test.py:10:1: E001: Test error message"
        result = parse_linter_output(pylint_output, 'python')
        self.assertIsNotNone(result)
        line_num, message = result
        self.assertEqual(line_num, 10)
        self.assertIn("Test error message", message)
    
    def test_parse_linter_output_javascript(self):
        """Test parsing JavaScript linter output."""
        # Test ESLint format
        eslint_output = "test.js:15:5: error: 'undefined_var' is not defined"
        result = parse_linter_output(eslint_output, 'javascript')
        self.assertIsNotNone(result)
        line_num, message = result
        self.assertEqual(line_num, 15)
        self.assertIn("undefined_var", message)
    
    def test_get_code_context(self):
        """Test getting code context around a line."""
        # Create a test file with multiple lines
        test_file = os.path.join(self.temp_dir, "test.py")
        content = """def function1():
    x = 1
    y = 2
    return x + y

def function2():
    a = 10
    b = 20
    return a * b
"""
        with open(test_file, 'w') as f:
            f.write(content)
        
        # Get context around line 3
        context = get_code_context(test_file, 3, context_lines=2)
        self.assertIn("x = 1", context)
        self.assertIn("y = 2", context)
    
    def test_enhance_code(self):
        """Test code enhancement functionality."""
        # Mock the model and tokenizer
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Test enhancement
        result = enhance_code(
            "/test/file.py",
            "x = 1",
            "python",
            "ollama",
            mock_model,
            mock_tokenizer
        )
        
        self.assertIsInstance(result, str)
    
    def test_process_file_parallel(self):
        """Test parallel file processing."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("""
def test_function():
    x = 1
    y = 2
    return x + y
""")
        
        # Mock model and tokenizer
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Test processing
        issues, linter_available = process_file_parallel(
            test_file,
            "python",
            "ollama",
            mock_model,
            mock_tokenizer,
            self.analyzer
        )
        
        self.assertIsInstance(issues, list)
        self.assertIsInstance(linter_available, bool)
    
    def test_scan_code_basic(self):
        """Test basic code scanning functionality."""
        # Create test files
        test_files = [
            ("test1.py", """
def function1():
    x = 1
    return x
"""),
            ("test2.js", """
function function2() {
    var x = 1;
    return x;
}
""")
        ]
        
        for filename, content in test_files:
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
        
        # Mock model and tokenizer
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Test scanning
        results = scan_code(
            self.temp_dir,
            "ollama",
            mock_model,
            mock_tokenizer
        )
        
        self.assertIsInstance(results, list)
    
    def test_scan_code_with_progress_callback(self):
        """Test code scanning with progress callback."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("def test(): pass")
        
        # Mock model and tokenizer
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Track progress calls
        progress_calls = []
        def progress_callback(current, total, message):
            progress_calls.append((current, total, message))
        
        # Test scanning with progress
        results = scan_code(
            self.temp_dir,
            "ollama",
            mock_model,
            mock_tokenizer,
            progress_callback=progress_callback
        )
        
        self.assertIsInstance(results, list)
        # Should have at least one progress call
        self.assertGreater(len(progress_calls), 0)
    
    def test_scan_code_with_log_callback(self):
        """Test code scanning with log callback."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("def test(): pass")
        
        # Mock model and tokenizer
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Track log calls
        log_calls = []
        def log_callback(message):
            log_calls.append(message)
        
        # Test scanning with logging
        results = scan_code(
            self.temp_dir,
            "ollama",
            mock_model,
            mock_tokenizer,
            log_message_callback=log_callback
        )
        
        self.assertIsInstance(results, list)
        # Should have some log messages
        self.assertGreater(len(log_calls), 0)
    
    def test_scan_code_with_cancellation(self):
        """Test code scanning with cancellation callback."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("def test(): pass")
        
        # Mock model and tokenizer
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Cancellation callback that always returns True (cancel)
        def cancellation_callback():
            return True
        
        # Test scanning with cancellation
        results = scan_code(
            self.temp_dir,
            "ollama",
            mock_model,
            mock_tokenizer,
            cancellation_callback=cancellation_callback
        )
        
        # Should return empty results due to cancellation
        self.assertEqual(results, [])
    
    def test_scan_code_large_file_handling(self):
        """Test handling of large files."""
        # Create a large test file
        test_file = os.path.join(self.temp_dir, "large_test.py")
        large_content = "def test():\n" + "    pass\n" * 10000  # Large file
        
        with open(test_file, 'w') as f:
            f.write(large_content)
        
        # Mock model and tokenizer
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Test scanning large file
        results = scan_code(
            self.temp_dir,
            "ollama",
            mock_model,
            mock_tokenizer
        )
        
        self.assertIsInstance(results, list)
    
    def test_scan_code_error_handling(self):
        """Test error handling in code scanning."""
        # Mock model and tokenizer
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Test scanning non-existent directory
        results = scan_code(
            "/nonexistent/directory",
            "ollama",
            mock_model,
            mock_tokenizer
        )
        
        # Should return empty results for non-existent directory
        self.assertEqual(results, [])
    
    def test_issue_type_conversion(self):
        """Test IssueType conversion in scanner."""
        # Create a test file that would generate issues
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("""
def test_function():
    password = "hardcoded_password"  # Should trigger security issue
    for i in range(1000):  # Should trigger performance issue
        print(i)
""")
        
        # Mock model and tokenizer
        mock_model = Mock()
        mock_tokenizer = Mock()
        
        # Test scanning
        results = scan_code(
            self.temp_dir,
            "ollama",
            mock_model,
            mock_tokenizer
        )
        
        self.assertIsInstance(results, list)
        
        # Check that results have proper issue_type values
        for result in results:
            self.assertIn('issue_type', result)
            issue_type = result['issue_type']
            self.assertIsInstance(issue_type, str)
            # Should be a valid IssueType value
            self.assertIn(issue_type, [it.value for it in IssueType])


if __name__ == '__main__':
    unittest.main() 