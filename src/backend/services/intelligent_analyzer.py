"""
intelligent_analyzer.py

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

import ast

# src/core/intelligent_analyzer.py
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import networkx as nx


class IssueType(Enum):
    LOGIC_ERROR = "logic_error"
    PERFORMANCE_ISSUE = "performance_issue"
    SECURITY_VULNERABILITY = "security_vulnerability"
    CODE_SMELL = "code_smell"
    MAINTAINABILITY_ISSUE = "maintainability_issue"
    DOCUMENTATION_ISSUE = "documentation_issue"
    BEST_PRACTICE_VIOLATION = "best_practice_violation"
    LINTER_ERROR = "linter_error"
    ARCHITECTURAL_ISSUE = "architectural_issue"
    DEPENDENCY_ISSUE = "dependency_issue"
    SEMANTIC_ISSUE = "semantic_issue"
    DATA_FLOW_ISSUE = "data_flow_issue"
    CODE_QUALITY = "code_quality"


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis."""

    file_path: str
    line_number: int
    issue_type: IssueType
    severity: str
    description: str
    code_snippet: str = ""
    suggestion: str = ""
    context: Optional[Dict[str, Any]] = None
    compliance_standards: Optional[List[str]] = None

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.context is None:
            self.context = {}


@dataclass
class CodePattern:
    name: str
    description: str
    pattern_type: str  # "anti_pattern", "design_pattern", "code_smell"
    severity: str
    confidence: float  # 0.0 to 1.0
    context: Optional[Dict[str, Any]] = None


