"""
SAST Security Analyzer

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

import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SecurityTool(Enum):
    BANDIT = "bandit"
    NJSSCAN = "njsscan"
    SEMGREP = "semgrep"
    SAFETY = "safety"
    TRUFFLEHOG = "trufflehog"
    PIP_AUDIT = "pip-audit"


@dataclass
class SecurityIssue:
    """Represents a security issue found by SAST tools."""

    file_path: str
    line_number: int
    severity: str
    issue_type: str
    description: str
    tool: SecurityTool
    confidence: float
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    code_snippet: str = ""
    suggestion: str = ""
    context: Optional[Dict[str, Any]] = None


class SASTAnalyzer:
    """
    SAST-based security analyzer that integrates dedicated security tools
    for accurate vulnerability detection with minimal false positives.
    """

    def __init__(self):
        self.tools_available = self._check_tools_availability()
        self.cache = {}

    def _check_tools_availability(self) -> Dict[SecurityTool, bool]:
        """Check which security tools are available on the system."""
        tools_status = {}

        for tool in SecurityTool:
            try:
                if tool == SecurityTool.BANDIT:
                    result = subprocess.run(
                        ["bandit", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    tools_status[tool] = result.returncode == 0
                elif tool == SecurityTool.NJSSCAN:
                    result = subprocess.run(
                        ["njsscan", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    tools_status[tool] = result.returncode == 0
                elif tool == SecurityTool.SEMGREP:
                    result = subprocess.run(
                        ["semgrep", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    tools_status[tool] = result.returncode == 0
                elif tool == SecurityTool.SAFETY:
                    result = subprocess.run(
                        ["safety", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    tools_status[tool] = result.returncode == 0
                elif tool == SecurityTool.TRUFFLEHOG:
                    result = subprocess.run(
                        ["trufflehog", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    tools_status[tool] = result.returncode == 0
                elif tool == SecurityTool.PIP_AUDIT:
                    result = subprocess.run(
                        ["pip-audit", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    tools_status[tool] = result.returncode == 0
            except (
                subprocess.TimeoutExpired,
                FileNotFoundError,
                subprocess.SubprocessError,
            ):
                tools_status[tool] = False
                logger.warning(f"Security tool {tool.value} not available")

        return tools_status

    def analyze_file(self, file_path: str, language: str) -> List[SecurityIssue]:
        """
        Analyze a single file for security vulnerabilities using appropriate SAST tools.

        Args:
            file_path: Path to the file to analyze
            language: Programming language of the file

        Returns:
            List of security issues found
        """
        # Check cache first
        cache_key = f"{file_path}_{language}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        issues = []

        try:
            if language == "python":
                if self.tools_available[SecurityTool.BANDIT]:
                    issues.extend(self._run_bandit(file_path))
                if self.tools_available[SecurityTool.SEMGREP]:
                    issues.extend(self._run_semgrep(file_path, "python"))

            elif language in ["javascript", "typescript"]:
                if self.tools_available[SecurityTool.NJSSCAN]:
                    issues.extend(self._run_njsscan(file_path))
                if self.tools_available[SecurityTool.SEMGREP]:
                    issues.extend(self._run_semgrep(file_path, "javascript"))

            # Cache results
            self.cache[cache_key] = issues

        except Exception as e:
            logger.error(f"Error analyzing {file_path} with SAST tools: {e}")

        return issues

    def analyze_project(self, project_path: str) -> List[SecurityIssue]:
        """
        Analyze an entire project for security vulnerabilities.

        Args:
            project_path: Path to the project root

        Returns:
            List of security issues found across the project
        """
        issues = []

        try:
            # Run project-wide scans
            if self.tools_available[SecurityTool.SEMGREP]:
                issues.extend(self._run_semgrep_project(project_path))

            if self.tools_available[SecurityTool.SAFETY]:
                issues.extend(self._run_safety_check(project_path))

            # Add secrets scanning
            if self.tools_available[SecurityTool.TRUFFLEHOG]:
                issues.extend(self._run_trufflehog_scan(project_path))

            # Add SCA scanning
            if self.tools_available[SecurityTool.PIP_AUDIT]:
                issues.extend(self._run_pip_audit_scan(project_path))

        except Exception as e:
            logger.error(f"Error analyzing project {project_path} with SAST tools: {e}")

        return issues

    def _run_bandit(self, file_path: str) -> List[SecurityIssue]:
        """Run Bandit security linter on Python files."""
        issues = []

        try:
            # Run bandit with JSON output
            result = subprocess.run(
                ["bandit", "-f", "json", "-r", file_path],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if (
                result.returncode == 0 or result.returncode == 1
            ):  # Bandit returns 1 when issues found
                try:
                    output = json.loads(result.stdout)

                    for issue in output.get("results", []):
                        security_issue = SecurityIssue(
                            file_path=issue.get("filename", file_path),
                            line_number=issue.get("line_number", 1),
                            severity=issue.get("issue_severity", "medium"),
                            issue_type=issue.get(
                                "issue_text", "security_vulnerability"
                            ),
                            description=issue.get("issue_text", ""),
                            tool=SecurityTool.BANDIT,
                            confidence=0.9,  # Bandit has high confidence
                            cwe_id=(
                                issue.get("cwe", {}).get("id")
                                if issue.get("cwe")
                                else None
                            ),
                            code_snippet=issue.get("code", ""),
                            suggestion=issue.get("more_info", ""),
                        )
                        issues.append(security_issue)

                except json.JSONDecodeError:
                    logger.error(f"Failed to parse Bandit output for {file_path}")

        except subprocess.TimeoutExpired:
            logger.warning(f"Bandit analysis timed out for {file_path}")
        except Exception as e:
            logger.error(f"Error running Bandit on {file_path}: {e}")

        return issues

    def _run_njsscan(self, file_path: str) -> List[SecurityIssue]:
        """Run njsscan security scanner on JavaScript/TypeScript files."""
        issues = []

        try:
            # Run njsscan with JSON output
            result = subprocess.run(
                ["njsscan", "--json", file_path],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout)

                    for file_issues in output.values():
                        if isinstance(file_issues, list):
                            for issue in file_issues:
                                security_issue = SecurityIssue(
                                    file_path=file_path,
                                    line_number=issue.get("line", 1),
                                    severity=issue.get("severity", "medium"),
                                    issue_type=issue.get(
                                        "type", "security_vulnerability"
                                    ),
                                    description=issue.get("message", ""),
                                    tool=SecurityTool.NJSSCAN,
                                    confidence=0.85,  # njsscan has good confidence
                                    cwe_id=issue.get("cwe", ""),
                                    code_snippet=issue.get("code", ""),
                                    suggestion=issue.get("remediation", ""),
                                )
                                issues.append(security_issue)

                except json.JSONDecodeError:
                    logger.error(f"Failed to parse njsscan output for {file_path}")

        except subprocess.TimeoutExpired:
            logger.warning(f"njsscan analysis timed out for {file_path}")
        except Exception as e:
            logger.error(f"Error running njsscan on {file_path}: {e}")

        return issues

    def _run_semgrep(self, file_path: str, language: str) -> List[SecurityIssue]:
        """Run Semgrep security scanner on files."""
        issues = []

        try:
            # Run semgrep with JSON output
            result = subprocess.run(
                ["semgrep", "--json", "--config=auto", file_path],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if (
                result.returncode == 0 or result.returncode == 1
            ):  # Semgrep returns 1 when issues found
                try:
                    output = json.loads(result.stdout)

                    for result_item in output.get("results", []):
                        security_issue = SecurityIssue(
                            file_path=result_item.get("path", file_path),
                            line_number=result_item.get("start", {}).get("line", 1),
                            severity=result_item.get("extra", {}).get(
                                "severity", "medium"
                            ),
                            issue_type=result_item.get(
                                "check_id", "security_vulnerability"
                            ),
                            description=result_item.get("extra", {}).get("message", ""),
                            tool=SecurityTool.SEMGREP,
                            confidence=0.8,  # Semgrep has good confidence
                            cwe_id=result_item.get("extra", {})
                            .get("metadata", {})
                            .get("cwe", ""),
                            code_snippet=result_item.get("extra", {}).get("lines", ""),
                            suggestion=result_item.get("extra", {}).get("fix", ""),
                        )
                        issues.append(security_issue)

                except json.JSONDecodeError:
                    logger.error(f"Failed to parse Semgrep output for {file_path}")

        except subprocess.TimeoutExpired:
            logger.warning(f"Semgrep analysis timed out for {file_path}")
        except Exception as e:
            logger.error(f"Error running Semgrep on {file_path}: {e}")

        return issues

    def _run_semgrep_project(self, project_path: str) -> List[SecurityIssue]:
        """Run Semgrep on entire project."""
        issues = []

        try:
            # Run semgrep on project with JSON output
            result = subprocess.run(
                ["semgrep", "--json", "--config=auto", project_path],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0 or result.returncode == 1:
                try:
                    output = json.loads(result.stdout)

                    for result_item in output.get("results", []):
                        security_issue = SecurityIssue(
                            file_path=result_item.get("path", ""),
                            line_number=result_item.get("start", {}).get("line", 1),
                            severity=result_item.get("extra", {}).get(
                                "severity", "medium"
                            ),
                            issue_type=result_item.get(
                                "check_id", "security_vulnerability"
                            ),
                            description=result_item.get("extra", {}).get("message", ""),
                            tool=SecurityTool.SEMGREP,
                            confidence=0.8,
                            cwe_id=result_item.get("extra", {})
                            .get("metadata", {})
                            .get("cwe", ""),
                            code_snippet=result_item.get("extra", {}).get("lines", ""),
                            suggestion=result_item.get("extra", {}).get("fix", ""),
                        )
                        issues.append(security_issue)

                except json.JSONDecodeError:
                    logger.error(f"Failed to parse Semgrep project output")

        except subprocess.TimeoutExpired:
            logger.warning(f"Semgrep project analysis timed out")
        except Exception as e:
            logger.error(f"Error running Semgrep on project: {e}")

        return issues

    def _run_safety_check(self, project_path: str) -> List[SecurityIssue]:
        """Run Safety dependency vulnerability scanner."""
        issues = []

        try:
            # Run safety check with JSON output
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=project_path,
            )

            if (
                result.returncode == 0 or result.returncode == 1
            ):  # Safety returns 1 when vulnerabilities found
                try:
                    output = json.loads(result.stdout)

                    for vuln in output:
                        security_issue = SecurityIssue(
                            file_path=f"{project_path}/requirements.txt",
                            line_number=1,
                            severity=vuln.get("severity", "medium"),
                            issue_type="dependency_vulnerability",
                            description=f"Vulnerable dependency: {vuln.get('package', '')} {vuln.get('installed_version', '')}",
                            tool=SecurityTool.SAFETY,
                            confidence=0.95,  # Safety has very high confidence
                            cwe_id=vuln.get("cve", ""),
                            code_snippet=f"Package: {vuln.get('package', '')}",
                            suggestion=f"Update to version {vuln.get('latest_version', 'latest')} or newer",
                        )
                        issues.append(security_issue)

                except json.JSONDecodeError:
                    logger.error(f"Failed to parse Safety output")

        except subprocess.TimeoutExpired:
            logger.warning(f"Safety check timed out")
        except Exception as e:
            logger.error(f"Error running Safety check: {e}")

        return issues

    def _run_trufflehog_scan(self, project_path: str) -> List[SecurityIssue]:
        """Run TruffleHog to scan for hardcoded secrets."""
        issues = []

        try:
            # Run trufflehog with JSON output
            result = subprocess.run(
                ["trufflehog", "--json", project_path],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                try:
                    # TruffleHog outputs one JSON object per line
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            issue_data = json.loads(line)
                            
                            security_issue = SecurityIssue(
                                file_path=issue_data.get("path", ""),
                                line_number=issue_data.get("line", 1),
                                severity="high",  # Secrets are always high severity
                                issue_type="hardcoded_secret",
                                description=f"Potential secret found: {issue_data.get('reason', 'Unknown secret type')}",
                                tool=SecurityTool.TRUFFLEHOG,
                                confidence=0.9,
                                cwe_id="CWE-532",  # Information Exposure Through Log Files
                                code_snippet=issue_data.get("raw", ""),
                                suggestion="Remove hardcoded secrets and use environment variables or secure secret management",
                            )
                            issues.append(security_issue)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse TruffleHog output: {e}")

        except subprocess.TimeoutExpired:
            logger.warning(f"TruffleHog analysis timed out for {project_path}")
        except Exception as e:
            logger.error(f"Error running TruffleHog on {project_path}: {e}")

        return issues

    def _run_pip_audit_scan(self, project_path: str) -> List[SecurityIssue]:
        """Run pip-audit to scan for vulnerable dependencies."""
        issues = []

        try:
            # Look for requirements files
            requirements_files = []
            for req_file in ["requirements.txt", "pyproject.toml", "setup.py"]:
                req_path = os.path.join(project_path, req_file)
                if os.path.exists(req_path):
                    requirements_files.append(req_path)

            if not requirements_files:
                logger.info(f"No requirements files found in {project_path}")
                return issues

            # Run pip-audit on each requirements file
            for req_file in requirements_files:
                try:
                    result = subprocess.run(
                        ["pip-audit", "--format", "json", "--requirement", req_file],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    if result.returncode == 0 or result.returncode == 1:  # pip-audit returns 1 when vulnerabilities found
                        try:
                            output = json.loads(result.stdout)
                            
                            for vuln in output.get("vulnerabilities", []):
                                security_issue = SecurityIssue(
                                    file_path=req_file,
                                    line_number=1,
                                    severity=vuln.get("severity", "medium"),
                                    issue_type="vulnerable_dependency",
                                    description=f"Vulnerable package: {vuln.get('package', {}).get('name', 'Unknown')} - {vuln.get('description', 'No description')}",
                                    tool=SecurityTool.PIP_AUDIT,
                                    confidence=0.95,
                                    cwe_id=vuln.get("cwe", ""),
                                    code_snippet=f"Package: {vuln.get('package', {}).get('name', 'Unknown')}",
                                    suggestion=f"Update {vuln.get('package', {}).get('name', 'Unknown')} to a secure version",
                                    context={
                                        "package_name": vuln.get("package", {}).get("name"),
                                        "current_version": vuln.get("package", {}).get("version"),
                                        "fixed_version": vuln.get("fixed_version"),
                                        "cve_id": vuln.get("id"),
                                    }
                                )
                                issues.append(security_issue)

                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse pip-audit output for {req_file}")

                except subprocess.TimeoutExpired:
                    logger.warning(f"pip-audit analysis timed out for {req_file}")
                except Exception as e:
                    logger.error(f"Error running pip-audit on {req_file}: {e}")

        except Exception as e:
            logger.error(f"Error running pip-audit scan on {project_path}: {e}")

        return issues

    def get_tools_status(self) -> Dict[str, bool]:
        """Get status of available security tools."""
        return {
            tool.value: available for tool, available in self.tools_available.items()
        }

    def clear_cache(self):
        """Clear the analysis cache."""
        self.cache.clear()
