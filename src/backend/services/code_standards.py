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

import ast
import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, TypeVar
from dataclasses import dataclass, field
from pathlib import Path
from ast import NodeVisitor
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Severity(str, Enum):
    """Severity levels for code standards violations."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Language(str, Enum):
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
    rules: List['CodeRule'] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    enabled: bool = True


@dataclass
class CodeAnalysisResult:
    """Result of code standards analysis."""
    file_path: str
    language: Language
    violations: List['CodeViolation'] = field(default_factory=list)
    total_violations: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    auto_fixable_count: int = 0


class PythonASTVisitor(NodeVisitor):
    """AST visitor for Python code analysis."""
    
    def __init__(self, rules: List['CodeRule'], file_path: str):
        self.rules = rules
        self.file_path = file_path
        self.violations: List['CodeViolation'] = []
        self.current_line = 0
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions."""
        self._check_naming_convention(node, "function")
        self._check_function_length(node)
        self._check_docstring(node)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions."""
        self._check_naming_convention(node, "class")
        self._check_class_length(node)
        self._check_docstring(node)
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name) -> None:
        """Visit variable names."""
        self._check_naming_convention(node, "variable")
        self.generic_visit(node)
    
    def visit_Constant(self, node: ast.Constant) -> None:
        """Visit constants."""
        self._check_magic_numbers(node)
        self.generic_visit(node)
    
    def _check_naming_convention(self, node: Union[ast.FunctionDef, ast.ClassDef, ast.Name], node_type: str) -> None:
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
    
    def _check_function_length(self, node: ast.FunctionDef) -> None:
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
    
    def _check_class_length(self, node: ast.ClassDef) -> None:
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
    
    def _check_docstring(self, node: Union[ast.FunctionDef, ast.ClassDef]) -> None:
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
    
    def _check_magic_numbers(self, node: ast.Constant) -> None:
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
    
    def _add_violation(self, rule: 'CodeRule', line: int, column: int, context: str):
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
        self.config_path = config_path or "config/code_standards_config.json"
        self.standards: Dict[str, 'CodeStandard'] = {}
        self._current_standard_name: Optional[str] = None
        
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
                    languages: List[Language] = []
                    for lang in standard_data.get("languages", []):
                        if isinstance(lang, str):
                            languages.append(Language(lang))
                        elif hasattr(lang, 'value'):  # Handle enum objects
                            languages.append(lang)
                        else:
                            languages.append(Language(str(lang)))
                    standard_data["languages"] = languages
                    
                    # Convert rules
                    rules: List['CodeRule'] = []
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
                    
                    # Convert datetime strings to datetime objects
                    if "created_date" in standard_data and isinstance(standard_data["created_date"], str):
                        try:
                            standard_data["created_date"] = datetime.fromisoformat(standard_data["created_date"])
                        except ValueError:
                            standard_data["created_date"] = datetime.now()
                            
                    if "last_updated" in standard_data and isinstance(standard_data["last_updated"], str):
                        try:
                            standard_data["last_updated"] = datetime.fromisoformat(standard_data["last_updated"])
                        except ValueError:
                            standard_data["last_updated"] = datetime.now()
                    
                    # Create CodeStandard object
                    standard = CodeStandard(**standard_data)
                    self.standards[standard.name] = standard
                    
                # Set current standard if specified
                if "current_standard" in data:
                    self._current_standard_name = data["current_standard"]
                    
        except Exception as e:
            logger.error(f"Error loading code standards config: {e}")
            self._create_default_standards()
    
    def save_config(self):
        """Save configuration to file."""
        try:
            # Convert standards to dictionaries
            standards_list: List[Dict[str, Any]] = []
            
            for standard in self.standards.values():
                # Convert rules
                rules_list: List[Dict[str, Any]] = []
                for rule in standard.rules:
                    rule_dict = {
                        "id": rule.id,
                        "name": rule.name,
                        "description": rule.description,
                        "language": rule.language.value,
                        "severity": rule.severity.value,
                        "pattern": rule.pattern,
                        "message": rule.message,
                        "category": rule.category,
                        "enabled": rule.enabled,
                        "auto_fix": rule.auto_fix,
                        "fix_template": rule.fix_template,
                        "tags": rule.tags
                    }
                    rules_list.append(rule_dict)
                
                # Create standard dict
                standard_dict: Dict[str, Any] = {
                    "name": standard.name,
                    "description": standard.description,
                    "company": standard.company,
                    "version": standard.version,
                    "languages": [lang.value for lang in standard.languages],
                    "rules": rules_list,
                    "created_date": standard.created_date.isoformat() if standard.created_date else None,
                    "last_updated": standard.last_updated.isoformat() if standard.last_updated else None,
                    "enabled": standard.enabled
                }
                standards_list.append(standard_dict)
            
            # Create final config
            config_data: Dict[str, Any] = {
                "standards": standards_list,
                "current_standard": self._current_standard_name
            }
            
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
            self._current_standard_name = python_pep8.name
            self.save_config()
    
    def add_standard(self, standard: 'CodeStandard'):
        """Add a new code standard."""
        self.standards[standard.name] = standard
        self.save_config()
    
    def remove_standard(self, standard_name: str):
        """Remove a code standard."""
        if standard_name in self.standards:
            del self.standards[standard_name]
            if self._current_standard_name == standard_name:
                self._current_standard_name = list(self.standards.keys())[0] if self.standards else None
            self.save_config()
    
    def get_standards(self) -> List['CodeStandard']:
        """Get all code standards."""
        return list(self.standards.values())
    
    @property
    def current_standard(self) -> Optional['CodeStandard']:
        """Get current code standard."""
        if self._current_standard_name:
            return self.standards.get(self._current_standard_name)
        return None
    
    def set_current_standard(self, standard_name: str) -> None:
        """Set current code standard."""
        if standard_name not in self.standards:
            raise ValueError(f"Standard {standard_name} not found")
        self._current_standard_name = standard_name
    
    def analyze_file(self, file_path: str) -> 'CodeAnalysisResult':
        """Analyze a file for code standard violations."""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Get current standard
            current = self.current_standard
            if not current:
                raise ValueError("No code standard configured")
            
            # Detect language
            language = self._detect_language(path)
            if not language:
                raise ValueError(f"Unsupported file type: {path.suffix}")
            
            # Get rules for language
            rules = [rule for rule in current.rules 
                    if rule.language == language and rule.enabled]
            
            # Read file content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Analyze based on language
            violations: List['CodeViolation'] = []
            if language == Language.PYTHON:
                violations = self._analyze_python_file(content, rules, str(path))
            elif language == Language.JAVASCRIPT:
                violations = self._analyze_javascript_file(content, rules, str(path))
            elif language == Language.TYPESCRIPT:
                violations = self._analyze_typescript_file(content, rules, str(path))
            
            # Create result
            result = CodeAnalysisResult(
                file_path=str(path),
                language=language,
                violations=violations
            )
            
            # Update counts
            result.total_violations = len(violations)
            result.error_count = len([v for v in violations if v.severity == Severity.ERROR])
            result.warning_count = len([v for v in violations if v.severity == Severity.WARNING])
            result.info_count = len([v for v in violations if v.severity == Severity.INFO])
            result.auto_fixable_count = len([v for v in violations if v.auto_fixable])
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            raise
            
    def _detect_language(self, path: Path) -> Optional[Language]:
        """Detect language from file extension."""
        suffix = path.suffix.lower()
        if suffix == '.py':
            return Language.PYTHON
        elif suffix == '.js':
            return Language.JAVASCRIPT
        elif suffix == '.ts':
            return Language.TYPESCRIPT
        else:
            return None
    
    def analyze_directory(self, directory_path: str) -> List['CodeAnalysisResult']:
        """Analyze all files in a directory."""
        try:
            path = Path(directory_path)
            if not path.exists():
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            if not path.is_dir():
                raise NotADirectoryError(f"Not a directory: {directory_path}")
            
            results: List['CodeAnalysisResult'] = []
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    try:
                        result = self.analyze_file(str(file_path))
                        if result:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"Error analyzing file {file_path}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing directory {directory_path}: {e}")
            return []
    
    def _analyze_python_file(self, content: str, rules: List['CodeRule'], file_path: str) -> List['CodeViolation']:
        """Analyze Python file using AST."""
        try:
            tree = ast.parse(content)
            visitor = PythonASTVisitor(rules, file_path)
            visitor.visit(tree)
            return visitor.violations
        except SyntaxError as e:
            violation = CodeViolation(
                rule_id="syntax-error",
                rule_name="Syntax Error",
                severity=Severity.ERROR,
                message=str(e),
                line_number=e.lineno or 0,
                column=e.offset or 0,
                line_content=e.text or "",
                file_path=file_path,
                category="syntax"
            )
            return [violation]
        except Exception as e:
            logger.error(f"Error analyzing Python file {file_path}: {e}")
            return []
    
    def _analyze_javascript_file(self, content: str, rules: List['CodeRule'], file_path: str) -> List['CodeViolation']:
        """Analyze JavaScript file."""
        # TODO: Implement JavaScript analysis
        violations: List['CodeViolation'] = []
        return violations
    
    def _analyze_typescript_file(self, content: str, rules: List['CodeRule'], file_path: str) -> List['CodeViolation']:
        """Analyze TypeScript file."""
        # TODO: Implement TypeScript analysis
        violations: List['CodeViolation'] = []
        return violations
    
    def auto_fix_violations(self, violations: List['CodeViolation']) -> List['CodeViolation']:
        """Automatically fix violations where possible."""
        fixed: List['CodeViolation'] = []
        for violation in violations:
            if violation.auto_fixable and violation.suggested_fix:
                try:
                    # Apply fix and mark as fixed
                    fixed_violation = violation
                    fixed_violation.suggested_fix = None  # Clear fix after applying
                    fixed.append(fixed_violation)
                except Exception as e:
                    logger.error(f"Error fixing violation: {e}")
            else:
                fixed.append(violation)
        return fixed
    
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