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

# src/core/intelligent_analyzer.py
import os
import re
import ast
import json
import hashlib
from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, Counter
import networkx as nx
from pathlib import Path

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

class SemanticAnalyzer:
    """Advanced semantic analysis for understanding code meaning and relationships."""
    
    def __init__(self):
        self.function_signatures = {}
        self.variable_usage = defaultdict(list)
        self.data_flows = defaultdict(list)
        self.dependency_graph = nx.DiGraph()
        
    def analyze_semantics(self, file_path: str, content: str, language: str) -> List[CodeIssue]:
        """Perform semantic analysis of code."""
        issues = []
        
        if language == 'python':
            issues.extend(self._analyze_python_semantics(file_path, content))
        elif language in ['javascript', 'typescript']:
            issues.extend(self._analyze_js_semantics(file_path, content))
        
        return issues
    
    def _analyze_python_semantics(self, file_path: str, content: str) -> List[CodeIssue]:
        """Semantic analysis for Python code."""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            # Analyze function calls and their arguments
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    issues.extend(self._analyze_function_call(node, file_path))
                elif isinstance(node, ast.Assign):
                    issues.extend(self._analyze_assignment(node, file_path))
                elif isinstance(node, ast.Compare):
                    issues.extend(self._analyze_comparison(node, file_path))
                elif isinstance(node, ast.BoolOp):
                    issues.extend(self._analyze_boolean_logic(node, file_path))
        
        except SyntaxError:
            pass
        
        return issues
    
    def _analyze_function_call(self, node: ast.Call, file_path: str) -> List[CodeIssue]:
        """Analyze function calls for semantic issues."""
        issues = []
        
        # Check for suspicious function calls
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            # Security-sensitive functions
            if func_name in ['eval', 'exec', 'input']:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=node.lineno,
                    issue_type=IssueType.SECURITY_VULNERABILITY,
                    severity="high",
                    description=f"Use of potentially dangerous function: {func_name}",
                    code_snippet=ast.unparse(node),
                    suggestion=f"Consider using safer alternatives to {func_name}."
                ))
            
            # Performance-sensitive functions
            if func_name in ['sleep']:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=node.lineno,
                    issue_type=IssueType.PERFORMANCE_ISSUE,
                    severity="medium",
                    description=f"Blocking call detected: {func_name}",
                    code_snippet=ast.unparse(node),
                    suggestion="Consider using async/await or non-blocking alternatives."
                ))
        
        # Check for attribute calls (e.g., time.sleep)
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                module_name = node.func.value.id
                func_name = node.func.attr
                
                # Performance-sensitive functions
                if module_name == 'time' and func_name == 'sleep':
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type=IssueType.PERFORMANCE_ISSUE,
                        severity="medium",
                        description=f"Blocking call detected: {module_name}.{func_name}",
                        code_snippet=ast.unparse(node),
                        suggestion="Consider using async/await or non-blocking alternatives."
                    ))
        
        return issues
    
    def _analyze_assignment(self, node: ast.Assign, file_path: str) -> List[CodeIssue]:
        """Analyze assignments for semantic issues."""
        issues = []
        
        # Check for unused variables
        for target in node.targets:
            if isinstance(target, ast.Name):
                # This would require tracking variable usage across the file
                pass
        
        return issues
    
    def _analyze_comparison(self, node: ast.Compare, file_path: str) -> List[CodeIssue]:
        """Analyze comparisons for semantic issues."""
        issues = []
        
        # Check for suspicious comparisons
        for op, comparator in zip(node.ops, node.comparators):
            if isinstance(op, ast.Eq) and isinstance(comparator, ast.Constant):
                if comparator.value is None:
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type=IssueType.SEMANTIC_ISSUE,
                        severity="low",
                        description="Comparison with None using == instead of 'is'",
                        code_snippet=ast.unparse(node),
                        suggestion="Use 'is None' instead of '== None' for identity comparison."
                    ))
        
        return issues
    
    def _analyze_boolean_logic(self, node: ast.BoolOp, file_path: str) -> List[CodeIssue]:
        """Analyze boolean logic for semantic issues."""
        issues = []
        
        # Check for redundant boolean expressions
        if isinstance(node.op, ast.And):
            for value in node.values:
                if isinstance(value, ast.Constant) and value.value is True:
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type=IssueType.SEMANTIC_ISSUE,
                        severity="low",
                        description="Redundant True in AND expression",
                        code_snippet=ast.unparse(node),
                        suggestion="Remove redundant True from boolean expression."
                    ))
        
        return issues
    
    def _analyze_js_semantics(self, file_path: str, content: str) -> List[CodeIssue]:
        """Semantic analysis for JavaScript/TypeScript code."""
        issues = []
        
        # Check for common JavaScript semantic issues
        patterns = [
            (r'==\s*null', "Use === null for null comparison"),
            (r'==\s*undefined', "Use === undefined for undefined comparison"),
            (r'console\.log', "Consider removing console.log statements in production"),
            (r'debugger;', "Remove debugger statements before production"),
        ]
        
        for pattern, suggestion in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=line_number,
                    issue_type=IssueType.CODE_SMELL,
                    severity="low",
                    description=f"Semantic issue: {suggestion}",
                    code_snippet=match.group(),
                    suggestion=suggestion
                ))
        
        return issues

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
                if file.endswith(('.py', '.js', '.ts', '.java')):
                    file_path = os.path.join(root, file)
                    self._analyze_file_dependencies(file_path)
    
    def _analyze_file_dependencies(self, file_path: str):
        """Analyze dependencies for a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
        
        if file_path.endswith('.py'):
            # Python imports
            import_patterns = [
                r'import\s+(\w+)',
                r'from\s+(\w+)\s+import',
                r'from\s+(\w+\.\w+)\s+import'
            ]
        elif file_path.endswith(('.js', '.ts')):
            # JavaScript/TypeScript imports
            import_patterns = [
                r'import\s+.*from\s+["\']([^"\']+)["\']',
                r'require\s*\(\s*["\']([^"\']+)["\']'
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
                    issues.append(CodeIssue(
                        file_path=cycle[0],
                        line_number=1,
                        issue_type=IssueType.ARCHITECTURAL_ISSUE,
                        severity="high",
                        description=f"Circular dependency detected involving {len(cycle)} files",
                        code_snippet=f"Files: {' -> '.join(cycle)}",
                        suggestion="Refactor to break the circular dependency by extracting common functionality."
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
                issues.append(CodeIssue(
                    file_path=node,
                    line_number=1,
                    issue_type=IssueType.ARCHITECTURAL_ISSUE,
                    severity="medium",
                    description=f"File has too many dependencies ({in_degree})",
                    code_snippet=f"Dependency count: {in_degree}",
                    suggestion="Consider breaking down the file into smaller, more focused modules."
                ))
        
        return issues

class PatternDetector:
    """Detect design patterns, anti-patterns, and architectural patterns."""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        
    def _initialize_patterns(self) -> Dict[str, List[Dict]]:
        """Initialize pattern detection rules."""
        return {
            'python': [
                # Design Patterns
                {
                    'name': 'Singleton Pattern',
                    'pattern': r'class\s+\w+:\s*\n\s*_instance\s*=\s*None',
                    'type': 'design_pattern',
                    'severity': 'low',
                    'description': 'Singleton pattern detected'
                },
                {
                    'name': 'Factory Pattern',
                    'pattern': r'def\s+create_\w+\s*\([^)]*\):',
                    'type': 'design_pattern',
                    'severity': 'low',
                    'description': 'Factory pattern detected'
                },
                # Anti-patterns
                {
                    'name': 'God Object',
                    'pattern': r'class\s+\w+:\s*\n(?:.*\n){50,}',
                    'type': 'anti_pattern',
                    'severity': 'high',
                    'description': 'God object anti-pattern detected'
                },
                {
                    'name': 'Spaghetti Code',
                    'pattern': r'(?:if|for|while|try).*:\s*\n(?:.*\n){20,}',
                    'type': 'anti_pattern',
                    'severity': 'medium',
                    'description': 'Complex nested control flow detected'
                }
            ],
            'javascript': [
                {
                    'name': 'Callback Hell',
                    'pattern': r'\.then\([^)]*\)\.then\([^)]*\)\.then\([^)]*\)',
                    'type': 'anti_pattern',
                    'severity': 'medium',
                    'description': 'Callback hell anti-pattern detected'
                },
                {
                    'name': 'Global Variables',
                    'pattern': r'var\s+\w+\s*=\s*[^;]+;',
                    'type': 'anti_pattern',
                    'severity': 'medium',
                    'description': 'Global variable usage detected'
                }
            ]
        }
    
    def detect_patterns(self, file_path: str, content: str, language: str) -> List[CodePattern]:
        """Detect patterns in code."""
        patterns = []
        
        if language in self.patterns:
            for pattern_def in self.patterns[language]:
                matches = re.finditer(pattern_def['pattern'], content, re.MULTILINE)
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    patterns.append(CodePattern(
                        name=pattern_def['name'],
                        description=pattern_def['description'],
                        pattern_type=pattern_def['type'],
                        severity=pattern_def['severity'],
                        confidence=0.8,  # Could be improved with ML
                        context={'line': line_num, 'match': match.group()}
                    ))
        
        return patterns

class DataFlowAnalyzer:
    """Analyze data flow and variable usage patterns."""
    
    def __init__(self):
        self.variable_definitions = defaultdict(list)
        self.variable_usage = defaultdict(list)
        self.data_flows = defaultdict(list)
        
    def analyze_data_flow(self, file_path: str, content: str, language: str) -> List[CodeIssue]:
        """Analyze data flow patterns."""
        issues = []
        
        if language == 'python':
            issues.extend(self._analyze_python_data_flow(file_path, content))
        elif language in ['javascript', 'typescript']:
            issues.extend(self._analyze_js_data_flow(file_path, content))
        
        return issues
    
    def _analyze_python_data_flow(self, file_path: str, content: str) -> List[CodeIssue]:
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
                if var_name not in self.variable_usage and not var_name.startswith('_'):
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=definitions[0],
                        issue_type=IssueType.SEMANTIC_ISSUE,
                        severity="low",
                        description=f"Unused variable: {var_name}",
                        code_snippet=f"Variable '{var_name}' is defined but never used",
                        suggestion="Remove the unused variable or use it in your code."
                    ))
            
            # Check for undefined variables
            for var_name, usages in self.variable_usage.items():
                if var_name not in self.variable_definitions and not var_name.startswith('_'):
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=usages[0],
                        issue_type=IssueType.LOGIC_ERROR,
                        severity="high",
                        description=f"Undefined variable: {var_name}",
                        code_snippet=f"Variable '{var_name}' is used but never defined",
                        suggestion="Define the variable before using it."
                    ))
        
        except SyntaxError:
            pass
        
        return issues
    
    def _analyze_js_data_flow(self, file_path: str, content: str) -> List[CodeIssue]:
        """Analyze data flow in JavaScript/TypeScript code."""
        issues = []
        
        # Extract variable declarations and usage
        var_patterns = [
            (r'var\s+(\w+)', 'var'),
            (r'let\s+(\w+)', 'let'),
            (r'const\s+(\w+)', 'const'),
            (r'function\s+(\w+)', 'function')
        ]
        
        variables = set()
        
        for pattern, var_type in var_patterns:
            for match in re.finditer(pattern, content):
                var_name = match.group(1)
                variables.add(var_name)
        
        # Check for undefined variables
        usage_pattern = r'\b(\w+)\b'
        for match in re.finditer(usage_pattern, content):
            var_name = match.group(1)
            if (var_name not in variables and 
                not var_name.startswith('_') and 
                var_name not in ['console', 'window', 'document', 'this', 'super']):
                
                line_num = content[:match.start()].count('\n') + 1
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=line_num,
                    issue_type=IssueType.LOGIC_ERROR,
                    severity="high",
                    description=f"Potentially undefined variable: {var_name}",
                    code_snippet=f"Variable '{var_name}' may be undefined",
                    suggestion="Ensure the variable is properly declared before use."
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
        if hasattr(self, '_patterns_loaded'):
            return
        
        # Cache common patterns for better performance
        self.pattern_cache = {
            'security': {
                'hardcoded_credentials': [
                    r'(?i)(password|secret|key|token)\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)(api_key|access_token|private_key)\s*=\s*["\"][^"\']+["\"]',
                ],
                'sql_injection': [
                    r'(?i)execute\s*\(\s*["\'][^"\']*\$[^"\']*["\']',
                    r'(?i)query\s*\(\s*["\'][^"\']*\$[^"\']*["\']',
                    r'(?i)(SELECT|INSERT|UPDATE|DELETE).*\+.*(input|request|user)',
                ],
                'xss_vulnerability': [
                    r'(?i)innerHTML\s*=\s*[^;]+',
                    r'(?i)document\.write\s*\(\s*[^)]+\)',
                    r'(?i)res\.send\s*\(.*req\.query',
                ],
                'command_injection': [
                    r'(?i)os\.system\s*\(.*input',
                    r'(?i)subprocess\.Popen\s*\(.*input',
                    r'(?i)system\s*\(.*user',
                ],
                'path_traversal': [
                    r'(?i)open\s*\(.*input',
                    r'(?i)readFile\s*\(.*user',
                    r'(?i)\.\./',
                ],
                'authentication_bypass': [
                    r'(?i)is_admin\s*\(\)\s*{\s*return\s*true',
                    r'(?i)admin\s*=\s*true',
                ],
                'insecure_crypto': [
                    r'(?i)md5\s*\(',
                    r'(?i)sha1\s*\(',
                    r'(?i)random\.random\s*\(',
                ],
                'weak_permissions': [
                    r'(?i)chmod\s*\(.*777',
                    r'(?i)os\.chmod\s*\(.*0o777',
                ],
                # OWASP/CWE/PCI mappings
                'owasp_a1_injection': [
                    r'(?i)execute\s*\(.*input',
                    r'(?i)eval\s*\(',
                ],
                'owasp_a2_broken_auth': [
                    r'(?i)login\s*\(.*\)',
                    r'(?i)auth\s*\(.*\)',
                ],
                'owasp_a3_sensitive_data': [
                    r'(?i)ssl_verify\s*=\s*false',
                    r'(?i)verify=False',
                ],
                'owasp_a5_broken_access': [
                    r'(?i)if\s+user\.role\s*==\s*["\"][a-z]+["\"]',
                ],
                'cwe_798_hardcoded_credential': [
                    r'(?i)password\s*=\s*["\"][^"\']+["\"]',
                ],
                'cwe_89_sql_injection': [
                    r'(?i)SELECT.*\+.*input',
                ],
                'pci_insecure_storage': [
                    r'(?i)card_number\s*=\s*["\"][^"\']+["\"]',
                ],
                # NIST, SOC2, ISO, HIPAA mappings (examples)
                'nist_ac_6_least_privilege': [r'(?i)chmod\s*\(.*777', r'(?i)os\.chmod\s*\(.*0o777'],
                'soc2_encryption': [r'(?i)ssl_verify\s*=\s*false', r'(?i)verify=False'],
                'iso_27001_access_control': [r'(?i)if\s+user\.role\s*==\s*["\"][a-z]+["\"]'],
                'hipaa_phi_exposure': [r'(?i)patient_name\s*=\s*["\"][^"\']+["\"]'],
                # Additional top compliance standards
                'gdpr_data_protection': [
                    r'(?i)personal_data\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)email\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)phone\s*=\s*["\"][^"\']+["\"]',
                ],
                'sox_financial_controls': [
                    r'(?i)financial_data\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)account_balance\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)transaction_amount\s*=\s*["\"][^"\']+["\"]',
                ],
                'fedramp_cloud_security': [
                    r'(?i)cloud_credentials\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)aws_key\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)azure_key\s*=\s*["\"][^"\']+["\"]',
                ],
                'cis_controls': [
                    r'(?i)admin_password\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)root_password\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)default_password\s*=\s*["\"][^"\']+["\"]',
                ],
                'mitre_attack': [
                    r'(?i)backdoor\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)malware\s*=\s*["\"][^"\']+["\"]',
                    r'(?i)exploit\s*=\s*["\"][^"\']+["\"]',
                ],
            },
            'performance': {
                'n_plus_one': [
                    r'(?i)for.*in.*:\s*\n\s*.*\.query\(',
                    r'(?i)foreach.*:\s*\n\s*.*\.find\(',
                ],
                'memory_leak': [
                    r'(?i)addEventListener.*function',
                    r'(?i)setInterval.*function',
                ]
            },
            'code_quality': {
                'magic_numbers': [
                    r'\b\d{3,}\b(?!\s*[a-zA-Z])',  # Numbers >= 100 not followed by text
                ],
                'long_functions': [
                    r'def\s+\w+\s*\([^)]*\):\s*\n(?:[^\n]*\n){50,}',  # Functions with 50+ lines
                ]
            }
        }
        
        self._patterns_loaded = True
    
    def analyze_file(self, file_path: str, language: str, linter_issues: Optional[List[Any]] = None, compliance: Optional[str] = None) -> List[CodeIssue]:
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
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            issues = []
            
            # Process linter issues first (they're already parsed)
            if linter_issues:
                for linter_issue in linter_issues:
                    issues.append(self._convert_linter_issue(linter_issue, file_path, language))
            
            # Add intelligent analysis issues
            intelligent_issues = self._analyze_content_intelligently(content, file_path, language)
            issues.extend(intelligent_issues)
            
            # Cache the results
            self.cache[cache_key] = issues
            
            # After collecting issues, filter by compliance if requested
            if compliance and compliance != 'all':
                issues = self._filter_by_compliance(issues, compliance)
            return issues
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return []
    
    def _analyze_content_intelligently(self, content: str, file_path: str, language: str) -> List[CodeIssue]:
        """Analyze content using intelligent patterns with optimized performance."""
        issues = []
        lines = content.split('\n')
        
        # Category to IssueType mapping
        category_to_issue_type = {
            'security': IssueType.SECURITY_VULNERABILITY,
            'performance': IssueType.PERFORMANCE_ISSUE,
            'code_quality': IssueType.CODE_QUALITY,
            'maintainability': IssueType.MAINTAINABILITY_ISSUE,
            'documentation': IssueType.DOCUMENTATION_ISSUE,
            'best_practice': IssueType.BEST_PRACTICE_VIOLATION,
            'logic': IssueType.LOGIC_ERROR,
            'semantic': IssueType.SEMANTIC_ISSUE,
            'data_flow': IssueType.DATA_FLOW_ISSUE,
            'architectural': IssueType.ARCHITECTURAL_ISSUE,
            'dependency': IssueType.DEPENDENCY_ISSUE,
            'code_smell': IssueType.CODE_SMELL
        }
        
        # Process patterns efficiently
        for category, patterns in self.pattern_cache.items():
            for pattern_name, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = re.finditer(pattern, content, re.MULTILINE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        if line_num <= len(lines):
                            line_content = lines[line_num - 1].strip()
                            
                            # Map category to IssueType
                            issue_type = category_to_issue_type.get(category, IssueType.CODE_QUALITY)
                            
                            issue = CodeIssue(
                                file_path=file_path,
                                line_number=line_num,
                                description=self._get_issue_description(category, pattern_name),
                                code_snippet=line_content,
                                issue_type=issue_type,
                                severity=self._get_severity(category, pattern_name),
                                context={'pattern': pattern_name, 'match': match.group()},
                                suggestion=self._get_suggestion_for_pattern(category, pattern_name)
                            )
                            issues.append(issue)
        
        return issues
    
    def _get_issue_description(self, category: str, pattern_name: str) -> str:
        """Get human-readable issue description."""
        descriptions = {
            'security': {
                'hardcoded_credentials': 'Hardcoded credentials detected - use environment variables',
                'sql_injection': 'Potential SQL injection vulnerability - use parameterized queries',
                'xss_vulnerability': 'Potential XSS vulnerability - sanitize user input',
            },
            'performance': {
                'n_plus_one': 'N+1 query problem detected - consider batch loading',
                'memory_leak': 'Potential memory leak - ensure proper cleanup',
            },
            'code_quality': {
                'magic_numbers': 'Magic number detected - consider using named constants',
                'long_functions': 'Function is too long - consider breaking it down',
            }
        }
        
        return descriptions.get(category, {}).get(pattern_name, f'{category} issue: {pattern_name}')
    
    def _get_severity(self, category: str, pattern_name: str) -> str:
        """Get severity level for the issue."""
        severity_map = {
            'security': 'high',
            'performance': 'medium',
            'code_quality': 'low'
        }
        
        return severity_map.get(category, 'medium')
    
    def _get_suggestion_for_pattern(self, category: str, pattern_name: str) -> str:
        """Get suggestion for the detected pattern."""
        suggestions = {
            'security': {
                'hardcoded_credentials': 'Use environment variables instead of hardcoding credentials',
                'sql_injection': 'Use parameterized queries to prevent SQL injection',
                'xss_vulnerability': 'Sanitize user input to prevent XSS attacks',
            },
            'performance': {
                'n_plus_one': 'Consider batch loading data to avoid N+1 queries',
                'memory_leak': 'Ensure proper cleanup to avoid memory leaks',
            },
            'code_quality': {
                'magic_numbers': 'Consider defining this as a named constant for better readability',
                'long_functions': 'Consider breaking down the function into smaller, more focused functions',
            }
        }
        
        return suggestions.get(category, {}).get(pattern_name, "No specific suggestion available")
    
    def _convert_linter_issue(self, linter_issue: dict, file_path: str, language: str) -> CodeIssue:
        """Convert linter issue to CodeIssue format."""
        try:
            # Handle different linter issue formats
            if isinstance(linter_issue, dict):
                # Dictionary format
                line_number = linter_issue.get('line', 1)
                message = linter_issue.get('message', 'Linter issue')
                code = linter_issue.get('code', '')
                linter_name = linter_issue.get('linter', 'unknown')
            elif isinstance(linter_issue, str):
                # String format - try to parse it
                from .scanner import parse_linter_output
                parsed = parse_linter_output(linter_issue, language)
                if parsed:
                    line_number, message = parsed
                    code = ''
                    linter_name = 'unknown'
                else:
                    # Fallback for unparseable strings
                    line_number = 1
                    message = linter_issue
                    code = ''
                    linter_name = 'unknown'
            else:
                # Fallback for unknown formats
                line_number = 1
                message = str(linter_issue)
                code = ''
                linter_name = 'unknown'
            
            return CodeIssue(
                file_path=file_path,
                line_number=line_number,
                description=message,
                code_snippet=code,
                issue_type=IssueType.CODE_QUALITY,
                severity='medium',
                context={'linter': linter_name},
                suggestion='Fix the linter error according to the language style guide'
            )
        except Exception as e:
            # Return a safe fallback issue
            return CodeIssue(
                file_path=file_path,
                line_number=1,
                description=f"Error processing linter issue: {e}",
                code_snippet="",
                issue_type=IssueType.CODE_QUALITY,
                severity='low',
                context={'linter': 'error'},
                suggestion='Check the linter configuration and try again'
            )

    def analyze_project(self, project_path: str) -> List[CodeIssue]:
        """
        Analyze entire project for architectural and dependency issues.
        """
        issues = []
        
        # Analyze dependencies
        issues.extend(self._analyze_dependencies(project_path))
        
        # Analyze project structure
        issues.extend(self._analyze_project_structure(project_path))
        
        return issues

    def _analyze_project_structure(self, project_path: str) -> List[CodeIssue]:
        """Analyze overall project structure and organization."""
        issues = []
        
        # Check for common project structure issues
        files = []
        for root, dirs, filenames in os.walk(project_path):
            for filename in filenames:
                if filename.endswith(('.py', '.js', '.ts', '.java')):
                    files.append(os.path.join(root, filename))
        
        # Check for large files
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if len(lines) > 1000:
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=1,
                        issue_type=IssueType.MAINTAINABILITY_ISSUE,
                        severity="medium",
                        description=f"File is very large ({len(lines)} lines)",
                        code_snippet=f"File contains {len(lines)} lines",
                        suggestion="Consider breaking this file into smaller, more focused modules."
                    ))
            except Exception:
                pass
        
        return issues

    def _analyze_dependencies(self, project_path: str) -> List[CodeIssue]:
        """Analyze dependencies for the project."""
        issues = []
        
        # Initialize dependency analyzer
        dependency_analyzer = DependencyAnalyzer()
        
        # Analyze dependencies
        issues.extend(dependency_analyzer.analyze_dependencies(project_path))
        
        return issues

    def _analyze_python_code(self, file_path: str, content: str, lines: List[str]) -> List[CodeIssue]:
        """Intelligent Python code analysis."""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            # Analyze function complexity
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_complexity(node)
                    if complexity > 10:
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type=IssueType.MAINTAINABILITY_ISSUE,
                            severity="medium",
                            description=f"Function '{node.name}' has high cyclomatic complexity ({complexity})",
                            code_snippet=self._get_code_snippet(lines, node.lineno),
                            suggestion="Consider breaking down the function into smaller, more focused functions."
                        ))
                    
                    # Check for long functions
                    if hasattr(node, 'end_lineno') and node.end_lineno:
                        function_length = node.end_lineno - node.lineno
                        if function_length > 50:
                            issues.append(CodeIssue(
                                file_path=file_path,
                                line_number=node.lineno,
                                issue_type=IssueType.MAINTAINABILITY_ISSUE,
                                severity="medium",
                                description=f"Function '{node.name}' is very long ({function_length} lines)",
                                code_snippet=self._get_code_snippet(lines, node.lineno),
                                suggestion="Consider refactoring into smaller functions for better maintainability."
                            ))
                
                # Check for magic numbers
                elif isinstance(node, ast.Num):
                    if isinstance(node.n, (int, float)) and abs(node.n) > 1000:
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type=IssueType.CODE_SMELL,
                            severity="low",
                            description=f"Magic number detected: {node.n}",
                            code_snippet=self._get_code_snippet(lines, node.lineno),
                            suggestion="Consider defining this as a named constant for better readability."
                        ))
                
                # Check for bare except clauses
                elif isinstance(node, ast.Try):
                    for handler in node.handlers:
                        if handler.type is None:
                            issues.append(CodeIssue(
                                file_path=file_path,
                                line_number=handler.lineno,
                                issue_type=IssueType.CODE_SMELL,
                                severity="medium",
                                description="Bare except clause detected",
                                code_snippet=self._get_code_snippet(lines, handler.lineno),
                                suggestion="Specify the exception type to catch only expected exceptions."
                            ))
        
        except SyntaxError as e:
            issues.append(CodeIssue(
                file_path=file_path,
                line_number=e.lineno or 1,
                issue_type=IssueType.LOGIC_ERROR,
                severity="high",
                description=f"Syntax error: {e.msg}",
                code_snippet=self._get_code_snippet(lines, e.lineno or 1),
                suggestion="Fix the syntax error to make the code executable."
            ))
        except Exception as e:
            # If AST parsing fails, fall back to regex-based analysis
            pass
        
        return issues

    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.AsyncWith, ast.With, ast.Try, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity

    def _get_code_snippet(self, lines: List[str], line_number: int, context: int = 2) -> str:
        """Get code snippet around the specified line."""
        start = max(0, line_number - context - 1)
        end = min(len(lines), line_number + context)
        return '\n'.join(lines[start:end])

    def generate_summary(self, issues: List[CodeIssue]) -> Dict[str, Any]:
        """Generate a comprehensive summary of all issues."""
        summary = {
            'total_issues': len(issues),
            'by_type': {},
            'by_severity': {},
            'by_language': {},
            'critical_issues': [],
            'recommendations': []
        }
        
        for issue in issues:
            # Count by type
            issue_type = issue.issue_type.value
            summary['by_type'][issue_type] = summary['by_type'].get(issue_type, 0) + 1
            
            # Count by severity
            summary['by_severity'][issue.severity] = summary['by_severity'].get(issue.severity, 0) + 1
            
            # Count by language (extract from file extension)
            ext = os.path.splitext(issue.file_path)[1].lower()
            summary['by_language'][ext] = summary['by_language'].get(ext, 0) + 1
            
            # Track critical issues
            if issue.severity == 'critical':
                summary['critical_issues'].append({
                    'file': issue.file_path,
                    'line': issue.line_number,
                    'description': issue.description
                })
        
        # Generate recommendations
        if summary['by_type'].get('security_vulnerability', 0) > 0:
            summary['recommendations'].append("Address security vulnerabilities immediately as they pose significant risks.")
        
        if summary['by_type'].get('performance_issue', 0) > 0:
            summary['recommendations'].append("Consider optimizing performance-critical code sections.")
        
        if summary['by_type'].get('maintainability_issue', 0) > 0:
            summary['recommendations'].append("Improve code maintainability by refactoring complex functions and improving documentation.")
        
        if summary['by_type'].get('linter_error', 0) > 0:
            summary['recommendations'].append("Fix linter errors to ensure code quality and consistency.")
        
        return summary

    def _filter_by_compliance(self, issues: List[CodeIssue], compliance: str) -> List[CodeIssue]:
        """Filter issues by compliance category (owasp, cwe, pci)."""
        compliance_map = {
            'owasp': [
                'owasp_a1_injection', 'owasp_a2_broken_auth', 'owasp_a3_sensitive_data', 'owasp_a5_broken_access',
                'sql_injection', 'xss_vulnerability', 'command_injection', 'path_traversal', 'authentication_bypass',
            ],
            'cwe': [
                'cwe_798_hardcoded_credential', 'cwe_89_sql_injection', 'hardcoded_credentials', 'sql_injection',
            ],
            'pci': [
                'pci_insecure_storage', 'hardcoded_credentials', 'insecure_crypto',
            ],
            'nist': [
                'nist_ac_6_least_privilege', 'hardcoded_credentials', 'sql_injection',
            ],
            'soc2': [
                'soc2_encryption', 'hardcoded_credentials', 'insecure_crypto',
            ],
            'iso27001': [
                'iso_27001_access_control', 'hardcoded_credentials', 'sql_injection',
            ],
            'hipaa': [
                'hipaa_phi_exposure', 'hardcoded_credentials',
            ],
            'gdpr': [
                'gdpr_data_protection', 'hardcoded_credentials', 'sql_injection',
            ],
            'sox': [
                'sox_financial_controls', 'hardcoded_credentials', 'sql_injection',
            ],
            'fedramp': [
                'fedramp_cloud_security', 'hardcoded_credentials', 'insecure_crypto',
            ],
            'cis': [
                'cis_controls', 'hardcoded_credentials', 'weak_permissions',
            ],
            'mitre': [
                'mitre_attack', 'command_injection', 'path_traversal',
            ],
        }
        allowed = set(compliance_map.get(compliance, []))
        filtered = [i for i in issues if getattr(i, 'pattern_name', None) in allowed or i.issue_type == 'SECURITY_VULNERABILITY']
        return filtered 