"""
Unit tests for intelligent_analyzer.py

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

from src.backend.services.intelligent_analyzer import (
    IntelligentCodeAnalyzer, 
    CodeIssue, 
    IssueType,
    SemanticAnalyzer,
    DependencyAnalyzer,
    DataFlowAnalyzer
)


class TestIssueType(unittest.TestCase):
    """Test IssueType enum functionality."""
    
    def test_issue_type_values(self):
        """Test that all IssueType values are valid strings."""
        for issue_type in IssueType:
            self.assertIsInstance(issue_type.value, str)
            self.assertTrue(len(issue_type.value) > 0)
    
    def test_issue_type_from_string(self):
        """Test creating IssueType from string values."""
        # Test valid mappings
        self.assertEqual(IssueType('performance_issue'), IssueType.PERFORMANCE_ISSUE)
        self.assertEqual(IssueType('security_vulnerability'), IssueType.SECURITY_VULNERABILITY)
        self.assertEqual(IssueType('code_quality'), IssueType.CODE_QUALITY)
    
    def test_issue_type_invalid_string(self):
        """Test that invalid strings raise ValueError."""
        with self.assertRaises(ValueError):
            IssueType('invalid_issue_type')


class TestCodeIssue(unittest.TestCase):
    """Test CodeIssue dataclass functionality."""
    
    def test_code_issue_creation(self):
        """Test creating a CodeIssue with valid parameters."""
        issue = CodeIssue(
            file_path="/test/file.py",
            line_number=10,
            issue_type=IssueType.PERFORMANCE_ISSUE,
            severity="medium",
            description="Test issue",
            code_snippet="test code",
            suggestion="Test suggestion"
        )
        
        self.assertEqual(issue.file_path, "/test/file.py")
        self.assertEqual(issue.line_number, 10)
        self.assertEqual(issue.issue_type, IssueType.PERFORMANCE_ISSUE)
        self.assertEqual(issue.severity, "medium")
        self.assertEqual(issue.description, "Test issue")
        self.assertEqual(issue.code_snippet, "test code")
        self.assertEqual(issue.suggestion, "Test suggestion")
    
    def test_code_issue_defaults(self):
        """Test CodeIssue with default parameters."""
        issue = CodeIssue(
            file_path="/test/file.py",
            line_number=10,
            issue_type=IssueType.CODE_QUALITY,
            severity="low",
            description="Test issue"
        )
        
        self.assertEqual(issue.code_snippet, "")
        self.assertEqual(issue.suggestion, "")
        self.assertEqual(issue.context, {})


class TestIntelligentCodeAnalyzer(unittest.TestCase):
    """Test IntelligentCodeAnalyzer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = IntelligentCodeAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_analyzer_initialization(self):
        """Test that analyzer initializes correctly."""
        self.assertIsNotNone(self.analyzer)
        self.assertIsInstance(self.analyzer.cache, dict)
        self.assertIsInstance(self.analyzer.pattern_cache, dict)
    
    def test_analyze_file_with_valid_python(self):
        """Test analyzing a valid Python file."""
        # Create a test Python file
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("""
def test_function():
    x = 1
    y = 2
    return x + y
""")
        
        issues = self.analyzer.analyze_file(test_file, 'python')
        self.assertIsInstance(issues, list)
    
    def test_analyze_file_with_syntax_error(self):
        """Test analyzing a Python file with syntax errors."""
        # Create a test Python file with syntax error
        test_file = os.path.join(self.temp_dir, "syntax_error.py")
        with open(test_file, 'w') as f:
            f.write("""
def test_function():
    x = 1
    y = 2
    return x + y  # Missing closing parenthesis
""")
        
        issues = self.analyzer.analyze_file(test_file, 'python')
        self.assertIsInstance(issues, list)
    
    def test_analyze_file_with_nonexistent_file(self):
        """Test analyzing a nonexistent file."""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.py")
        issues = self.analyzer.analyze_file(nonexistent_file, 'python')
        self.assertEqual(issues, [])
    
    def test_generate_summary(self):
        """Test summary generation."""
        # Create test issues
        issues = [
            CodeIssue(
                file_path="/test/file1.py",
                line_number=10,
                issue_type=IssueType.PERFORMANCE_ISSUE,
                severity="medium",
                description="Performance issue 1"
            ),
            CodeIssue(
                file_path="/test/file2.py",
                line_number=20,
                issue_type=IssueType.SECURITY_VULNERABILITY,
                severity="high",
                description="Security issue 1"
            ),
            CodeIssue(
                file_path="/test/file3.py",
                line_number=30,
                issue_type=IssueType.PERFORMANCE_ISSUE,
                severity="low",
                description="Performance issue 2"
            )
        ]
        
        summary = self.analyzer.generate_summary(issues)
        
        self.assertIn('total_issues', summary)
        self.assertIn('by_type', summary)
        self.assertIn('by_severity', summary)
        self.assertIn('by_language', summary)
        self.assertIn('critical_issues', summary)
        self.assertIn('recommendations', summary)
        
        self.assertEqual(summary['total_issues'], 3)
        self.assertEqual(summary['by_type']['performance_issue'], 2)
        self.assertEqual(summary['by_type']['security_vulnerability'], 1)
        self.assertEqual(summary['by_severity']['medium'], 1)
        self.assertEqual(summary['by_severity']['high'], 1)
        self.assertEqual(summary['by_severity']['low'], 1)
    
    def test_analyze_content_intelligently(self):
        """Test intelligent content analysis."""
        content = """
def bad_function():
    password = "hardcoded_password"  # Security issue
    for i in range(1000):  # Performance issue
        print(i)
"""
        
        issues = self.analyzer._analyze_content_intelligently(content, "/test/file.py", "python")
        self.assertIsInstance(issues, list)
    
    def test_convert_linter_issue_dict(self):
        """Test converting linter issue from dict format."""
        linter_issue = {
            'line': 10,
            'message': 'Test linter message',
            'code': 'E001',
            'linter': 'pylint'
        }
        
        issue = self.analyzer._convert_linter_issue(linter_issue, "/test/file.py", "python")
        self.assertIsInstance(issue, CodeIssue)
        self.assertEqual(issue.line_number, 10)
        self.assertEqual(issue.description, 'Test linter message')
    
    def test_convert_linter_issue_string(self):
        """Test converting linter issue from string format."""
        linter_issue = "10:1: E001: Test linter message"
        
        issue = self.analyzer._convert_linter_issue(linter_issue, "/test/file.py", "python")
        self.assertIsInstance(issue, CodeIssue)
    
    def test_convert_linter_issue_invalid(self):
        """Test converting invalid linter issue."""
        linter_issue = None
        
        issue = self.analyzer._convert_linter_issue(linter_issue, "/test/file.py", "python")
        self.assertIsInstance(issue, CodeIssue)
        self.assertEqual(issue.line_number, 1)


