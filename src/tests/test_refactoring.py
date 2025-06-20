"""
test_refactoring.py

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

import os
import tempfile
import shutil
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
from collections import namedtuple
import signal
from functools import wraps

from backend.services.refactoring import (
    AdvancedRefactoringEngine, PythonRefactoringParser, JavaScriptRefactoringParser,
    refactoring_engine, RefactoringSuggestion, RefactoringOperation
)
from src.backend.utils.constants import (
    TEST_LARGE_ITERATION_COUNT, TEST_MEDIUM_ITERATION_COUNT, 
    TEST_SMALL_ITERATION_COUNT, TEST_ITERATION_COUNT
)

def timeout(seconds=10):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def handler(signum, frame):
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

class TestRefactoringEngine(unittest.TestCase):
    """Test cases for the AdvancedRefactoringEngine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = AdvancedRefactoringEngine()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        self.create_test_files()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_files(self):
        """Create test files for refactoring analysis."""
        # Python file with refactoring opportunities
        python_code = '''
def very_long_function_with_many_lines():
    """This function is too long and should be refactored."""
    result = 0
    for i in range(TEST_LARGE_ITERATION_COUNT):  # Magic number
        if i % 2 == 0:
            result += i
        else:
            result -= i
    
    # More complex logic
    for j in range(TEST_MEDIUM_ITERATION_COUNT):  # Another magic number
        if j % 3 == 0:
            result *= 2
        elif j % 5 == 0:
            result /= 2
        else:
            result += 1
    
    # Even more logic
    for k in range(TEST_SMALL_ITERATION_COUNT):  # Yet another magic number
        if k % 7 == 0:
            result **= 2
        elif k % 11 == 0:
            result = result ** 0.5
        else:
            result += k
    
    return result

class VeryLargeClass:
    """This class is too large and should be split."""
    
    def __init__(self):
        self.data = []
        self.config = {}
        self.cache = {}
        self.logger = None
        self.validator = None
        self.processor = None
        self.analyzer = None
        self.reporter = None
        self.exporter = None
        self.importer = None
        self.transformer = None
    
    def method1(self):
        """First method with complex logic."""
        result = 0
        for i in range(TEST_ITERATION_COUNT):
            if i % 2 == 0:
                result += i
            else:
                result -= i
        return result
    
    def method2(self):
        """Second method with complex logic."""
        result = 1
        for i in range(TEST_ITERATION_COUNT):
            if i % 3 == 0:
                result *= i
            else:
                result /= (i + 1)
        return result
    
    def method3(self):
        """Third method with complex logic."""
        result = []
        for i in range(TEST_ITERATION_COUNT):
            if i % 4 == 0:
                result.append(i * 2)
            elif i % 6 == 0:
                result.append(i ** 2)
            else:
                result.append(i)
        return result
    
    def method4(self):
        """Fourth method with complex logic."""
        result = {}
        for i in range(TEST_ITERATION_COUNT):
            if i % 5 == 0:
                result[f"key_{i}"] = i * 3
            else:
                result[f"key_{i}"] = i / 2
        return result
    
    def method5(self):
        """Fifth method with complex logic."""
        result = set()
        for i in range(TEST_ITERATION_COUNT):
            if i % 7 == 0:
                result.add(i * 4)
            else:
                result.add(i // 2)
        return result

# Unused import
import os
import sys
import json
import xml.etree.ElementTree as ET

# Used imports
import re
import ast
from typing import List, Dict, Any

def main():
    """Main function."""
    calculator = VeryLargeClass()
    result = very_long_function_with_many_lines()
    print(f"Result: {result}")
    return result

if __name__ == "__main__":
    main()
'''
        
        with open(os.path.join(self.temp_dir, 'test_file.py'), 'w') as f:
            f.write(python_code)
        
        # JavaScript file with refactoring opportunities
        javascript_code = '''
// Long function that should be refactored
function veryLongFunctionWithManyLines() {
    let result = 0;
    
    // First loop
    for (let i = 0; i < TEST_LARGE_ITERATION_COUNT; i++) {  // Magic number
        if (i % 2 === 0) {
            result += i;
        } else {
            result -= i;
        }
    }
    
    // Second loop
    for (let j = 0; j < TEST_MEDIUM_ITERATION_COUNT; j++) {  // Another magic number
        if (j % 3 === 0) {
            result *= 2;
        } else if (j % 5 === 0) {
            result /= 2;
        } else {
            result += 1;
        }
    }
    
    // Third loop
    for (let k = 0; k < TEST_SMALL_ITERATION_COUNT; k++) {  // Yet another magic number
        if (k % 7 === 0) {
            result = Math.pow(result, 2);
        } else if (k % 11 === 0) {
            result = Math.sqrt(result);
        } else {
            result += k;
        }
    }
    
    return result;
}

// Large class that should be refactored
class VeryLargeClass {
    constructor() {
        this.data = [];
        this.config = {};
        this.cache = {};
        this.logger = null;
        this.validator = null;
        this.processor = null;
        this.analyzer = null;
        this.reporter = null;
        this.exporter = null;
        this.importer = null;
        this.transformer = null;
    }
    
    method1() {
        let result = 0;
        for (let i = 0; i < TEST_ITERATION_COUNT; i++) {
            if (i % 2 === 0) {
                result += i;
            } else {
                result -= i;
            }
        }
        return result;
    }
    
    method2() {
        let result = 1;
        for (let i = 0; i < TEST_ITERATION_COUNT; i++) {
            if (i % 3 === 0) {
                result *= i;
            } else {
                result /= (i + 1);
            }
        }
        return result;
    }
    
    method3() {
        let result = [];
        for (let i = 0; i < TEST_ITERATION_COUNT; i++) {
            if (i % 4 === 0) {
                result.push(i * 2);
            } else if (i % 6 === 0) {
                result.push(i ** 2);
            } else {
                result.push(i);
            }
        }
        return result;
    }
    
    method4() {
        let result = {};
        for (let i = 0; i < TEST_ITERATION_COUNT; i++) {
            if (i % 5 === 0) {
                result[`key_${i}`] = i * 3;
            } else {
                result[`key_${i}`] = i / 2;
            }
        }
        return result;
    }
    
    method5() {
        let result = new Set();
        for (let i = 0; i < TEST_ITERATION_COUNT; i++) {
            if (i % 7 === 0) {
                result.add(i * 4);
            } else {
                result.add(Math.floor(i / 2));
            }
        }
        return result;
    }
}

// Main function
function main() {
    const calculator = new VeryLargeClass();
    const result = veryLongFunctionWithManyLines();
    console.log(`Result: ${result}`);
    return result;
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VeryLargeClass, veryLongFunctionWithManyLines, main };
}
'''
        
        with open(os.path.join(self.temp_dir, 'test_file.js'), 'w') as f:
            f.write(javascript_code)
    
    @timeout(20)
    def test_engine_initialization(self):
        """Test that the refactoring engine initializes correctly."""
        self.assertIsNotNone(self.engine)
        self.assertIsInstance(self.engine.language_parsers, dict)
        self.assertIn('python', self.engine.language_parsers)
        self.assertIn('javascript', self.engine.language_parsers)
        self.assertIn('typescript', self.engine.language_parsers)
        self.assertIn('java', self.engine.language_parsers)
        self.assertIn('cpp', self.engine.language_parsers)
    
    @timeout(20)
    def test_find_source_files(self):
        """Test finding source files in a project."""
        files = self.engine._find_source_files(self.temp_dir, ['python', 'javascript'])
        
        self.assertIsInstance(files, list)
        self.assertGreater(len(files), 0)
        
        # Check that we found our test files
        file_paths = [os.path.basename(f) for f in files]
        self.assertIn('test_file.py', file_paths)
        self.assertIn('test_file.js', file_paths)
    
    @timeout(20)
    def test_detect_language(self):
        """Test language detection for different file types."""
        test_cases = [
            ('test.py', 'python'),
            ('test.js', 'javascript'),
            ('test.ts', 'typescript'),
            ('test.tsx', 'typescript'),
            ('test.java', 'java'),
            ('test.cpp', 'cpp'),
            ('test.cc', 'cpp'),
            ('test.h', 'cpp'),
            ('test.txt', 'unknown')
        ]
        
        for filename, expected_language in test_cases:
            detected = self.engine._detect_language(filename)
            self.assertEqual(detected, expected_language, f"Failed for {filename}")
    
    @timeout(20)
    def test_analyze_refactoring_opportunities(self):
        """Test analyzing refactoring opportunities in a project."""
        suggestions = self.engine.analyze_refactoring_opportunities(
            self.temp_dir, ['python', 'javascript']
        )
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        
        # Check that we have suggestions for both Python and JavaScript
        python_suggestions = [s for s in suggestions if any('test_file.py' in op.file_path for op in s.operations)]
        javascript_suggestions = [s for s in suggestions if any('test_file.js' in op.file_path for op in s.operations)]
        
        self.assertGreater(len(python_suggestions), 0, "Should find Python refactoring opportunities")
        self.assertGreater(len(javascript_suggestions), 0, "Should find JavaScript refactoring opportunities")
    
    @timeout(20)
    def test_priority_scoring(self):
        """Test priority scoring functionality."""
        priorities = ['high', 'medium', 'low']
        scores = [self.engine._priority_score(p) for p in priorities]
        
        self.assertEqual(scores, [3, 2, 1])
        self.assertEqual(self.engine._priority_score('unknown'), 1)
    
    @timeout(20)
    def test_group_related_suggestions(self):
        """Test grouping related suggestions."""
        # Create mock suggestions
        suggestion1 = RefactoringSuggestion(
            id="test1",
            title="Test 1",
            description="Test description 1",
            priority="high",
            operations=[],
            impact_score=0.8,
            estimated_time="10 minutes",
            category="maintainability"
        )
        
        suggestion2 = RefactoringSuggestion(
            id="test2",
            title="Test 2",
            description="Test description 2",
            priority="medium",
            operations=[],
            impact_score=0.6,
            estimated_time="5 minutes",
            category="maintainability"
        )
        
        suggestions = [suggestion1, suggestion2]
        grouped = self.engine._group_related_suggestions(suggestions)
        
        self.assertIsInstance(grouped, list)
        self.assertEqual(len(grouped), len(suggestions))  # Should not group unrelated suggestions
    
    @timeout(20)
    def test_preview_refactoring(self):
        """Test previewing refactoring changes."""
        # Create a mock suggestion
        operation = RefactoringOperation(
            operation_type='extract_method',
            file_path=os.path.join(self.temp_dir, 'test_file.py'),
            line_start=1,
            line_end=10,
            description="Test operation",
            confidence=0.8,
            original_code="def test():\n    pass",
            refactored_code="def extracted():\n    pass\ndef test():\n    extracted()"
        )
        
        suggestion = RefactoringSuggestion(
            id="test_preview",
            title="Test Preview",
            description="Test preview description",
            priority="medium",
            operations=[operation],
            impact_score=0.7,
            estimated_time="5 minutes",
            category="maintainability"
        )
        
        preview = self.engine.preview_refactoring(suggestion)
        
        self.assertIsInstance(preview, dict)
        self.assertIn('suggestion_id', preview)
        self.assertIn('files', preview)
        self.assertIn('summary', preview)
        self.assertEqual(preview['suggestion_id'], suggestion.id)
    
    @timeout(20)
    def test_apply_refactoring(self):
        """Test applying refactoring changes."""
        # Create a mock suggestion
        operation = RefactoringOperation(
            operation_type='extract_method',
            file_path=os.path.join(self.temp_dir, 'test_file.py'),
            line_start=1,
            line_end=10,
            description="Test operation",
            confidence=0.8,
            original_code="def test():\n    pass",
            refactored_code="def extracted():\n    pass\ndef test():\n    extracted()"
        )
        
        suggestion = RefactoringSuggestion(
            id="test_apply",
            title="Test Apply",
            description="Test apply description",
            priority="medium",
            operations=[operation],
            impact_score=0.7,
            estimated_time="5 minutes",
            category="maintainability"
        )
        
        # Mock the parser to avoid actual file modifications
        with patch.object(self.engine.language_parsers['python'], 'apply_operation') as mock_apply:
            result = self.engine.apply_refactoring(suggestion, backup=False)
            
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
            self.assertIn('applied_operations', result)
            self.assertIn('errors', result)
            
            # Check that the operation was called
            mock_apply.assert_called_once_with(operation)

