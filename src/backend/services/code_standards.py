"""
Code Standards Service

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

"""
Code Standards Service - Enforce company-specific coding standards.
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

import ast
from ast import NodeVisitor

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Severity levels for code standards violations."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Language(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"


@dataclass
class CodeRule:
    """Code standard rule definition."""
    id: str
    name: str
    description: str
    language: Language
    severity: Severity
    pattern: str  # Regex pattern or AST pattern
    message: str
    category: str  # "naming", "style", "security", "performance", etc.
    enabled: bool = True
    auto_fix: bool = False
    fix_template: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class CodeViolation:
    """Code standard violation."""
    rule_id: str
    rule_name: str
    severity: Severity
    message: str
    line_number: int
    column: int
    line_content: str
    file_path: str
    category: str
    auto_fixable: bool = False
    suggested_fix: Optional[str] = None


@dataclass
class CodeStandard:
    """Code standard configuration."""
    name: str
    description: str
    company: str
    version: str
    languages: List[Language] = field(default_factory=list)
    rules: List[CodeRule] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    enabled: bool = True


@dataclass
class CodeAnalysisResult:
    """Result of code standards analysis."""
    file_path: str
    language: Language
    violations: List[CodeViolation] = field(default_factory=list)
    total_violations: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    auto_fixable_count: int = 0


class PythonASTVisitor(NodeVisitor):
    """AST visitor for Python code analysis."""
    
    def __init__(self, rules: List[CodeRule], file_path: str):
        self.rules = rules
        self.file_path = file_path
        self.violations: List[CodeViolation] = []
        self.current_line = 0
    
    def visit_FunctionDef(self, node):
        """Visit function definitions."""
        self._check_naming_convention(node, "function")
        self._check_function_length(node)
        self._check_docstring(node)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Visit class definitions."""
        self._check_naming_convention(node, "class")
        self._check_class_length(node)
        self._check_docstring(node)
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Visit variable names."""
        self._check_naming_convention(node, "variable")
        self.generic_visit(node)
    
    def visit_Constant(self, node):
        """Visit constants."""
        self._check_magic_numbers(node)
        self.generic_visit(node)
    
    def _check_naming_convention(self, node, node_type: str):
        """Check naming conventions."""
        name = getattr(node, 'name', None)
        if not name:
            return
        
        for rule in self.rules:
            if (rule.category == "naming" and 
                rule.language == Language.PYTHON and 
                rule.enabled):
                
                if re.match(rule.pattern, name):
                    self._add_violation(rule, node.lineno, node.col_offset, 
                                      f"Line {node.lineno}: {name}")
    
    def _check_function_length(self, node):
        """Check function length."""
        for rule in self.rules:
            if (rule.category == "complexity" and 
                rule.language == Language.PYTHON and 
                rule.enabled):
                
                # Count lines in function
                lines = len(node.body)
                if lines > int(rule.pattern):
                    self._add_violation(rule, node.lineno, node.col_offset,
                                      f"Function '{node.name}' has {lines} lines")
    
    def _check_class_length(self, node):
        """Check class length."""
        for rule in self.rules:
            if (rule.category == "complexity" and 
                rule.language == Language.PYTHON and 
                rule.enabled):
                
                # Count methods in class
                methods = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
                if methods > int(rule.pattern):
                    self._add_violation(rule, node.lineno, node.col_offset,
                                      f"Class '{node.name}' has {methods} methods")
    
    def _check_docstring(self, node):
        """Check for docstrings."""
        for rule in self.rules:
            if (rule.category == "documentation" and 
                rule.language == Language.PYTHON and 
                rule.enabled):
                
                has_docstring = (node.body and 
                               isinstance(node.body[0], ast.Expr) and
                               isinstance(node.body[0].value, ast.Constant) and
                               isinstance(node.body[0].value.value, str))
                
                if not has_docstring:
                    self._add_violation(rule, node.lineno, node.col_offset,
                                      f"Missing docstring for '{getattr(node, 'name', 'unknown')}'")
    
    def _check_magic_numbers(self, node):
        """Check for magic numbers."""
        for rule in self.rules:
            if (rule.category == "style" and 
                rule.language == Language.PYTHON and 
                rule.enabled):
                
                if isinstance(node.value, (int, float)):
                    value = str(node.value)
                    if re.match(rule.pattern, value):
                        self._add_violation(rule, node.lineno, node.col_offset,
                                          f"Magic number: {value}")
    
    def _add_violation(self, rule: CodeRule, line: int, column: int, context: str):
        """Add a violation to the list."""
        violation = CodeViolation(
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            message=rule.message,
            line_number=line,
            column=column,
            line_content=context,
            file_path=self.file_path,
            category=rule.category,
            auto_fixable=rule.auto_fix,
            suggested_fix=rule.fix_template
        )
        self.violations.append(violation)