class TestSemanticAnalyzer(unittest.TestCase):
    """Test SemanticAnalyzer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = SemanticAnalyzer()
    
    def test_analyze_python_semantics(self):
        """Test Python semantic analysis."""
        content = """
def test_function():
    eval("print('hello')")  # Security issue
    time.sleep(1)  # Performance issue
    x = None
    if x == None:  # Semantic issue
        pass
"""
        
        issues = self.analyzer._analyze_python_semantics("/test/file.py", content)
        self.assertIsInstance(issues, list)
    
    def test_analyze_js_semantics(self):
        """Test JavaScript semantic analysis."""
        content = """
function testFunction() {
    var x = null;
    if (x == null) {  // Semantic issue
        console.log("null");
    }
}
"""
        
        issues = self.analyzer._analyze_js_semantics("/test/file.js", content)
        self.assertIsInstance(issues, list)
    
    def test_analyze_function_call_security(self):
        """Test function call security analysis."""
        content = """
def test_function():
    eval("print('hello')")
    exec("print('world')")
    input("Enter password: ")
"""
        
        issues = self.analyzer._analyze_python_semantics("/test/file.py", content)
        security_issues = [i for i in issues if i.issue_type == IssueType.SECURITY_VULNERABILITY]
        self.assertGreater(len(security_issues), 0)
    
    def test_analyze_function_call_performance(self):
        """Test function call performance analysis."""
        content = """
import time

def test_function():
    time.sleep(1)
    import time
    time.sleep(0.5)
"""
        
        issues = self.analyzer._analyze_python_semantics("/test/file.py", content)
        performance_issues = [i for i in issues if i.issue_type == IssueType.PERFORMANCE_ISSUE]
        self.assertGreater(len(performance_issues), 0)


class TestDataFlowAnalyzer(unittest.TestCase):
    """Test DataFlowAnalyzer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = DataFlowAnalyzer()
    
    def test_analyze_python_data_flow(self):
        """Test Python data flow analysis."""
        content = """
def test_function():
    x = 1
    y = 2
    z = x + y
    print(z)
    unused_var = 10  # Unused variable
"""
        
        issues = self.analyzer._analyze_python_data_flow("/test/file.py", content)
        self.assertIsInstance(issues, list)
    
    def test_analyze_js_data_flow(self):
        """Test JavaScript data flow analysis."""
        content = """
function testFunction() {
    var x = 1;
    let y = 2;
    const z = x + y;
    console.log(z);
    var undefined_var;  // Potentially undefined
}
"""
        
        issues = self.analyzer._analyze_js_data_flow("/test/file.js", content)
        self.assertIsInstance(issues, list)


class TestDependencyAnalyzer(unittest.TestCase):
    """Test DependencyAnalyzer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = DependencyAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_analyze_dependencies(self):
        """Test dependency analysis."""
        # Create test project structure
        test_file = os.path.join(self.temp_dir, "test.py")
        with open(test_file, 'w') as f:
            f.write("import os\nimport sys\n")
        
        issues = self.analyzer.analyze_dependencies(self.temp_dir)
        self.assertIsInstance(issues, list)


if __name__ == '__main__':
    unittest.main() 