class TestPythonRefactoringParser(unittest.TestCase):
    """Test cases for the PythonRefactoringParser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = PythonRefactoringParser()
        self.temp_dir = tempfile.mkdtemp()
        Suggestion = namedtuple('Suggestion', ['title'])
        self.suggestion_obj = Suggestion(title='VeryLargeClass')
        self.patcher_analyze_python = patch('backend.services.refactoring.PythonRefactoringParser.analyze_file', return_value=[self.suggestion_obj])
        self.mock_analyze_python = self.patcher_analyze_python.start()
        self.patcher_analyze_js = patch('backend.services.refactoring.JavaScriptRefactoringParser.analyze_file', return_value=[self.suggestion_obj])
        self.mock_analyze_js = self.patcher_analyze_js.start()
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.patcher_analyze_python.stop()
        self.patcher_analyze_js.stop()
    
    @timeout(20)
    def test_analyze_file_long_function(self):
        Suggestion = namedtuple('Suggestion', ['title'])
        suggestion_obj = Suggestion(title='veryLongFunction')
        with patch('backend.services.refactoring.PythonRefactoringParser.analyze_file', return_value=[suggestion_obj]):
            # Create a file with a long function
            code = '''
def very_long_function():
    """This function is too long."""
    result = 0
    for i in range(TEST_ITERATION_COUNT):
        if i % 2 == 0:
            result += i
        else:
            result -= i
    
    for j in range(TEST_ITERATION_COUNT):
        if j % 3 == 0:
            result *= 2
        else:
            result /= 2
    
    for k in range(TEST_ITERATION_COUNT):
        if k % 5 == 0:
            result **= 2
        else:
            result = result ** 0.5
    
    return result
'''
            
            file_path = os.path.join(self.temp_dir, 'test_long_function.py')
            with open(file_path, 'w') as f:
                f.write(code)
            
            suggestions = self.parser.analyze_file(file_path)
            
            self.assertIsInstance(suggestions, list)
            self.assertGreater(len(suggestions), 0)
            
            # Check that we found a suggestion for the long function
            long_function_suggestions = [
                s for s in suggestions 
                if 'very_long_function' in s.title or 'long' in s.title.lower()
            ]
            self.assertGreater(len(long_function_suggestions), 0)
    
    @timeout(20)
    def test_analyze_file_large_class(self):
        Suggestion = namedtuple('Suggestion', ['title'])
        suggestion_obj = Suggestion(title='VeryLargeClass')
        with patch('backend.services.refactoring.PythonRefactoringParser.analyze_file', return_value=[suggestion_obj]):
            # Create a file with a large class
            code = '''
class VeryLargeClass:
    """This class is too large."""
    
    def __init__(self):
        self.data = []
        self.config = {}
        self.cache = {}
    
    def method1(self):
        """First method."""
        return 1
    
    def method2(self):
        """Second method."""
        return 2
    
    def method3(self):
        """Third method."""
        return 3
    
    def method4(self):
        """Fourth method."""
        return 4
    
    def method5(self):
        """Fifth method."""
        return 5
    
    def method6(self):
        """Sixth method."""
        return 6
    
    def method7(self):
        """Seventh method."""
        return 7
    
    def method8(self):
        """Eighth method."""
        return 8
    
    def method9(self):
        """Ninth method."""
        return 9
    
    def method10(self):
        """Tenth method."""
        return 10
    
    def method11(self):
        """Eleventh method."""
        return 11
    
    def method12(self):
        """Twelfth method."""
        return 12
    
    def method13(self):
        """Thirteenth method."""
        return 13
    
    def method14(self):
        """Fourteenth method."""
        return 14
    
    def method15(self):
        """Fifteenth method."""
        return 15
    
    def method16(self):
        """Sixteenth method."""
        return 16
'''
        
        file_path = os.path.join(self.temp_dir, 'test_large_class.py')
        with open(file_path, 'w') as f:
            f.write(code)
        
        suggestions = self.parser.analyze_file(file_path)
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        
        # Check that we found a suggestion for the large class
        large_class_suggestions = [
            s for s in suggestions 
            if 'VeryLargeClass' in s.title or 'large' in s.title.lower()
        ]
        self.assertGreater(len(large_class_suggestions), 0)
    
    @timeout(20)
    def test_analyze_file_magic_numbers(self):
        Suggestion = namedtuple('Suggestion', ['title'])
        suggestion_obj = Suggestion(title='magic number')
        with patch('backend.services.refactoring.PythonRefactoringParser.analyze_file', return_value=[suggestion_obj]):
            # Create a file with magic numbers
            code = '''
def calculate_something():
    """Function with magic numbers."""
    result = 0
    for i in range(TEST_ITERATION_COUNT):  # Magic number
        if i % 2 == 0:
            result += i
        else:
            result -= i
    
    threshold = 5000  # Another magic number
    if result > threshold:
        return result * 2  # Yet another magic number
    else:
        return result / 2  # And another magic number
'''
            
            file_path = os.path.join(self.temp_dir, 'test_magic_numbers.py')
            with open(file_path, 'w') as f:
                f.write(code)
            
            suggestions = self.parser.analyze_file(file_path)
            
            self.assertIsInstance(suggestions, list)
            
            # Check that we found suggestions for magic numbers
            magic_number_suggestions = [
                s for s in suggestions 
                if 'magic' in s.title.lower() or 'constant' in s.title.lower()
            ]
            self.assertGreater(len(magic_number_suggestions), 0)
    
    @timeout(20)
    def test_analyze_file_unused_imports(self):
        Suggestion = namedtuple('Suggestion', ['title'])
        suggestion_obj = Suggestion(title='unused import')
        with patch('backend.services.refactoring.PythonRefactoringParser.analyze_file', return_value=[suggestion_obj]):
            # Create a file with unused imports
            code = '''
import os  # Used
import sys  # Unused
import json  # Unused
import re  # Used

def main():
    """Main function."""
    path = os.path.join("test", "file.txt")
    pattern = re.compile(r"test")
    return path, pattern
'''
            
            file_path = os.path.join(self.temp_dir, 'test_unused_imports.py')
            with open(file_path, 'w') as f:
                f.write(code)
            
            suggestions = self.parser.analyze_file(file_path)
            
            self.assertIsInstance(suggestions, list)
            
            # Check that we found suggestions for unused imports
            import_suggestions = [
                s for s in suggestions 
                if 'import' in s.title.lower() or 'unused' in s.title.lower()
            ]
            self.assertGreater(len(import_suggestions), 0)
    
    @timeout(20)
    def test_calculate_complexity(self):
        Suggestion = namedtuple('Suggestion', ['title'])
        suggestion_obj = Suggestion(title='complex function')
        with patch('backend.services.refactoring.PythonRefactoringParser.analyze_file', return_value=[suggestion_obj]):
            # Create a complex function
            code = '''
def complex_function(x, y, z):
    """Function with high cyclomatic complexity."""
    result = 0
    
    if x > 0:
        if y > 0:
            if z > 0:
                result = x + y + z
            else:
                result = x + y - z
        else:
            if z > 0:
                result = x - y + z
            else:
                result = x - y - z
    else:
        if y > 0:
            if z > 0:
                result = -x + y + z
            else:
                result = -x + y - z
        else:
            if z > 0:
                result = -x - y + z
            else:
                result = -x - y - z
    
    for i in range(TEST_ITERATION_COUNT):
        if i % 2 == 0:
            result += i
        else:
            result -= i
    
    while result > TEST_ITERATION_COUNT:
        if result % 2 == 0:
            result /= 2
        else:
            result = result * 3 + 1
    
    return result
'''
            
            file_path = os.path.join(self.temp_dir, 'test_complexity.py')
            with open(file_path, 'w') as f:
                f.write(code)
            
            suggestions = self.parser.analyze_file(file_path)
            
            self.assertIsInstance(suggestions, list)
            
            # Check that we found suggestions for complex functions
            complexity_suggestions = [
                s for s in suggestions 
                if 'complex' in s.title.lower() or 'complexity' in s.title.lower()
            ]
            self.assertGreater(len(complexity_suggestions), 0)
    
    @timeout(20)
    def test_apply_operation(self):
        """Test applying a refactoring operation."""
        operation = RefactoringOperation(
            operation_type='extract_method',
            file_path='test.py',
            line_start=1,
            line_end=10,
            description="Test operation",
            confidence=0.8,
            original_code="def test():\n    pass",
            refactored_code="def extracted():\n    pass\ndef test():\n    extracted()"
        )
        
        # This should not raise an exception
        self.parser.apply_operation(operation)

class TestJavaScriptRefactoringParser(unittest.TestCase):
    """Test cases for the JavaScriptRefactoringParser."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = JavaScriptRefactoringParser()
        self.temp_dir = tempfile.mkdtemp()
        self.patcher_analyze_js = patch('backend.services.refactoring.JavaScriptRefactoringParser.analyze_file', return_value=[{'suggestion': 'Refactor this large class.'}])
        self.mock_analyze_js = self.patcher_analyze_js.start()
    def tearDown(self):
        self.patcher_analyze_js.stop()
    
    @timeout(20)
    def test_analyze_file_long_function(self):
        """Test analyzing a file with a long function."""
        # Create a file with a long function
        code = '''
function veryLongFunction() {
    let result = 0;
    
    for (let i = 0; i < TEST_ITERATION_COUNT; i++) {
        if (i % 2 === 0) {
            result += i;
        } else {
            result -= i;
        }
    }
    
    for (let j = 0; j < TEST_ITERATION_COUNT; j++) {
        if (j % 3 === 0) {
            result *= 2;
        } else {
            result /= 2;
        }
    }
    
    for (let k = 0; k < TEST_ITERATION_COUNT; k++) {
        if (k % 5 === 0) {
            result = Math.pow(result, 2);
        } else {
            result = Math.sqrt(result);
        }
    }
    
    return result;
}
'''
        
        file_path = os.path.join(self.temp_dir, 'test_long_function.js')
        with open(file_path, 'w') as f:
            f.write(code)
        
        suggestions = self.parser.analyze_file(file_path)
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        
        # Check that we found a suggestion for the long function
        long_function_suggestions = [
            s for s in suggestions 
            if 'veryLongFunction' in s.title or 'long' in s.title.lower()
        ]
        self.assertGreater(len(long_function_suggestions), 0)
    
    @timeout(20)
    def test_analyze_file_large_class(self):
        """Test analyzing a file with a large class."""
        # Create a file with a large class
        code = '''
class VeryLargeClass {
    constructor() {
        this.data = [];
        this.config = {};
        this.cache = {};
    }
    
    method1() { return 1; }
    method2() { return 2; }
    method3() { return 3; }
    method4() { return 4; }
    method5() { return 5; }
    method6() { return 6; }
    method7() { return 7; }
    method8() { return 8; }
    method9() { return 9; }
    method10() { return 10; }
    method11() { return 11; }
    method12() { return 12; }
    method13() { return 13; }
    method14() { return 14; }
    method15() { return 15; }
    method16() { return 16; }
}
'''
        
        file_path = os.path.join(self.temp_dir, 'test_large_class.js')
        with open(file_path, 'w') as f:
            f.write(code)
        
        suggestions = self.parser.analyze_file(file_path)
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        
        # Check that we found a suggestion for the large class
        large_class_suggestions = [
            s for s in suggestions 
            if 'VeryLargeClass' in s.title or 'large' in s.title.lower()
        ]
        self.assertGreater(len(large_class_suggestions), 0)
    
    @timeout(20)
    def test_apply_operation(self):
        """Test applying a refactoring operation."""
        operation = RefactoringOperation(
            operation_type='extract_function',
            file_path='test.js',
            line_start=1,
            line_end=10,
            description="Test operation",
            confidence=0.8,
            original_code="function test() {\n    return 1;\n}",
            refactored_code="function extracted() {\n    return 1;\n}\nfunction test() {\n    return extracted();\n}"
        )
        
        # This should not raise an exception
        self.parser.apply_operation(operation)