class DependencyAnalyzer:
    """Analyze code dependencies and architectural relationships."""

    def __init__(self):
        self.dependency_graph = nx.DiGraph()
        self.circular_dependencies = []
        self.unused_dependencies = []

    def analyze_dependencies(self, project_path: str) -> List[CodeIssue]:
        """Analyze project dependencies."""
        issues = []

        # Build dependency graph
        self._build_dependency_graph(project_path)

        # Detect circular dependencies
        issues.extend(self._detect_circular_dependencies())

        # Detect unused dependencies
        issues.extend(self._detect_unused_dependencies())

        # Analyze dependency complexity
        issues.extend(self._analyze_dependency_complexity())

        return issues

    def _build_dependency_graph(self, project_path: str):
        """Build a graph of file dependencies."""
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".java")):
                    file_path = os.path.join(root, file)
                    self._analyze_file_dependencies(file_path)

    def _analyze_file_dependencies(self, file_path: str):
        """Analyze dependencies for a single file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract imports
            imports = self._extract_imports(file_path, content)

            # Add to dependency graph
            for imp in imports:
                self.dependency_graph.add_edge(file_path, imp)

        except Exception:
            pass

    def _extract_imports(self, file_path: str, content: str) -> List[str]:
        """Extract import statements from file content."""
        imports = []

        if file_path.endswith(".py"):
            # Python imports
            import_patterns = [
                r"import\s+(\w+)",
                r"from\s+(\w+)\s+import",
                r"from\s+(\w+\.\w+)\s+import",
            ]
        elif file_path.endswith((".js", ".ts")):
            # JavaScript/TypeScript imports
            import_patterns = [
                r'import\s+.*from\s+["\']([^"\']+)["\']',
                r'require\s*\(\s*["\']([^"\']+)["\']',
            ]

        for pattern in import_patterns:
            for match in re.finditer(pattern, content):
                imports.append(match.group(1))

        return imports

    def _detect_circular_dependencies(self) -> List[CodeIssue]:
        """Detect circular dependencies in the codebase."""
        issues = []

        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))

            for cycle in cycles:
                if len(cycle) > 1:  # Only report cycles with multiple files
                    issues.append(
                        CodeIssue(
                            file_path=cycle[0],
                            line_number=1,
                            issue_type=IssueType.ARCHITECTURAL_ISSUE,
                            severity="high",
                            description=f"Circular dependency detected involving {len(cycle)} files",
                            code_snippet=f"Files: {' -> '.join(cycle)}",
                            suggestion="Refactor to break the circular dependency by extracting common functionality.",
                        ))

        except Exception:
            pass

        return issues

    def _detect_unused_dependencies(self) -> List[CodeIssue]:
        """Detect unused dependencies."""
        issues = []

        # This would require more sophisticated analysis
        # For now, we'll provide a placeholder
        return issues

    def _analyze_dependency_complexity(self) -> List[CodeIssue]:
        """Analyze dependency complexity."""
        issues = []

        # Check for files with too many dependencies
        for node in self.dependency_graph.nodes():
            in_degree = self.dependency_graph.in_degree(node)
            out_degree = self.dependency_graph.out_degree(node)

            if in_degree > 10:
                issues.append(
                    CodeIssue(
                        file_path=node,
                        line_number=1,
                        issue_type=IssueType.ARCHITECTURAL_ISSUE,
                        severity="medium",
                        description=f"File has too many dependencies ({in_degree})",
                        code_snippet=f"Dependency count: {in_degree}",
                        suggestion="Consider breaking down the file into smaller, more focused modules.",
                    ))

        return issues


class PatternDetector:
    """Detect design patterns, anti-patterns, and architectural patterns."""

    def __init__(self):
        self.patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[str, List[Dict]]:
        """Initialize pattern detection rules."""
        return {
            "python": [
                # Design Patterns
                {
                    "name": "Singleton Pattern",
                    "pattern": r"class\s+\w+:\s*\n\s*_instance\s*=\s*None",
                    "type": "design_pattern",
                    "severity": "low",
                    "description": "Singleton pattern detected",
                },
                {
                    "name": "Factory Pattern",
                    "pattern": r"def\s+create_\w+\s*\([^)]*\):",
                    "type": "design_pattern",
                    "severity": "low",
                    "description": "Factory pattern detected",
                },
                # Anti-patterns
                {
                    "name": "God Object",
                    "pattern": r"class\s+\w+:\s*\n(?:.*\n){50,}",
                    "type": "anti_pattern",
                    "severity": "high",
                    "description": "God object anti-pattern detected",
                },
                {
                    "name": "Spaghetti Code",
                    "pattern": r"(?:if|for|while|try).*:\s*\n(?:.*\n){20,}",
                    "type": "anti_pattern",
                    "severity": "medium",
                    "description": "Complex nested control flow detected",
                },
            ],
            "javascript": [
                {
                    "name": "Callback Hell",
                    "pattern": r"\.then\([^)]*\)\.then\([^)]*\)\.then\([^)]*\)",
                    "type": "anti_pattern",
                    "severity": "medium",
                    "description": "Callback hell anti-pattern detected",
                },
                {
                    "name": "Global Variables",
                    "pattern": r"var\s+\w+\s*=\s*[^;]+;",
                    "type": "anti_pattern",
                    "severity": "medium",
                    "description": "Global variable usage detected",
                },
            ],
        }

    def detect_patterns(
        self, file_path: str, content: str, language: str
    ) -> List[CodePattern]:
        """Detect patterns in code."""
        patterns = []

        if language in self.patterns:
            for pattern_def in self.patterns[language]:
                matches = re.finditer(pattern_def["pattern"], content, re.MULTILINE)

                for match in matches:
                    line_num = content[: match.start()].count("\n") + 1

                    patterns.append(
                        CodePattern(
                            name=pattern_def["name"],
                            description=pattern_def["description"],
                            pattern_type=pattern_def["type"],
                            severity=pattern_def["severity"],
                            confidence=0.8,  # Could be improved with ML
                            context={"line": line_num, "match": match.group()},
                        )
                    )

        return patterns


class DataFlowAnalyzer:
    """Analyze data flow and variable usage patterns."""

    def __init__(self):
        self.variable_definitions = defaultdict(list)
        self.variable_usage = defaultdict(list)
        self.data_flows = defaultdict(list)

    def analyze_data_flow(
        self, file_path: str, content: str, language: str
    ) -> List[CodeIssue]:
        """Analyze data flow patterns."""
        issues = []

        if language == "python":
            issues.extend(self._analyze_python_data_flow(file_path, content))
        elif language in ["javascript", "typescript"]:
            issues.extend(self._analyze_js_data_flow(file_path, content))

        return issues

    def _analyze_python_data_flow(
        self, file_path: str, content: str
    ) -> List[CodeIssue]:
        """Analyze data flow in Python code."""
        issues = []

        try:
            tree = ast.parse(content)

            # Track variable definitions and usage
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.variable_definitions[target.id].append(node.lineno)

                elif isinstance(node, ast.Name):
                    if isinstance(node.ctx, ast.Load):
                        self.variable_usage[node.id].append(node.lineno)

            # Check for unused variables
            for var_name, definitions in self.variable_definitions.items():
                if var_name not in self.variable_usage and not var_name.startswith("_"):
                    issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=definitions[0],
                            issue_type=IssueType.SEMANTIC_ISSUE,
                            severity="low",
                            description=f"Unused variable: {var_name}",
                            code_snippet=f"Variable '{var_name}' is defined but never used",
                            suggestion="Remove the unused variable or use it in your code.",
                        ))

            # Check for undefined variables
            for var_name, usages in self.variable_usage.items():
                if (
                    var_name not in self.variable_definitions
                    and not var_name.startswith("_")
                ):
                    issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=usages[0],
                            issue_type=IssueType.LOGIC_ERROR,
                            severity="high",
                            description=f"Undefined variable: {var_name}",
                            code_snippet=f"Variable '{var_name}' is used but never defined",
                            suggestion="Define the variable before using it.",
                        ))

        except SyntaxError:
            pass

        return issues

    def _analyze_js_data_flow(self, file_path: str, content: str) -> List[CodeIssue]:
        """Analyze data flow in JavaScript/TypeScript code."""
        issues = []

        # Extract variable declarations and usage
        var_patterns = [
            (r"var\s+(\w+)", "var"),
            (r"let\s+(\w+)", "let"),
            (r"const\s+(\w+)", "const"),
            (r"function\s+(\w+)", "function"),
        ]

        variables = set()

        for pattern, var_type in var_patterns:
            for match in re.finditer(pattern, content):
                var_name = match.group(1)
                variables.add(var_name)

        # Check for undefined variables
        usage_pattern = r"\b(\w+)\b"
        for match in re.finditer(usage_pattern, content):
            var_name = match.group(1)
            if (
                var_name not in variables
                and not var_name.startswith("_")
                and var_name not in ["console", "window", "document", "this", "super"]
            ):

                line_num = content[: match.start()].count("\n") + 1
                issues.append(
                    CodeIssue(
                        file_path=file_path,
                        line_number=line_num,
                        issue_type=IssueType.LOGIC_ERROR,
                        severity="high",
                        description=f"Potentially undefined variable: {var_name}",
                        code_snippet=f"Variable '{var_name}' may be undefined",
                        suggestion="Ensure the variable is properly declared before use.",
                    ))

        return issues


class IntelligentCodeAnalyzer:
    """
    Intelligent code analyzer that combines multiple analysis techniques.
    Optimized with caching and lazy loading for better performance.
    """

    def __init__(self):
        self.cache = {}
        self.pattern_cache = {}
        self._load_patterns()

    def _load_patterns(self):
        """Load analysis patterns with caching."""
        if hasattr(self, "_patterns_loaded"):
            return

        # Cache common patterns for better performance
        self.pattern_cache = {
            "security": {
                "hardcoded_credentials": [
                    r'(?i)(password|secret|key|token)\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)(api_key|access_token|private_key)\s*=\s*["\"][^"\']+["\"]',
                ],
                "sql_injection": [
                    r'(?i)execute\s*\(\s*["\'][^"\']*\$[^"\']*["\']',
                    r'(?i)query\s*\(\s*["\'][^"\']*\$[^"\']*["\']',
                    r"(?i)(SELECT|INSERT|UPDATE|DELETE).*\+.*(input|request|user)",
                ],
                "xss_vulnerability": [
                    r"(?i)innerHTML\s*=\s*[^;]+",
                    r"(?i)document\.write\s*\(\s*[^)]+\)",
                    r"(?i)res\.send\s*\(.*req\.query",
                ],
                "command_injection": [
                    r"(?i)os\.system\s*\(.*input",
                    r"(?i)subprocess\.Popen\s*\(.*input",
                    r"(?i)system\s*\(.*user",
                ],
                "path_traversal": [
                    r"(?i)open\s*\(.*input",
                    r"(?i)readFile\s*\(.*user",
                    r"(?i)\.\./",
                ],
                "authentication_bypass": [
                    r"(?i)is_admin\s*\(\)\s*{\s*return\s*true",
                    r"(?i)admin\s*=\s*true",
                ],
                "insecure_crypto": [
                    r"(?i)md5\s*\(",
                    r"(?i)sha1\s*\(",
                    r"(?i)random\.random\s*\(",
                ],
                "weak_permissions": [
                    r"(?i)chmod\s*\(.*777",
                    r"(?i)os\.chmod\s*\(.*0o777",
                ],
                # OWASP/CWE/PCI mappings
                "owasp_a1_injection": [
                    r"(?i)execute\s*\(.*input",
                    r"(?i)eval\s*\(",
                ],
                "owasp_a2_broken_auth": [
                    r"(?i)login\s*\(.*\)",
                    r"(?i)auth\s*\(.*\)",
                ],
                "owasp_a3_sensitive_data": [
                    r"(?i)ssl_verify\s*=\s*false",
                    r"(?i)verify=False",
                ],
                "owasp_a5_broken_access": [
                    r'(?i)if\s+user\.role\s*==\s*["\"][a-z]+["\"]',
                ],
                "cwe_798_hardcoded_credential": [
                    r'(?i)password\s*=\s*["\"][^"\']+["\"]',
                ],
                "cwe_89_sql_injection": [
                    r"(?i)SELECT.*\+.*input",
                ],
                "pci_insecure_storage": [
                    r'(?i)card_number\s*=\s*["\"][^"\']+["\"]',
                ],
                # NIST, SOC2, ISO, HIPAA mappings (examples)
                "nist_ac_6_least_privilege": [
                    r"(?i)chmod\s*\(.*777",
                    r"(?i)os\.chmod\s*\(.*0o777",
                ],
                "soc2_encryption": [r"(?i)ssl_verify\s*=\s*false", r"(?i)verify=False"],
                "iso_27001_access_control": [
                    r'(?i)if\s+user\.role\s*==\s*["\"][a-z]+["\"]'
                ],
                "hipaa_phi_exposure": [r'(?i)patient_name\s*=\s*["\"][^"\']+["\"]'],
                # Additional top compliance standards
                "gdpr_data_protection": [
                    r'(?i)personal_data\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)email\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)phone\s*=\s*["\"][^"\']+["\"]',
                ],
                "sox_financial_controls": [
                    r'(?i)financial_data\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)account_balance\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)transaction_amount\s*=\s*["\"][^"\']+["\"]',
                ],
                "fedramp_cloud_security": [
                    r'(?i)cloud_credentials\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)aws_key\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)azure_key\s*=\s*["\"][^"\']+["\"]',
                ],
                "cis_controls": [
                    r'(?i)admin_password\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)root_password\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)default_password\s*=\s*["\"][^"\']+["\"]',
                ],
                "mitre_attack": [
                    r'(?i)backdoor\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)malware\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)exploit\s*=\s*["\"][^"\']+["\"]',
                ],
            },
            "performance": {
                "n_plus_one": [
                    r"(?i)for.*in.*:\s*\n\s*.*\.query\(",
                    r"(?i)foreach.*:\s*\n\s*.*\.find\(",
                ],
                "memory_leak": [
                    r"(?i)addEventListener.*function",
                    r"(?i)setInterval.*function",
                ],
            },
            "code_quality": {
                "magic_numbers": [
                    r"\b\d{3,}\b(?!\s*[a-zA-Z])",  # Numbers >= 100 not followed by text
                ],
                "long_functions": [
                    # Functions with 50+ lines
                    r"def\s+\w+\s*\([^)]*\):\s*\n(?:[^\n]*\n){50,}",
                ],
            },
        }

        self._patterns_loaded = True

    def analyze_file(
        self,
        file_path: str,
        language: str,
        linter_issues: Optional[List[Any]] = None,
        compliance: Optional[str] = None,
    ) -> List[CodeIssue]:
        """
        Analyze a file for code issues with optimized performance.
        Uses lazy loading and caching to improve speed.
        """
        # Check cache first
        cache_key = f"{file_path}_{language}_{hash(str(linter_issues))}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # Lazy load file content only when needed
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            issues = []

            # Process linter issues first (they're already parsed)
            if linter_issues:
                for linter_issue in linter_issues:
                    issues.append(
                        self._convert_linter_issue(linter_issue, file_path, language)
                    )

            # Add intelligent analysis issues
            intelligent_issues = self._analyze_content_intelligently(
                content, file_path, language
            )
            issues.extend(intelligent_issues)

            # Cache the results
            self.cache[cache_key] = issues

            # After collecting issues, filter by compliance if requested
            if compliance and compliance != "all":
                issues = self._filter_by_compliance(issues, compliance)
            return issues

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return []

    def _analyze_content_intelligently(
        self, content: str, file_path: str, language: str
    ) -> List[CodeIssue]:
        """Analyze content using intelligent patterns with optimized performance."""
        issues = []
        lines = content.split("\n")

        # Category to IssueType mapping
        category_to_issue_type = {
            "security": IssueType.SECURITY_VULNERABILITY,
            "performance": IssueType.PERFORMANCE_ISSUE,
            "code_quality": IssueType.CODE_QUALITY,
            "maintainability": IssueType.MAINTAINABILITY_ISSUE,
            "documentation": IssueType.DOCUMENTATION_ISSUE,
            "best_practice": IssueType.BEST_PRACTICE_VIOLATION,
            "logic": IssueType.LOGIC_ERROR,
            "semantic": IssueType.SEMANTIC_ISSUE,
            "data_flow": IssueType.DATA_FLOW_ISSUE,
            "architectural": IssueType.ARCHITECTURAL_ISSUE,
            "dependency": IssueType.DEPENDENCY_ISSUE,
            "code_smell": IssueType.CODE_SMELL,
        }

        # Process patterns efficiently
        for category, patterns in self.pattern_cache.items():
            for pattern_name, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = re.finditer(pattern, content, re.MULTILINE)
                    for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        if line_num <= len(lines):
                            line_content = lines[line_num - 1].strip()

                            # Map category to IssueType
                            issue_type = category_to_issue_type.get(
                                category, IssueType.CODE_QUALITY
                            )

                            issue = CodeIssue(
                                file_path=file_path,
                                line_number=line_num,
                                description=self._get_issue_description(
                                    category, pattern_name
                                ),
                                code_snippet=line_content,
                                issue_type=issue_type,
                                severity=self._get_severity(category, pattern_name),
                                context={
                                    "pattern": pattern_name,
                                    "match": match.group(),
                                },
                                suggestion=self._get_suggestion_for_pattern(
                                    category, pattern_name
                                ),
                            )
                            issues.append(issue)

        return issues

    def _get_issue_description(self, category: str, pattern_name: str) -> str:
        """Get human-readable issue description."""
        descriptions = {
            "security": {
                "hardcoded_credentials": "Hardcoded credentials detected - use environment variables",
                "sql_injection": "Potential SQL injection vulnerability - use parameterized queries",
                "xss_vulnerability": "Potential XSS vulnerability - sanitize user input",
            },
            "performance": {
                "n_plus_one": "N+1 query problem detected - consider batch loading",
                "memory_leak": "Potential memory leak - ensure proper cleanup",
            },
            "code_quality": {
                "magic_numbers": "Magic number detected - consider using named constants",
                "long_functions": "Function is too long - consider breaking it down",
            },
        }

        return descriptions.get(category, {}).get(
            pattern_name, f"{category} issue: {pattern_name}"
        )

    def _get_severity(self, category: str, pattern_name: str) -> str:
        """Get severity level for the issue."""
        severity_map = {
            "security": "high",
            "performance": "medium",
            "code_quality": "low",
        }

        return severity_map.get(category, "medium")

    def _get_suggestion_for_pattern(self, category: str, pattern_name: str) -> str:
        """Get suggestion for the detected pattern."""
        suggestions = {
            "security": {
                "hardcoded_credentials": "Use environment variables instead of hardcoding credentials",
                "sql_injection": "Use parameterized queries to prevent SQL injection",
                "xss_vulnerability": "Sanitize user input to prevent XSS attacks",
            },
            "performance": {
                "n_plus_one": "Consider batch loading data to avoid N+1 queries",
                "memory_leak": "Ensure proper cleanup to avoid memory leaks",
            },
            "code_quality": {
                "magic_numbers": "Consider defining this as a named constant for better readability",
                "long_functions": "Consider breaking down the function into smaller, more focused functions",
            },
        }

        return suggestions.get(category, {}).get(
            pattern_name, "No specific suggestion available"
        )

    def _convert_linter_issue(
        self, linter_issue: dict, file_path: str, language: str
    ) -> CodeIssue:
        """Convert linter issue to CodeIssue format."""
        try:
            # Handle different linter issue formats
            if isinstance(linter_issue, dict):
                # Dictionary format
                line_number = linter_issue.get("line", 1)
                message = linter_issue.get("message", "Linter issue")
                code = linter_issue.get("code", "")
                linter_name = linter_issue.get("linter", "unknown")
            elif isinstance(linter_issue, str):
                # String format - try to parse it
                from .scanner import parse_linter_output

                parsed = parse_linter_output(linter_issue, language)
                if parsed:
                    line_number, message = parsed
                    code = ""
                    linter_name = "unknown"
                else:
                    # Fallback for unparseable strings
                    line_number = 1
                    message = linter_issue
                    code = ""
                    linter_name = "unknown"
            else:
                # Fallback for unknown formats
                line_number = 1
                message = str(linter_issue)
                code = ""
                linter_name = "unknown"

            return CodeIssue(
                file_path=file_path,
                line_number=line_number,
                description=message,
                code_snippet=code,
                issue_type=IssueType.CODE_QUALITY,
                severity="medium",
                context={"linter": linter_name},
                suggestion="Fix the linter error according to the language style guide",
            )
        except Exception as e:
            # Return a safe fallback issue
            return CodeIssue(
                file_path=file_path,
                line_number=1,
                description=f"Error processing linter issue: {e}",
                code_snippet="",
                issue_type=IssueType.CODE_QUALITY,
                severity="low",
                context={"linter": "error"},
                suggestion="Check the linter configuration and try again",
            )

    def analyze_project(self, project_path: str) -> List[CodeIssue]:
        """Analyze an entire project for code issues."""
        issues = []
        
        # Analyze project structure
        issues.extend(self._analyze_project_structure(project_path))
        
        # Analyze dependencies
        issues.extend(self._analyze_dependencies(project_path))
        
        # Analyze individual files
        for root, dirs, files in os.walk(project_path):
            # Skip common directories that shouldn't be analyzed
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}]
            
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.h')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        language = self._get_language_from_extension(file)
                        file_issues = self.analyze_file(file_path, language, content=content)
                        issues.extend(file_issues)
                    except Exception as e:
                        # Log error but continue with other files
                        print(f"Error analyzing {file_path}: {e}")
        
        return issues

    def perform_quick_scan(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Performs a quick, local scan of a file for common issues.
        This should not use an LLM and should be fast.
        """
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            language = self._get_language_from_extension(file_path)
            
            # Quick pattern-based checks
            for i, line in enumerate(lines, 1):
                line_issues = self._quick_line_analysis(line, i, language)
                issues.extend(line_issues)
            
            # Quick file-level checks
            file_issues = self._quick_file_analysis(content, file_path, language)
            issues.extend(file_issues)
            
        except Exception as e:
            issues.append({
                "line": 1,
                "issue": f"Error reading file: {e}",
                "severity": "error",
                "type": "file_error"
            })
        
        return issues

    def _quick_line_analysis(self, line: str, line_number: int, language: str) -> List[Dict[str, Any]]:
        """Quick analysis of a single line for common issues."""
        issues = []
        
        # Common patterns to check
        patterns = {
            "TODO": "Found 'TODO:' comment that should be addressed",
            "FIXME": "Found 'FIXME:' comment that needs attention",
            "HACK": "Found 'HACK:' comment indicating temporary workaround",
            "XXX": "Found 'XXX:' comment indicating problematic code",
            "print(": "Found print statement - consider using proper logging",
            "console.log(": "Found console.log statement - consider using proper logging",
            "debugger;": "Found debugger statement - remove before production",
            "pass": "Found empty pass statement - consider removing or adding implementation",
        }
        
        for pattern, message in patterns.items():
            if pattern in line:
                issues.append({
                    "line": line_number,
                    "issue": message,
                    "severity": "warning" if pattern in ["TODO", "FIXME", "HACK", "XXX"] else "info",
                    "type": "comment" if pattern in ["TODO", "FIXME", "HACK", "XXX"] else "code_smell",
                    "code_snippet": line.strip()
                })
        
        # Language-specific checks
        if language == "python":
            python_issues = self._quick_python_line_analysis(line, line_number)
            issues.extend(python_issues)
        elif language in ["javascript", "typescript"]:
            js_issues = self._quick_js_line_analysis(line, line_number)
            issues.extend(js_issues)
        
        return issues

    def _quick_python_line_analysis(self, line: str, line_number: int) -> List[Dict[str, Any]]:
        """Quick Python-specific line analysis."""
        issues = []
        
        # Python-specific patterns
        python_patterns = {
            "except:": "Bare except clause - specify exception type",
            "except Exception:": "Broad exception handling - consider specific exceptions",
            "import *": "Wildcard import - import specific modules",
            "from .* import *": "Wildcard import - import specific items",
            "global ": "Global variable usage - consider passing as parameter",
            "eval(": "eval() usage - security risk, consider alternatives",
            "exec(": "exec() usage - security risk, consider alternatives",
            "__import__(": "__import__() usage - security risk",
        }
        
        for pattern, message in python_patterns.items():
            if pattern in line:
                issues.append({
                    "line": line_number,
                    "issue": message,
                    "severity": "warning" if "security" in message else "info",
                    "type": "security" if "security" in message else "code_smell",
                    "code_snippet": line.strip()
                })
        
        return issues

    def _quick_js_line_analysis(self, line: str, line_number: int) -> List[Dict[str, Any]]:
        """Quick JavaScript/TypeScript-specific line analysis."""
        issues = []
        
        # JavaScript-specific patterns
        js_patterns = {
            "eval(": "eval() usage - security risk, consider alternatives",
            "innerHTML": "innerHTML usage - potential XSS risk",
            "document.write(": "document.write() usage - consider DOM manipulation",
            "var ": "var declaration - consider using let or const",
            "== ": "Loose equality - consider using === for type safety",
            "!= ": "Loose inequality - consider using !== for type safety",
        }
        
        for pattern, message in js_patterns.items():
            if pattern in line:
                issues.append({
                    "line": line_number,
                    "issue": message,
                    "severity": "warning" if "security" in message else "info",
                    "type": "security" if "security" in message else "code_smell",
                    "code_snippet": line.strip()
                })
        
        return issues

    def _quick_file_analysis(self, content: str, file_path: str, language: str) -> List[Dict[str, Any]]:
        """Quick file-level analysis."""
        issues = []
        
        # Check file size
        if len(content) > 10000:  # 10KB
            issues.append({
                "line": 1,
                "issue": "Large file detected - consider breaking into smaller modules",
                "severity": "info",
                "type": "maintainability",
                "code_snippet": f"File size: {len(content)} characters"
            })
        
        # Check for long lines
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append({
                    "line": i,
                    "issue": "Long line detected - consider breaking into multiple lines",
                    "severity": "info",
                    "type": "style",
                    "code_snippet": line[:50] + "..." if len(line) > 50 else line
                })
        
        # Check for missing docstrings (Python)
        if language == "python":
            if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
                # Check if there are functions/classes without docstrings
                if "def " in content or "class " in content:
                    issues.append({
                        "line": 1,
                        "issue": "Missing module docstring",
                        "severity": "info",
                        "type": "documentation",
                        "code_snippet": "Consider adding a module-level docstring"
                    })
        
        return issues

    def _get_language_from_extension(self, file_path: str) -> str:
        """Get language from file extension."""
        ext = file_path.lower().split('.')[-1]
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'h': 'c',
            'hpp': 'cpp'
        }
        return language_map.get(ext, 'unknown')

    def get_ai_enhancement(self, issue_description: str, file_path: str, line_number: int, language: str) -> Dict[str, Any]:
        """
        Gets a detailed analysis of a specific issue from an LLM.
        This is the slower, AI-powered analysis that should be called on-demand.
        """
        try:
            # Read the file content around the issue line
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Get context around the issue line
            start_line = max(0, line_number - 3)
            end_line = min(len(lines), line_number + 2)
            context_lines = lines[start_line:end_line]
            context = ''.join(context_lines)
            
            # Create a focused prompt for the AI
            prompt = f"""
            Analyze this code issue in detail:
            
            File: {file_path}
            Line: {line_number}
            Language: {language}
            Issue: {issue_description}
            
            Code context:
            {context}
            
            Please provide:
            1. Detailed explanation of the issue
            2. Why it's problematic
            3. Specific suggestions for improvement
            4. Code example of the fix
            5. Best practices to follow
            """
            
            # This would call the LLM manager
            # For now, return a structured response
            return {
                "detailed_analysis": f"AI analysis for: {issue_description}",
                "explanation": f"This issue at line {line_number} in {file_path} requires attention.",
                "suggestions": [
                    "Review the code for potential improvements",
                    "Consider following language-specific best practices",
                    "Add appropriate error handling if needed"
                ],
                "code_example": "# Example of improved code would go here",
                "best_practices": [
                    "Follow language-specific style guides",
                    "Use appropriate error handling",
                    "Consider security implications"
                ],
                "severity": "medium",
                "confidence": 0.8
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get AI enhancement: {e}",
                "detailed_analysis": "Unable to analyze due to error",
                "suggestions": ["Check file accessibility", "Verify file encoding"],
                "severity": "error"
            }
