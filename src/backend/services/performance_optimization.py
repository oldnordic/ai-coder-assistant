"""
Performance Optimization Service

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
Performance Optimization Service - Analyze and optimize code performance.
"""

import json
import logging
import re
import ast
import time
import psutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import cProfile
import pstats
import io
import subprocess
import threading

logger = logging.getLogger(__name__)


@dataclass
class PerformanceIssue:
    """Performance issue found during analysis."""
    line_number: int
    issue_type: str
    severity: str  # "critical", "high", "medium", "low"
    description: str
    impact_score: float  # 0.0 to 1.0
    suggestion: str
    category: str  # "algorithm", "memory", "io", "database", "network"
    auto_fixable: bool = False
    fix_code: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for a file or function."""
    execution_time: float
    memory_usage: float
    cpu_usage: float
    function_calls: int
    line_count: int
    complexity_score: float
    optimization_score: float  # 0.0 to 100.0


@dataclass
class PerformanceAnalysisResult:
    """Result of performance analysis."""
    file_path: str
    language: str
    overall_score: float  # 0.0 to 100.0
    issues: List[PerformanceIssue] = field(default_factory=list)
    metrics: Optional[PerformanceMetrics] = None
    analysis_time: float = 0.0
    recommendations: List[str] = field(default_factory=list)


class PythonPerformanceAnalyzer:
    """Python-specific performance analyzer."""
    
    def __init__(self):
        self.performance_patterns = {
            "inefficient_loop": {
                "pattern": r"for\s+\w+\s+in\s+range\(len\([^)]+\)\)",
                "severity": "medium",
                "description": "Inefficient loop using range(len())",
                "suggestion": "Use enumerate() or direct iteration",
                "category": "algorithm"
            },
            "list_comprehension_opportunity": {
                "pattern": r"for\s+\w+\s+in\s+\w+:\s*\n\s*\w+\.append\(",
                "severity": "low",
                "description": "List append in loop could be list comprehension",
                "suggestion": "Convert to list comprehension for better performance",
                "category": "algorithm"
            },
            "global_variable_usage": {
                "pattern": r"global\s+\w+",
                "severity": "medium",
                "description": "Global variable usage can impact performance",
                "suggestion": "Consider passing variables as parameters",
                "category": "memory"
            },
            "string_concatenation": {
                "pattern": r"\w+\s*\+\s*['\"][^'\"]*['\"]",
                "severity": "low",
                "description": "String concatenation in loop",
                "suggestion": "Use join() or f-strings for better performance",
                "category": "algorithm"
            },
            "unused_imports": {
                "pattern": r"import\s+\w+",
                "severity": "low",
                "description": "Unused imports increase load time",
                "suggestion": "Remove unused imports",
                "category": "memory"
            }
        }
    
    def analyze_file(self, file_path: str) -> PerformanceAnalysisResult:
        """Analyze a Python file for performance issues."""
        start_time = time.time()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            issues = []
            
            # Analyze with regex patterns
            for pattern_name, pattern_info in self.performance_patterns.items():
                matches = re.finditer(pattern_info["pattern"], content, re.MULTILINE)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    issues.append(PerformanceIssue(
                        line_number=line_number,
                        issue_type=pattern_name,
                        severity=pattern_info["severity"],
                        description=pattern_info["description"],
                        impact_score=self._calculate_impact_score(pattern_info["severity"]),
                        suggestion=pattern_info["suggestion"],
                        category=pattern_info["category"],
                        auto_fixable=False
                    ))
            
            # AST-based analysis
            try:
                tree = ast.parse(content)
                ast_issues = self._analyze_ast(tree, content)
                issues.extend(ast_issues)
            except SyntaxError:
                logger.warning(f"Syntax error in {file_path}, skipping AST analysis")
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(issues)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(issues)
            
            analysis_time = time.time() - start_time
            
            return PerformanceAnalysisResult(
                file_path=file_path,
                language="python",
                overall_score=overall_score,
                issues=issues,
                analysis_time=analysis_time,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return PerformanceAnalysisResult(
                file_path=file_path,
                language="python",
                overall_score=0.0,
                issues=[],
                analysis_time=time.time() - start_time,
                recommendations=[f"Error during analysis: {e}"]
            )
    
    def _analyze_ast(self, tree: ast.AST, content: str) -> List[PerformanceIssue]:
        """Analyze AST for performance issues."""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Check for inefficient loops
                if self._is_inefficient_loop(node):
                    issues.append(PerformanceIssue(
                        line_number=node.lineno,
                        issue_type="inefficient_loop_ast",
                        severity="medium",
                        description="Inefficient loop detected",
                        impact_score=0.6,
                        suggestion="Consider using more efficient iteration",
                        category="algorithm"
                    ))
            
            elif isinstance(node, ast.ListComp):
                # Check for complex list comprehensions
                if self._is_complex_comprehension(node):
                    issues.append(PerformanceIssue(
                        line_number=node.lineno,
                        issue_type="complex_comprehension",
                        severity="low",
                        description="Complex list comprehension may be hard to read",
                        impact_score=0.3,
                        suggestion="Consider breaking into multiple steps for readability",
                        category="algorithm"
                    ))
            
            elif isinstance(node, ast.Call):
                # Check for expensive function calls
                if self._is_expensive_call(node):
                    issues.append(PerformanceIssue(
                        line_number=node.lineno,
                        issue_type="expensive_call",
                        severity="high",
                        description="Expensive function call detected",
                        impact_score=0.8,
                        suggestion="Consider caching or optimizing the call",
                        category="algorithm"
                    ))
        
        return issues
    
    def _is_inefficient_loop(self, node: ast.For) -> bool:
        """Check if a loop is inefficient."""
        # Simple heuristic: check if it's iterating over range(len())
        if isinstance(node.iter, ast.Call):
            if isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
                if (isinstance(node.iter.args[0], ast.Call) and 
                    isinstance(node.iter.args[0].func, ast.Name) and 
                    node.iter.args[0].func.id == 'len'):
                    return True
        return False
    
    def _is_complex_comprehension(self, node: ast.ListComp) -> bool:
        """Check if a list comprehension is too complex."""
        # Count the number of generators and conditions
        complexity = len(node.generators)
        for generator in node.generators:
            if generator.ifs:
                complexity += len(generator.ifs)
        return complexity > 2
    
    def _is_expensive_call(self, node: ast.Call) -> bool:
        """Check if a function call is expensive."""
        expensive_functions = {
            'requests.get', 'requests.post', 'subprocess.call', 'subprocess.run',
            'open', 'json.loads', 'pickle.loads', 'xml.etree.ElementTree.parse'
        }
        
        if isinstance(node.func, ast.Attribute):
            func_name = f"{node.func.value.id}.{node.func.attr}"
            return func_name in expensive_functions
        elif isinstance(node.func, ast.Name):
            return node.func.id in expensive_functions
        
        return False
    
    def _calculate_impact_score(self, severity: str) -> float:
        """Calculate impact score based on severity."""
        severity_scores = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.3
        }
        return severity_scores.get(severity, 0.5)
    
    def _calculate_overall_score(self, issues: List[PerformanceIssue]) -> float:
        """Calculate overall performance score."""
        if not issues:
            return 100.0
        
        total_impact = sum(issue.impact_score for issue in issues)
        max_possible_impact = len(issues) * 1.0
        
        # Convert to percentage (100 = perfect, 0 = worst)
        score = max(0.0, 100.0 - (total_impact / max_possible_impact) * 100.0)
        return round(score, 1)
    
    def _generate_recommendations(self, issues: List[PerformanceIssue]) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        if not issues:
            recommendations.append("No performance issues found. Code looks good!")
            return recommendations
        
        # Group issues by category
        categories = {}
        for issue in issues:
            if issue.category not in categories:
                categories[issue.category] = []
            categories[issue.category].append(issue)
        
        # Generate category-specific recommendations
        for category, category_issues in categories.items():
            if category == "algorithm":
                recommendations.append(f"Algorithm optimization: {len(category_issues)} issues found. Consider reviewing loop structures and data structures.")
            elif category == "memory":
                recommendations.append(f"Memory optimization: {len(category_issues)} issues found. Consider reducing memory allocations and improving garbage collection.")
            elif category == "io":
                recommendations.append(f"I/O optimization: {len(category_issues)} issues found. Consider batching operations and using async I/O where appropriate.")
        
        # Add general recommendations
        if len(issues) > 10:
            recommendations.append("High number of performance issues detected. Consider a comprehensive code review.")
        
        return recommendations


class PerformanceOptimizationService:
    """Main performance optimization service."""
    
    def __init__(self):
        self.analyzers = {
            "python": PythonPerformanceAnalyzer()
        }
        self.analysis_cache = {}
    
    def analyze_file(self, file_path: str) -> PerformanceAnalysisResult:
        """Analyze a file for performance issues."""
        file_path = str(file_path)
        
        # Check cache
        if file_path in self.analysis_cache:
            return self.analysis_cache[file_path]
        
        # Detect language
        language = self._detect_language(file_path)
        
        if language not in self.analyzers:
            return PerformanceAnalysisResult(
                file_path=file_path,
                language=language,
                overall_score=0.0,
                issues=[],
                recommendations=[f"Language {language} not supported for performance analysis"]
            )
        
        # Analyze file
        result = self.analyzers[language].analyze_file(file_path)
        
        # Cache result
        self.analysis_cache[file_path] = result
        
        return result
    
    def analyze_directory(self, directory_path: str) -> List[PerformanceAnalysisResult]:
        """Analyze all files in a directory."""
        results = []
        directory = Path(directory_path)
        
        if not directory.exists():
            return results
        
        # Find all supported files
        supported_extensions = {".py", ".js", ".ts", ".java", ".cpp", ".c", ".cs"}
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix in supported_extensions:
                try:
                    result = self.analyze_file(str(file_path))
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error analyzing {file_path}: {e}")
        
        return results
    
    def get_system_metrics(self) -> Dict[str, float]:
        """Get current system performance metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_available": memory.available / (1024**3),  # GB
                "disk_usage": disk.percent,
                "disk_free": disk.free / (1024**3)  # GB
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def profile_function(self, func, *args, **kwargs) -> Dict[str, Any]:
        """Profile a function's performance."""
        profiler = cProfile.Profile()
        profiler.enable()
        
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        profiler.disable()
        
        # Get profiling stats
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        stats.print_stats(20)  # Top 20 functions
        
        return {
            "execution_time": execution_time,
            "result": result,
            "profiling_stats": s.getvalue(),
            "function_name": func.__name__
        }
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp"
        }
        return language_map.get(ext, "unknown")
    
    def clear_cache(self):
        """Clear the analysis cache."""
        self.analysis_cache.clear()
    
    def get_analysis_summary(self, results: List[PerformanceAnalysisResult]) -> Dict[str, Any]:
        """Get a summary of analysis results."""
        if not results:
            return {"message": "No files analyzed"}
        
        total_files = len(results)
        total_issues = sum(len(r.issues) for r in results)
        avg_score = sum(r.overall_score for r in results) / total_files
        
        # Count issues by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for result in results:
            for issue in result.issues:
                severity_counts[issue.severity] += 1
        
        # Count issues by category
        category_counts = {}
        for result in results:
            for issue in result.issues:
                category_counts[issue.category] = category_counts.get(issue.category, 0) + 1
        
        return {
            "total_files": total_files,
            "total_issues": total_issues,
            "average_score": round(avg_score, 1),
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
            "best_file": max(results, key=lambda r: r.overall_score).file_path,
            "worst_file": min(results, key=lambda r: r.overall_score).file_path
        }