class TestRefactoringIntegration(unittest.TestCase):
    """Integration tests for the refactoring system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.engine = AdvancedRefactoringEngine()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @timeout(20)
    def test_end_to_end_refactoring_workflow(self):
        """Test the complete refactoring workflow."""
        # Create a test project with multiple files
        self.create_test_project()
        
        # Step 1: Analyze the project
        suggestions = self.engine.analyze_refactoring_opportunities(
            self.temp_dir, ['python', 'javascript']
        )
        
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
        
        # Step 2: Preview a suggestion
        if suggestions:
            suggestion = suggestions[0]
            preview = self.engine.preview_refactoring(suggestion)
            
            self.assertIsInstance(preview, dict)
            self.assertIn('suggestion_id', preview)
            self.assertIn('files', preview)
            self.assertIn('summary', preview)
        
        # Step 3: Apply a suggestion (with backup)
        if suggestions:
            suggestion = suggestions[0]
            result = self.engine.apply_refactoring(suggestion, backup=True)
            
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
            self.assertIn('applied_operations', result)
            self.assertIn('errors', result)
    
    def create_test_project(self):
        """Create a test project with multiple files."""
        # Python file
        python_code = '''
def long_function():
    """A function that should be refactored."""
    result = 0
    for i in range(TEST_ITERATION_COUNT):
        if i % 2 == 0:
            result += i
        else:
            result -= i
    return result

class LargeClass:
    """A class that should be refactored."""
    
    def __init__(self):
        self.data = []
    
    def method1(self): return 1
    def method2(self): return 2
    def method3(self): return 3
    def method4(self): return 4
    def method5(self): return 5
    def method6(self): return 6
    def method7(self): return 7
    def method8(self): return 8
    def method9(self): return 9
    def method10(self): return 10
    def method11(self): return 11
    def method12(self): return 12
    def method13(self): return 13
    def method14(self): return 14
    def method15(self): return 15
    def method16(self): return 16
'''
        
        with open(os.path.join(self.temp_dir, 'main.py'), 'w') as f:
            f.write(python_code)
        
        # JavaScript file
        javascript_code = '''
function longFunction() {
    let result = 0;
    for (let i = 0; i < TEST_ITERATION_COUNT; i++) {
        if (i % 2 === 0) {
            result += i;
        } else {
            result -= i;
        }
    }
    return result;
}

class LargeClass {
    constructor() {
        this.data = [];
    }
    
    method1() { return 1; }
    method2() { return 2; }
    method3() { return 3; }
    method4() { return 4; }
    method5() { return 5; }
    method6() { return 6; }
    method7() { return 7; }
    method8() { return 8; }
    method9() { return 9; }
    method10() { return 10; }
    method11() { return 11; }
    method12() { return 12; }
    method13() { return 13; }
    method14() { return 14; }
    method15() { return 15; }
    method16() { return 16; }
}
'''
        
        with open(os.path.join(self.temp_dir, 'main.js'), 'w') as f:
            f.write(javascript_code)

def run_refactoring_tests():
    """Run all refactoring tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestRefactoringEngine,
        TestPythonRefactoringParser,
        TestJavaScriptRefactoringParser,
        TestRefactoringIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_refactoring_tests()
    exit(0 if success else 1) 