class CodeStandardsService:
    """Main code standards service."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "code_standards_config.json"
        self.standards: Dict[str, CodeStandard] = {}
        self.current_standard: Optional[str] = None
        
        self.load_config()
        self._create_default_standards()
    
    def load_config(self):
        """Load configuration from file."""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                # Load standards
                for standard_data in data.get("standards", []):
                    # Convert language strings to Language enum
                    languages = []
                    for lang in standard_data.get("languages", []):
                        if isinstance(lang, str):
                            languages.append(Language(lang))
                        elif hasattr(lang, 'value'):  # Handle enum objects
                            languages.append(lang)
                        else:
                            languages.append(Language(str(lang)))
                    standard_data["languages"] = languages
                    
                    # Convert rules
                    rules = []
                    for rule_data in standard_data.get("rules", []):
                        # Handle language conversion
                        rule_language = rule_data["language"]
                        if isinstance(rule_language, str):
                            rule_data["language"] = Language(rule_language)
                        elif hasattr(rule_language, 'value'):  # Handle enum objects
                            rule_data["language"] = rule_language
                        else:
                            rule_data["language"] = Language(str(rule_language))
                        
                        # Handle severity conversion
                        rule_severity = rule_data["severity"]
                        if isinstance(rule_severity, str):
                            rule_data["severity"] = Severity(rule_severity)
                        elif hasattr(rule_severity, 'value'):  # Handle enum objects
                            rule_data["severity"] = rule_severity
                        else:
                            rule_data["severity"] = Severity(str(rule_severity))
                        
                        rules.append(CodeRule(**rule_data))
                    standard_data["rules"] = rules
                    
                    standard = CodeStandard(**standard_data)
                    self.standards[standard.name] = standard
                
                self.current_standard = data.get("current_standard")
                    
        except Exception as e:
            logger.error(f"Error loading code standards config: {e}")
    
    def save_config(self):
        """Save configuration to file."""
        try:
            config_data = {
                "standards": [],
                "current_standard": self.current_standard
            }
            
            for standard in self.standards.values():
                standard_dict = standard.__dict__.copy()
                # Convert Language enum to string values
                standard_dict["languages"] = [lang.value for lang in standard.languages]
                
                # Convert rules with proper enum handling
                rules_data = []
                for rule in standard.rules:
                    rule_dict = rule.__dict__.copy()
                    rule_dict["language"] = rule.language.value
                    rule_dict["severity"] = rule.severity.value
                    rules_data.append(rule_dict)
                standard_dict["rules"] = rules_data
                
                config_data["standards"].append(standard_dict)
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving code standards config: {e}")
    
    def _create_default_standards(self):
        """Create default code standards."""
        if not self.standards:
            # Python PEP 8 Standard
            python_pep8 = CodeStandard(
                name="Python PEP 8",
                description="Python code style guide based on PEP 8",
                company="Default",
                version="1.0.0",
                languages=[Language.PYTHON],
                rules=[
                    CodeRule(
                        id="python_naming_functions",
                        name="Function Naming Convention",
                        description="Functions should use snake_case naming",
                        language=Language.PYTHON,
                        severity=Severity.WARNING,
                        pattern=r"^[a-z_][a-z0-9_]*$",
                        message="Function names should use snake_case",
                        category="naming",
                        auto_fix=True
                    ),
                    CodeRule(
                        id="python_naming_classes",
                        name="Class Naming Convention",
                        description="Classes should use PascalCase naming",
                        language=Language.PYTHON,
                        severity=Severity.WARNING,
                        pattern=r"^[A-Z][a-zA-Z0-9]*$",
                        message="Class names should use PascalCase",
                        category="naming",
                        auto_fix=True
                    ),
                    CodeRule(
                        id="python_function_length",
                        name="Function Length",
                        description="Functions should not exceed 50 lines",
                        language=Language.PYTHON,
                        severity=Severity.WARNING,
                        pattern="50",
                        message="Function is too long, consider breaking it down",
                        category="complexity",
                        auto_fix=False
                    ),
                    CodeRule(
                        id="python_class_length",
                        name="Class Length",
                        description="Classes should not exceed 20 methods",
                        language=Language.PYTHON,
                        severity=Severity.WARNING,
                        pattern="20",
                        message="Class has too many methods, consider splitting",
                        category="complexity",
                        auto_fix=False
                    ),
                    CodeRule(
                        id="python_docstring",
                        name="Docstring Required",
                        description="Public functions and classes should have docstrings",
                        language=Language.PYTHON,
                        severity=Severity.INFO,
                        pattern="",
                        message="Missing docstring",
                        category="documentation",
                        auto_fix=False
                    ),
                    CodeRule(
                        id="python_magic_numbers",
                        name="Magic Numbers",
                        description="Avoid magic numbers, use named constants",
                        language=Language.PYTHON,
                        severity=Severity.WARNING,
                        pattern=r"^(0|1|2|3|4|5|6|7|8|9|10)$",
                        message="Consider using a named constant instead of magic number",
                        category="style",
                        auto_fix=False
                    )
                ]
            )
            
            self.standards[python_pep8.name] = python_pep8
            self.current_standard = python_pep8.name
            self.save_config()
    
    def add_standard(self, standard: CodeStandard):
        """Add a new code standard."""
        self.standards[standard.name] = standard
        self.save_config()
    
    def remove_standard(self, standard_name: str):
        """Remove a code standard."""
        if standard_name in self.standards:
            del self.standards[standard_name]
            if self.current_standard == standard_name:
                self.current_standard = list(self.standards.keys())[0] if self.standards else None
            self.save_config()
    
    def get_standards(self) -> List[CodeStandard]:
        """Get all code standards."""
        return list(self.standards.values())
    
    def get_current_standard(self) -> Optional[CodeStandard]:
        """Get the current active standard."""
        if self.current_standard and self.current_standard in self.standards:
            return self.standards[self.current_standard]
        return None
    
    def set_current_standard(self, standard_name: str):
        """Set the current active standard."""
        if standard_name in self.standards:
            self.current_standard = standard_name
            self.save_config()
    
    def analyze_file(self, file_path: str) -> CodeAnalysisResult:
        """Analyze a single file for code standard violations."""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Determine language from file extension
            language = self._detect_language(file_path)
            if not language:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
            
            # Get current standard
            standard = self.get_current_standard()
            if not standard:
                raise ValueError("No code standard configured")
            
            # Get rules for this language
            rules = [rule for rule in standard.rules if rule.language == language]
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            violations = []
            
            if language == Language.PYTHON:
                violations = self._analyze_python_file(content, rules, str(file_path))
            elif language == Language.JAVASCRIPT:
                violations = self._analyze_javascript_file(content, rules, str(file_path))
            elif language == Language.TYPESCRIPT:
                violations = self._analyze_typescript_file(content, rules, str(file_path))
            # Add more language analyzers as needed
            
            # Count violations by severity
            error_count = len([v for v in violations if v.severity == Severity.ERROR])
            warning_count = len([v for v in violations if v.severity == Severity.WARNING])
            info_count = len([v for v in violations if v.severity == Severity.INFO])
            auto_fixable_count = len([v for v in violations if v.auto_fixable])
            
            return CodeAnalysisResult(
                file_path=str(file_path),
                language=language,
                violations=violations,
                total_violations=len(violations),
                error_count=error_count,
                warning_count=warning_count,
                info_count=info_count,
                auto_fixable_count=auto_fixable_count
            )
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return CodeAnalysisResult(
                file_path=str(file_path),
                language=Language.PYTHON,
                violations=[],
                total_violations=0
            )
    
    def analyze_directory(self, directory_path: str) -> List[CodeAnalysisResult]:
        """Analyze all files in a directory for code standard violations."""
        results = []
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.error(f"Directory not found: {directory_path}")
            return results
        
        # Supported file extensions
        supported_extensions = {
            '.py': Language.PYTHON,
            '.js': Language.JAVASCRIPT,
            '.ts': Language.TYPESCRIPT,
            '.jsx': Language.JAVASCRIPT,
            '.tsx': Language.TYPESCRIPT,
            '.java': Language.JAVA,
            '.cpp': Language.CPP,
            '.cc': Language.CPP,
            '.cxx': Language.CPP,
            '.cs': Language.CSHARP,
            '.go': Language.GO,
            '.rs': Language.RUST,
            '.php': Language.PHP,
            '.rb': Language.RUBY
        }
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix in supported_extensions:
                try:
                    result = self.analyze_file(str(file_path))
                    if result.total_violations > 0:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Error analyzing {file_path}: {e}")
        
        return results
    
    def _detect_language(self, file_path: Path) -> Optional[Language]:
        """Detect programming language from file extension."""
        extension_map = {
            '.py': Language.PYTHON,
            '.js': Language.JAVASCRIPT,
            '.ts': Language.TYPESCRIPT,
            '.jsx': Language.JAVASCRIPT,
            '.tsx': Language.TYPESCRIPT,
            '.java': Language.JAVA,
            '.cpp': Language.CPP,
            '.cc': Language.CPP,
            '.cxx': Language.CPP,
            '.cs': Language.CSHARP,
            '.go': Language.GO,
            '.rs': Language.RUST,
            '.php': Language.PHP,
            '.rb': Language.RUBY
        }
        
        return extension_map.get(file_path.suffix.lower())
    
    def _analyze_python_file(self, content: str, rules: List[CodeRule], file_path: str) -> List[CodeViolation]:
        """Analyze Python file using AST."""
        try:
            tree = ast.parse(content)
            visitor = PythonASTVisitor(rules, file_path)
            visitor.visit(tree)
            return visitor.violations
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error analyzing Python file {file_path}: {e}")
            return []
    
    def _analyze_javascript_file(self, content: str, rules: List[CodeRule], file_path: str) -> List[CodeViolation]:
        """Analyze JavaScript file using regex patterns."""
        violations = []
        lines = content.split('\n')
        
        for rule in rules:
            if rule.language == Language.JAVASCRIPT and rule.enabled:
                for line_num, line in enumerate(lines, 1):
                    if re.search(rule.pattern, line):
                        violation = CodeViolation(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            severity=rule.severity,
                            message=rule.message,
                            line_number=line_num,
                            column=0,
                            line_content=line.strip(),
                            file_path=file_path,
                            category=rule.category,
                            auto_fixable=rule.auto_fix,
                            suggested_fix=rule.fix_template
                        )
                        violations.append(violation)
        
        return violations
    
    def _analyze_typescript_file(self, content: str, rules: List[CodeRule], file_path: str) -> List[CodeViolation]:
        """Analyze TypeScript file using regex patterns."""
        # Similar to JavaScript for now
        return self._analyze_javascript_file(content, rules, file_path)
    
    def auto_fix_violations(self, violations: List[CodeViolation]) -> List[CodeViolation]:
        """Automatically fix violations where possible."""
        fixed_violations = []
        
        for violation in violations:
            if violation.auto_fixable and violation.suggested_fix:
                # Apply the suggested fix
                # This is a simplified implementation
                fixed_violations.append(violation)
            else:
                fixed_violations.append(violation)
        
        return fixed_violations
    
    def export_standard(self, standard_name: str, export_path: str):
        """Export a code standard to a file."""
        if standard_name not in self.standards:
            raise ValueError(f"Standard '{standard_name}' not found")
        
        standard = self.standards[standard_name]
        
        try:
            with open(export_path, 'w') as f:
                json.dump(standard.__dict__, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error exporting standard: {e}")
            raise
    
    def import_standard(self, import_path: str):
        """Import a code standard from a file."""
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)
            
            # Convert data to CodeStandard object
            languages = [Language(lang) for lang in data.get("languages", [])]
            data["languages"] = languages
            
            rules = []
            for rule_data in data.get("rules", []):
                rule_data["language"] = Language(rule_data["language"])
                rule_data["severity"] = Severity(rule_data["severity"])
                rules.append(CodeRule(**rule_data))
            data["rules"] = rules
            
            standard = CodeStandard(**data)
            self.standards[standard.name] = standard
            self.save_config()
            
        except Exception as e:
            logger.error(f"Error importing standard: {e}")
            raise


# Global instance
code_standards_service = CodeStandardsService() 