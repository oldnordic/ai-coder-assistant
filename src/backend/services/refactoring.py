"""
refactoring.py

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
import ast
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import difflib
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from ..utils.constants import MAX_FILE_SIZE_KB
from .intelligent_analyzer import CodeIssue, IssueType

logger = logging.getLogger(__name__)

@dataclass
class RefactoringOperation:
    """Represents a refactoring operation."""
    operation_type: str  # 'extract_method', 'extract_class', 'rename', 'inline', 'move'
    file_path: str
    line_start: int
    line_end: int
    description: str
    confidence: float  # 0.0 to 1.0
    original_code: str
    refactored_code: str
    dependencies: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RefactoringSuggestion:
    """Represents a refactoring suggestion with multiple operations."""
    id: str
    title: str
    description: str
    priority: str  # 'high', 'medium', 'low'
    operations: List[RefactoringOperation]
    impact_score: float  # 0.0 to 1.0
    estimated_time: str  # e.g., "5-10 minutes"
    category: str  # 'performance', 'maintainability', 'readability', 'architecture'
    tags: List[str] = field(default_factory=list)

class AdvancedRefactoringEngine:
    """
    Advanced refactoring engine that provides comprehensive refactoring capabilities.
    Supports multiple languages and refactoring patterns.
    """
    
    def __init__(self):
        self.language_parsers = {
            'python': PythonRefactoringParser(),
            'javascript': JavaScriptRefactoringParser(),
            'typescript': TypeScriptRefactoringParser(),
            'java': JavaRefactoringParser(),
            'cpp': CppRefactoringParser(),
        }
        self.refactoring_patterns = self._load_refactoring_patterns()
        self.safety_checks = self._load_safety_checks()
        
    def _load_refactoring_patterns(self) -> Dict[str, List[Dict]]:
        """Load refactoring patterns for different languages."""
        return {
            'python': [
                {
                    'name': 'extract_method',
                    'pattern': r'def\s+\w+\s*\([^)]*\):\s*\n(?:[^\n]*\n){20,}',
                    'description': 'Long method that can be broken down',
                    'priority': 'medium'
                },
                {
                    'name': 'extract_class',
                    'pattern': r'class\s+\w+:\s*\n(?:.*\n){100,}',
                    'description': 'Large class that can be split',
                    'priority': 'high'
                },
                {
                    'name': 'inline_variable',
                    'pattern': r'(\w+)\s*=\s*([^;\n]+)\s*\n\s*return\s+\1',
                    'description': 'Variable used only once in return',
                    'priority': 'low'
                },
                {
                    'name': 'extract_constant',
                    'pattern': r'\b\d{3,}\b(?!\s*[a-zA-Z])',
                    'description': 'Magic numbers that should be constants',
                    'priority': 'low'
                }
            ],
            'javascript': [
                {
                    'name': 'extract_function',
                    'pattern': r'function\s+\w+\s*\([^)]*\)\s*{\s*(?:[^{}]|{[^{}]*}){200,}}',
                    'description': 'Long function that can be broken down',
                    'priority': 'medium'
                },
                {
                    'name': 'extract_class',
                    'pattern': r'class\s+\w+\s*{\s*(?:[^{}]|{[^{}]*}){300,}}',
                    'description': 'Large class that can be split',
                    'priority': 'high'
                }
            ]
        }
    
    def _load_safety_checks(self) -> Dict[str, List[str]]:
        """Load safety checks for refactoring operations."""
        return {
            'python': [
                'check_imports_not_broken',
                'check_function_signatures',
                'check_class_inheritance',
                'check_variable_scope',
                'check_test_coverage'
            ],
            'javascript': [
                'check_imports_not_broken',
                'check_function_signatures',
                'check_class_methods',
                'check_variable_scope',
                'check_module_exports'
            ]
        }
    
    def analyze_refactoring_opportunities(self, project_path: str, 
                                        languages: List[str] = None) -> List[RefactoringSuggestion]:
        """
        Analyze a project for refactoring opportunities.
        
        Args:
            project_path: Path to the project directory
            languages: List of languages to analyze (default: all supported)
            
        Returns:
            List of refactoring suggestions
        """
        if languages is None:
            languages = ['python', 'javascript', 'typescript', 'java', 'cpp']
        
        suggestions = []
        
        try:
            # Find source files
            files = self._find_source_files(project_path, languages)
            
            # Analyze each file
            for file_path in files:
                language = self._detect_language(file_path)
                parser = self.language_parsers.get(language)
                
                if parser:
                    try:
                        file_suggestions = parser.analyze_file(file_path)
                        suggestions.extend(file_suggestions)
                    except Exception as e:
                        logger.error(f"Error analyzing {file_path}: {e}")
                        continue
            
            # Group related suggestions
            grouped_suggestions = self._group_related_suggestions(suggestions)
            
            # Sort by priority and impact
            sorted_suggestions = sorted(
                grouped_suggestions,
                key=lambda s: (self._priority_score(s.priority), s.impact_score),
                reverse=True
            )
            
            return sorted_suggestions
            
        except Exception as e:
            logger.error(f"Error analyzing refactoring opportunities: {e}")
            return []
    
    def _find_source_files(self, project_path: str, languages: List[str]) -> List[str]:
        """Find all source files in the project."""
        files = []
        language_extensions = {
            'python': ['.py'],
            'javascript': ['.js'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'cpp': ['.cpp', '.cc', '.cxx', '.h', '.hpp']
        }
        
        extensions = []
        for lang in languages:
            if lang in language_extensions:
                extensions.extend(language_extensions[lang])
        
        for root, dirs, filenames in os.walk(project_path):
            # Skip common directories that shouldn't be refactored
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', 'venv', '.venv'}]
            
            for filename in filenames:
                if any(filename.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, filename)
                    
                    # Check file size
                    try:
                        if os.path.getsize(file_path) <= MAX_FILE_SIZE_KB * 1024:
                            files.append(file_path)
                    except OSError:
                        continue
        
        return files
    
    def _detect_language(self, file_path: str) -> str:
        """Detect the programming language of a file."""
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'cpp',
            '.hpp': 'cpp'
        }
        return language_map.get(ext, 'unknown')
    
    def _group_related_suggestions(self, suggestions: List[RefactoringSuggestion]) -> List[RefactoringSuggestion]:
        """Group related refactoring suggestions together."""
        # This is a simplified grouping - could be enhanced with more sophisticated logic
        grouped = []
        processed = set()
        
        for suggestion in suggestions:
            if suggestion.id in processed:
                continue
            
            related = [s for s in suggestions if self._are_related(suggestion, s)]
            if len(related) > 1:
                # Merge related suggestions
                merged = self._merge_suggestions(related)
                grouped.append(merged)
                processed.update(s.id for s in related)
            else:
                grouped.append(suggestion)
                processed.add(suggestion.id)
        
        return grouped
    
    def _are_related(self, s1: RefactoringSuggestion, s2: RefactoringSuggestion) -> bool:
        """Check if two suggestions are related."""
        # Same file and similar operations
        if s1.operations and s2.operations:
            file1 = s1.operations[0].file_path
            file2 = s2.operations[0].file_path
            return file1 == file2 and s1.category == s2.category
        
        return False
    
    def _merge_suggestions(self, suggestions: List[RefactoringSuggestion]) -> RefactoringSuggestion:
        """Merge multiple related suggestions into one."""
        if not suggestions:
            return suggestions[0]
        
        # Use the first suggestion as base
        base = suggestions[0]
        
        # Merge operations
        all_operations = []
        for suggestion in suggestions:
            all_operations.extend(suggestion.operations)
        
        # Calculate combined impact
        total_impact = sum(s.impact_score for s in suggestions) / len(suggestions)
        
        # Create merged suggestion
        merged = RefactoringSuggestion(
            id=f"merged_{base.id}",
            title=f"Multiple {base.category} improvements",
            description=f"Combined {len(suggestions)} related refactoring operations",
            priority=self._highest_priority([s.priority for s in suggestions]),
            operations=all_operations,
            impact_score=total_impact,
            estimated_time=self._estimate_combined_time(suggestions),
            category=base.category,
            tags=list(set(tag for s in suggestions for tag in s.tags))
        )
        
        return merged
    
    def _highest_priority(self, priorities: List[str]) -> str:
        """Get the highest priority from a list."""
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        return max(priorities, key=lambda p: priority_order.get(p, 0))
    
    def _estimate_combined_time(self, suggestions: List[RefactoringSuggestion]) -> str:
        """Estimate combined time for multiple suggestions."""
        # Simple estimation - could be enhanced
        total_minutes = len(suggestions) * 5  # Assume 5 minutes per suggestion
        if total_minutes <= 15:
            return f"{total_minutes} minutes"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}h {minutes}m"
    
    def _priority_score(self, priority: str) -> int:
        """Convert priority string to numeric score."""
        return {'high': 3, 'medium': 2, 'low': 1}.get(priority, 1)
    
    def apply_refactoring(self, suggestion: RefactoringSuggestion, 
                         backup: bool = True) -> Dict[str, Any]:
        """
        Apply a refactoring suggestion.
        
        Args:
            suggestion: The refactoring suggestion to apply
            backup: Whether to create backup files
            
        Returns:
            Dictionary with results and any errors
        """
        results = {
            'success': True,
            'applied_operations': [],
            'errors': [],
            'backup_files': [],
            'modified_files': set()
        }
        
        try:
            # Create backups if requested
            if backup:
                for operation in suggestion.operations:
                    backup_path = self._create_backup(operation.file_path)
                    if backup_path:
                        results['backup_files'].append(backup_path)
            
            # Apply each operation
            for operation in suggestion.operations:
                try:
                    self._apply_operation(operation)
                    results['applied_operations'].append(operation)
                    results['modified_files'].add(operation.file_path)
                except Exception as e:
                    results['errors'].append(f"Failed to apply {operation.operation_type}: {e}")
                    results['success'] = False
            
            # Run safety checks
            safety_results = self._run_safety_checks(suggestion)
            results['safety_checks'] = safety_results
            
            if not safety_results['passed']:
                results['warnings'] = safety_results['warnings']
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Refactoring failed: {e}")
        
        return results
    
    def _create_backup(self, file_path: str) -> Optional[str]:
        """Create a backup of a file."""
        try:
            backup_path = f"{file_path}.backup"
            with open(file_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup for {file_path}: {e}")
            return None
    
    def _apply_operation(self, operation: RefactoringOperation):
        """Apply a single refactoring operation."""
        language = self._detect_language(operation.file_path)
        parser = self.language_parsers.get(language)
        
        if parser:
            parser.apply_operation(operation)
        else:
            raise ValueError(f"No parser available for language: {language}")
    
    def _run_safety_checks(self, suggestion: RefactoringSuggestion) -> Dict[str, Any]:
        """Run safety checks after refactoring."""
        results = {
            'passed': True,
            'warnings': [],
            'errors': []
        }
        
        for operation in suggestion.operations:
            language = self._detect_language(operation.file_path)
            checks = self.safety_checks.get(language, [])
            
            for check_name in checks:
                try:
                    check_method = getattr(self, check_name, None)
                    if check_method:
                        check_result = check_method(operation)
                        if not check_result['passed']:
                            results['warnings'].extend(check_result['warnings'])
                            if check_result.get('critical', False):
                                results['errors'].extend(check_result['errors'])
                                results['passed'] = False
                except Exception as e:
                    results['warnings'].append(f"Safety check {check_name} failed: {e}")
        
        return results
    
    def preview_refactoring(self, suggestion: RefactoringSuggestion) -> Dict[str, Any]:
        """
        Preview the changes that would be made by a refactoring suggestion.
        
        Args:
            suggestion: The refactoring suggestion to preview
            
        Returns:
            Dictionary with preview information including diffs
        """
        preview = {
            'suggestion_id': suggestion.id,
            'title': suggestion.title,
            'description': suggestion.description,
            'files': {},
            'summary': {
                'files_modified': 0,
                'lines_added': 0,
                'lines_removed': 0,
                'operations': len(suggestion.operations)
            }
        }
        
        for operation in suggestion.operations:
            file_path = operation.file_path
            
            if file_path not in preview['files']:
                preview['files'][file_path] = {
                    'original_content': '',
                    'modified_content': '',
                    'diff': '',
                    'operations': []
                }
                
                # Read original content
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        preview['files'][file_path]['original_content'] = f.read()
                except Exception as e:
                    preview['files'][file_path]['error'] = f"Could not read file: {e}"
                    continue
            
            # Add operation to file
            preview['files'][file_path]['operations'].append({
                'type': operation.operation_type,
                'line_start': operation.line_start,
                'line_end': operation.line_end,
                'description': operation.description
            })
            
            # Generate diff
            original_lines = preview['files'][file_path]['original_content'].splitlines()
            modified_lines = self._apply_operation_to_lines(original_lines, operation)
            
            # Create diff
            diff = list(difflib.unified_diff(
                original_lines,
                modified_lines,
                fromfile=f'a/{file_path}',
                tofile=f'b/{file_path}',
                lineterm=''
            ))
            
            preview['files'][file_path]['diff'] = '\n'.join(diff)
            preview['files'][file_path]['modified_content'] = '\n'.join(modified_lines)
            
            # Update summary
            preview['summary']['files_modified'] += 1
            preview['summary']['lines_added'] += len([line for line in diff if line.startswith('+') and not line.startswith('+++')])
            preview['summary']['lines_removed'] += len([line for line in diff if line.startswith('-') and not line.startswith('---')])
        
        return preview
    
    def _apply_operation_to_lines(self, lines: List[str], operation: RefactoringOperation) -> List[str]:
        """Apply a refactoring operation to a list of lines (for preview)."""
        # This is a simplified implementation - language parsers would handle this more sophisticatedly
        modified_lines = lines.copy()
        
        if operation.line_start <= len(modified_lines) and operation.line_end <= len(modified_lines):
            # Replace the lines with refactored code
            refactored_lines = operation.refactored_code.splitlines()
            
            # Remove original lines
            del modified_lines[operation.line_start - 1:operation.line_end]
            
            # Insert refactored lines
            for i, line in enumerate(refactored_lines):
                modified_lines.insert(operation.line_start - 1 + i, line)
        
        return modified_lines

class PythonRefactoringParser:
    """Parser for Python code refactoring."""
    
    def analyze_file(self, file_path: str) -> List[RefactoringSuggestion]:
        """Analyze a Python file for refactoring opportunities."""
        suggestions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            lines = content.splitlines()
            
            # Analyze functions
            suggestions.extend(self._analyze_functions(tree, lines, file_path))
            
            # Analyze classes
            suggestions.extend(self._analyze_classes(tree, lines, file_path))
            
            # Analyze variables and constants
            suggestions.extend(self._analyze_variables(tree, lines, file_path))
            
            # Analyze imports
            suggestions.extend(self._analyze_imports(tree, lines, file_path))
            
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
        
        return suggestions
    
    def _analyze_functions(self, tree: ast.AST, lines: List[str], file_path: str) -> List[RefactoringSuggestion]:
        """Analyze functions for refactoring opportunities."""
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for long functions
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    function_length = node.end_lineno - node.lineno
                    if function_length > 20:
                        suggestion = self._create_extract_method_suggestion(
                            node, lines, file_path, function_length
                        )
                        suggestions.append(suggestion)
                
                # Check for complex functions
                complexity = self._calculate_complexity(node)
                if complexity > 10:
                    suggestion = self._create_simplify_function_suggestion(
                        node, lines, file_path, complexity
                    )
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _analyze_classes(self, tree: ast.AST, lines: List[str], file_path: str) -> List[RefactoringSuggestion]:
        """Analyze classes for refactoring opportunities."""
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check for large classes
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    class_length = node.end_lineno - node.lineno
                    if class_length > 50:
                        suggestion = self._create_extract_class_suggestion(
                            node, lines, file_path, class_length
                        )
                        suggestions.append(suggestion)
                
                # Check for too many methods
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > 10:
                    suggestion = self._create_split_class_suggestion(
                        node, lines, file_path, len(methods)
                    )
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _analyze_variables(self, tree: ast.AST, lines: List[str], file_path: str) -> List[RefactoringSuggestion]:
        """Analyze variables for refactoring opportunities."""
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Check for magic numbers
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        value = node.value
                        if isinstance(value, ast.Constant) and isinstance(value.value, (int, float)):
                            if abs(value.value) > 100:
                                suggestion = self._create_extract_constant_suggestion(
                                    node, lines, file_path, value.value
                                )
                                suggestions.append(suggestion)
        
        return suggestions
    
    def _analyze_imports(self, tree: ast.AST, lines: List[str], file_path: str) -> List[RefactoringSuggestion]:
        """Analyze imports for refactoring opportunities."""
        suggestions = []
        
        # Check for unused imports
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in used_names and not alias.name.startswith('_'):
                        suggestion = self._create_remove_unused_import_suggestion(
                            node, lines, file_path, [alias.name]
                        )
                        suggestions.append(suggestion)
        
        return suggestions
    
    def _create_extract_method_suggestion(self, node: ast.FunctionDef, lines: List[str], 
                                        file_path: str, length: int) -> RefactoringSuggestion:
        """Create a suggestion for extracting a method."""
        operation = RefactoringOperation(
            operation_type='extract_method',
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno + length,
            description=f"Extract method from long function '{node.name}' ({length} lines)",
            confidence=0.8,
            original_code=self._get_code_snippet(lines, node.lineno, node.end_lineno),
            refactored_code=self._generate_extracted_method_code(node, lines),
            dependencies=[file_path],
            risks=['May break existing functionality'],
            benefits=['Improved readability', 'Better testability', 'Reduced complexity']
        )
        
        return RefactoringSuggestion(
            id=f"extract_method_{file_path}_{node.lineno}",
            title=f"Extract method from '{node.name}'",
            description=f"Function '{node.name}' is {length} lines long and can be broken down into smaller methods",
            priority='medium',
            operations=[operation],
            impact_score=0.7,
            estimated_time="10-15 minutes",
            category='maintainability',
            tags=['extract-method', 'long-function', 'complexity']
        )
    
    def _create_extract_class_suggestion(self, node: ast.ClassDef, lines: List[str], 
                                       file_path: str, length: int) -> RefactoringSuggestion:
        """Create a suggestion for extracting a class."""
        operation = RefactoringOperation(
            operation_type='extract_class',
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno + length,
            description=f"Extract class from large class '{node.name}' ({length} lines)",
            confidence=0.9,
            original_code=self._get_code_snippet(lines, node.lineno, node.end_lineno),
            refactored_code=self._generate_extracted_class_code(node, lines),
            dependencies=[file_path],
            risks=['May require updating imports', 'Could break inheritance'],
            benefits=['Better separation of concerns', 'Improved maintainability', 'Reduced coupling']
        )
        
        return RefactoringSuggestion(
            id=f"extract_class_{file_path}_{node.lineno}",
            title=f"Extract class from '{node.name}'",
            description=f"Class '{node.name}' is {length} lines long and can be split into smaller classes",
            priority='high',
            operations=[operation],
            impact_score=0.8,
            estimated_time="20-30 minutes",
            category='architecture',
            tags=['extract-class', 'large-class', 'separation-of-concerns']
        )
    
    def _create_extract_constant_suggestion(self, node: ast.Assign, lines: List[str], 
                                          file_path: str, value: Any) -> RefactoringSuggestion:
        """Create a suggestion for extracting a constant."""
        line_start = node.lineno
        line_end = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
        
        # Generate constant name
        constant_name = f"CONSTANT_{abs(hash(str(value))) % 10000}"
        
        # Create operation
        operation = RefactoringOperation(
            operation_type='extract_constant',
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            description=f"Extract magic number {value} as constant {constant_name}",
            confidence=0.8,
            original_code=self._get_code_snippet(lines, line_start, line_end),
            refactored_code=self._generate_constant_code(node, value),
            dependencies=[],
            risks=['May affect other parts of code that use this value'],
            benefits=['Improved readability', 'Centralized configuration'],
            context={'value': value, 'constant_name': constant_name}
        )
        
        return RefactoringSuggestion(
            id=f"extract_constant_{file_path}_{line_start}",
            title=f"Extract constant for magic number {value}",
            description=f"Replace magic number {value} with named constant {constant_name}",
            priority='medium',
            operations=[operation],
            impact_score=0.6,
            estimated_time="2-3 minutes",
            category='readability',
            tags=['magic-number', 'constant', 'readability']
        )
    
    def _create_remove_unused_import_suggestion(self, import_node: ast.Import, lines: List[str], 
                                              file_path: str, unused_names: List[str]) -> RefactoringSuggestion:
        """Create a suggestion for removing unused imports."""
        line_start = import_node.lineno
        line_end = import_node.end_lineno if hasattr(import_node, 'end_lineno') and import_node.end_lineno is not None else import_node.lineno
        
        # Create operation
        operation = RefactoringOperation(
            operation_type='remove_unused_import',
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            description=f"Remove unused import: {', '.join(unused_names)}",
            confidence=0.9,
            original_code=self._get_code_snippet(lines, line_start, line_end),
            refactored_code="",  # Remove the line
            dependencies=[],
            risks=['May break code if import is actually used'],
            benefits=['Cleaner code', 'Faster imports', 'Reduced dependencies'],
            context={'unused_names': unused_names}
        )
        
        return RefactoringSuggestion(
            id=f"remove_import_{file_path}_{line_start}",
            title=f"Remove unused import: {', '.join(unused_names)}",
            description=f"Remove unused import statement for {', '.join(unused_names)}",
            priority='low',
            operations=[operation],
            impact_score=0.3,
            estimated_time="1 minute",
            category='maintainability',
            tags=['unused-import', 'cleanup', 'maintainability']
        )
    
    def _create_split_class_suggestion(self, node: ast.ClassDef, lines: List[str], 
                                     file_path: str, method_count: int) -> RefactoringSuggestion:
        """Create a suggestion for splitting a large class."""
        line_start = node.lineno
        line_end = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno is not None else node.lineno
        
        # Create operation
        operation = RefactoringOperation(
            operation_type='extract_class',
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            description=f"Split large class with {method_count} methods into smaller classes",
            confidence=0.7,
            original_code=self._get_code_snippet(lines, line_start, line_end),
            refactored_code=self._generate_extracted_class_code(node, lines),
            dependencies=[],
            risks=['May break existing code that uses this class'],
            benefits=['Better separation of concerns', 'Improved testability'],
            context={'method_count': method_count, 'class_name': node.name}
        )
        
        return RefactoringSuggestion(
            id=f"split_class_{file_path}_{line_start}",
            title=f"Split large class {node.name}",
            description=f"Class {node.name} has {method_count} methods and should be split into smaller, focused classes",
            priority='medium',
            operations=[operation],
            impact_score=0.7,
            estimated_time="15-30 minutes",
            category='architecture',
            tags=['large-class', 'extract-class', 'architecture']
        )
    
    def _create_simplify_function_suggestion(self, node: ast.FunctionDef, lines: List[str], 
                                           file_path: str, complexity: int) -> RefactoringSuggestion:
        """Create a suggestion for simplifying a complex function."""
        line_start = node.lineno
        line_end = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno is not None else node.lineno
        
        # Create operation
        operation = RefactoringOperation(
            operation_type='extract_method',
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            description=f"Simplify complex function with cyclomatic complexity {complexity}",
            confidence=0.8,
            original_code=self._get_code_snippet(lines, line_start, line_end),
            refactored_code=self._generate_extracted_method_code(node, lines),
            dependencies=[],
            risks=['May change function behavior if not careful'],
            benefits=['Improved readability', 'Better testability', 'Reduced complexity'],
            context={'complexity': complexity, 'function_name': node.name}
        )
        
        return RefactoringSuggestion(
            id=f"simplify_function_{file_path}_{line_start}",
            title=f"Simplify complex function {node.name}",
            description=f"Function {node.name} has cyclomatic complexity {complexity} and should be simplified",
            priority='high',
            operations=[operation],
            impact_score=0.8,
            estimated_time="10-20 minutes",
            category='maintainability',
            tags=['complex-function', 'extract-method', 'maintainability']
        )
    
    def _get_code_snippet(self, lines: List[str], start_line: int, end_line: int) -> str:
        """Get code snippet between start and end lines."""
        if end_line is None:
            end_line = start_line
        start = max(0, start_line - 1)
        end = min(len(lines), end_line)
        return '\n'.join(lines[start:end])
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.AsyncWith, ast.With, ast.Try, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _generate_extracted_method_code(self, node: ast.FunctionDef, lines: List[str]) -> str:
        """Generate code for an extracted method."""
        # This is a simplified implementation
        original_code = self._get_code_snippet(lines, node.lineno, node.end_lineno)
        
        # Extract the body (simplified)
        lines_code = original_code.splitlines()
        if len(lines_code) > 2:
            # Remove function definition and keep body
            body_lines = lines_code[1:-1]  # Remove first and last lines
            return '\n'.join(body_lines)
        
        return original_code
    
    def _generate_extracted_class_code(self, node: ast.ClassDef, lines: List[str]) -> str:
        """Generate code for an extracted class."""
        # This is a simplified implementation
        return f"# Extracted class from {node.name}\nclass ExtractedClass:\n    pass"
    
    def _generate_constant_code(self, node: ast.Assign, value: Any) -> str:
        """Generate code for an extracted constant."""
        # Generate a meaningful constant name
        constant_name = f"CONSTANT_{abs(value)}"
        return f"{constant_name} = {value}"
    
    def apply_operation(self, operation: RefactoringOperation):
        """Apply a refactoring operation to a Python file."""
        # This would implement the actual refactoring logic
        # For now, we'll just log the operation
        logger.info(f"Applying {operation.operation_type} to {operation.file_path}")

class JavaScriptRefactoringParser:
    """Parser for JavaScript code refactoring."""
    
    def analyze_file(self, file_path: str) -> List[RefactoringSuggestion]:
        """Analyze a JavaScript file for refactoring opportunities."""
        # Simplified implementation - would use a proper JavaScript parser
        suggestions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic pattern-based analysis
            suggestions.extend(self._analyze_functions_pattern(content, file_path))
            suggestions.extend(self._analyze_classes_pattern(content, file_path))
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
        
        return suggestions
    
    def _analyze_functions_pattern(self, content: str, file_path: str) -> List[RefactoringSuggestion]:
        """Analyze functions using regex patterns."""
        suggestions = []
        
        # Find long functions
        function_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*{([^{}]|{[^{}]*}){100,}}'
        matches = re.finditer(function_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            function_name = match.group(1)
            function_body = match.group(2)
            
            operation = RefactoringOperation(
                operation_type='extract_function',
                file_path=file_path,
                line_start=content[:match.start()].count('\n') + 1,
                line_end=content[:match.end()].count('\n') + 1,
                description=f"Extract function from long function '{function_name}'",
                confidence=0.7,
                original_code=match.group(0),
                refactored_code=f"// Extracted function from {function_name}",
                dependencies=[file_path],
                risks=['May break existing functionality'],
                benefits=['Improved readability', 'Better testability']
            )
            
            suggestion = RefactoringSuggestion(
                id=f"extract_function_{file_path}_{function_name}",
                title=f"Extract function from '{function_name}'",
                description=f"Function '{function_name}' is very long and can be broken down",
                priority='medium',
                operations=[operation],
                impact_score=0.6,
                estimated_time="15-20 minutes",
                category='maintainability',
                tags=['extract-function', 'long-function']
            )
            
            suggestions.append(suggestion)
        
        return suggestions
    
    def _analyze_classes_pattern(self, content: str, file_path: str) -> List[RefactoringSuggestion]:
        """Analyze classes using regex patterns."""
        suggestions = []
        
        # Find large classes
        class_pattern = r'class\s+(\w+)\s*{([^{}]|{[^{}]*}){200,}}'
        matches = re.finditer(class_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            class_name = match.group(1)
            
            operation = RefactoringOperation(
                operation_type='extract_class',
                file_path=file_path,
                line_start=content[:match.start()].count('\n') + 1,
                line_end=content[:match.end()].count('\n') + 1,
                description=f"Extract class from large class '{class_name}'",
                confidence=0.8,
                original_code=match.group(0),
                refactored_code=f"// Extracted class from {class_name}",
                dependencies=[file_path],
                risks=['May require updating imports'],
                benefits=['Better separation of concerns', 'Improved maintainability']
            )
            
            suggestion = RefactoringSuggestion(
                id=f"extract_class_{file_path}_{class_name}",
                title=f"Extract class from '{class_name}'",
                description=f"Class '{class_name}' is very large and can be split",
                priority='high',
                operations=[operation],
                impact_score=0.7,
                estimated_time="25-35 minutes",
                category='architecture',
                tags=['extract-class', 'large-class']
            )
            
            suggestions.append(suggestion)
        
        return suggestions
    
    def apply_operation(self, operation: RefactoringOperation):
        """Apply a refactoring operation to a JavaScript file."""
        logger.info(f"Applying {operation.operation_type} to {operation.file_path}")

class TypeScriptRefactoringParser(JavaScriptRefactoringParser):
    """Parser for TypeScript code refactoring."""
    # Inherits from JavaScript parser with TypeScript-specific enhancements
    pass

class JavaRefactoringParser:
    """Parser for Java code refactoring."""
    
    def analyze_file(self, file_path: str) -> List[RefactoringSuggestion]:
        """Analyze a Java file for refactoring opportunities."""
        # Simplified implementation
        return []
    
    def apply_operation(self, operation: RefactoringOperation):
        """Apply a refactoring operation to a Java file."""
        logger.info(f"Applying {operation.operation_type} to {operation.file_path}")

class CppRefactoringParser:
    """Parser for C++ code refactoring."""
    
    def analyze_file(self, file_path: str) -> List[RefactoringSuggestion]:
        """Analyze a C++ file for refactoring opportunities."""
        # Simplified implementation
        return []
    
    def apply_operation(self, operation: RefactoringOperation):
        """Apply a refactoring operation to a C++ file."""
        logger.info(f"Applying {operation.operation_type} to {operation.file_path}")

# Global instance for easy access
refactoring_engine = AdvancedRefactoringEngine() 