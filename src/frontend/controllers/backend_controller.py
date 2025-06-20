"""
Backend Controller

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
Backend Controller - Handles communication between frontend and backend services.
"""

from src.core.config import Config
from src.backend.services.scanner import ScannerService
from src.backend.services.llm_manager import LLMManager
from src.backend.services.local_code_reviewer import (
    LocalCodeReviewer, 
    EnhancementRequest, 
    EnhancementResult, 
    EnhancementType,
    get_local_code_reviewer
)
from src.backend.services.intelligent_analyzer import IntelligentCodeAnalyzer
from src.backend.utils.secrets import get_secrets_manager
import logging
from typing import Any, Dict, List, Optional, Callable
import os


logger = logging.getLogger(__name__)


class BackendController:
    """Controller for backend services."""

    def __init__(self):
        self._llm_manager = None
        self._scanner_service = None
        self._local_code_reviewer = None
        self._intelligent_analyzer = None
        self._config = Config()

    def get_llm_manager(self):
        """Get the LLMManager instance."""
        if self._llm_manager is None:
            # Use centralized configuration management
            config_file_name = self._config.get(
                "config_files.llm_studio", "llm_studio_config.json"
            )
            config_path = str(self._config.get_config_file_path(config_file_name))
            self._llm_manager = LLMManager(config_path=config_path)
        return self._llm_manager

    def get_scanner_service(self):
        """Get the ScannerService instance."""
        if self._scanner_service is None:
            self._scanner_service = ScannerService()
        return self._scanner_service

    def get_local_code_reviewer(self) -> LocalCodeReviewer:
        """Get the LocalCodeReviewer instance."""
        if self._local_code_reviewer is None:
            self._local_code_reviewer = get_local_code_reviewer()
        return self._local_code_reviewer

    def get_intelligent_analyzer(self) -> IntelligentCodeAnalyzer:
        """Get the IntelligentCodeAnalyzer instance."""
        if self._intelligent_analyzer is None:
            self._intelligent_analyzer = IntelligentCodeAnalyzer()
        return self._intelligent_analyzer

    # AI Analysis Methods

    def start_quick_scan(self, directory_path: str, include_patterns: Optional[List[str]] = None, 
                        exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Start a quick scan of the specified directory.
        
        This method implements the first stage of the two-stage analysis approach:
        1. Quick Scan: Immediate local analysis using static rules
        2. AI Enhancement: On-demand AI analysis of specific issues
        
        Args:
            directory_path: Path to the directory to scan
            include_patterns: List of file patterns to include
            exclude_patterns: List of file patterns to exclude
            
        Returns:
            Dictionary containing scan results with the following format:
            {
                "success": bool,
                "issues": [
                    {
                        "file": "path/to/file.py",
                        "line": 10,
                        "issue": "Description of the issue",
                        "severity": "high|medium|low",
                        "type": "issue_type",
                        "code_snippet": "line_of_code",
                        "context": "surrounding_lines"
                    }
                ],
                "total_issues": int,
                "scan_type": "quick_scan"
            }
        """
        try:
            analyzer = self.get_intelligent_analyzer()
            
            # Use default patterns if none provided
            if include_patterns is None:
                include_patterns = ["*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.c", "*.h", "*.hpp"]
            if exclude_patterns is None:
                exclude_patterns = ["__pycache__/*", "node_modules/*", ".git/*", "*.pyc", "*.log"]
            
            # Get all files to scan
            files_to_scan = []
            for root, dirs, files in os.walk(directory_path):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    # Check if file matches include patterns
                    if any(file.endswith(pattern.strip().replace('*', '')) for pattern in include_patterns):
                        # Check if file should be excluded
                        if not any(exclude.replace('*', '') in file_path for exclude in exclude_patterns):
                            files_to_scan.append(file_path)
            
            logger.info(f"Found {len(files_to_scan)} files to scan in {directory_path}")
            
            # Perform quick scan on each file
            all_issues = []
            for file_path in files_to_scan:
                try:
                    file_issues = analyzer.perform_quick_scan(file_path)
                    # Add file path to each issue
                    for issue in file_issues:
                        issue["file_path"] = file_path
                    all_issues.extend(file_issues)
                except Exception as e:
                    logger.warning(f"Error scanning file {file_path}: {e}")
                    # Add error issue
                    all_issues.append({
                        "file_path": file_path,
                        "line_number": 1,
                        "description": f"Error scanning file: {e}",
                        "severity": "error",
                        "issue_type": "file_error",
                        "code_snippet": "",
                        "context": "",
                        "language": "unknown"
                    })
            
            # Convert to frontend-friendly format
            formatted_issues: List[Dict[str, Any]] = []
            for issue in all_issues:
                formatted_issue = {
                    "file": issue.get("file_path", ""),
                    "line": issue.get("line_number", 0),
                    "issue": issue.get("description", ""),
                    "severity": issue.get("severity", "medium"),
                    "type": issue.get("issue_type", "code_quality"),
                    "code_snippet": issue.get("code_snippet", ""),
                    "context": issue.get("context", ""),
                    "language": issue.get("language", "unknown")
                }
                formatted_issues.append(formatted_issue)
            
            logger.info(f"Quick scan completed. Found {len(formatted_issues)} issues in {len(files_to_scan)} files")
            
            return {
                "success": True,
                "issues": formatted_issues,
                "total_issues": len(formatted_issues),
                "scan_type": "quick_scan"
            }
            
        except Exception as e:
            logger.error(f"Error during quick scan: {e}")
            return {
                "success": False,
                "error": str(e),
                "issues": [],
                "total_issues": 0,
                "scan_type": "quick_scan"
            }

    def get_ai_enhancement(self, issue_data: Dict[str, Any], 
                          enhancement_type: str = "code_improvement") -> EnhancementResult:
        """
        Get AI enhancement for a specific issue.
        
        This method implements the second stage of the two-stage analysis approach:
        1. Quick Scan: Immediate local analysis using static rules
        2. AI Enhancement: On-demand AI analysis of specific issues
        
        Args:
            issue_data: Dictionary containing issue details with the following format:
                {
                    "file": "path/to/file.py",
                    "line": 10,
                    "issue": "Description of the issue",
                    "severity": "high|medium|low",
                    "type": "issue_type",
                    "code_snippet": "line_of_code",
                    "context": "surrounding_lines",
                    "language": "language_name"
                }
            enhancement_type: Type of enhancement to perform (code_improvement, security_analysis, etc.)
            
        Returns:
            EnhancementResult with detailed analysis and structured suggestions
        """
        try:
            reviewer = self.get_local_code_reviewer()
            
            # Create enhancement request
            request = EnhancementRequest(
                issue_description=issue_data.get("issue", ""),
                file_path=issue_data.get("file", ""),
                line_number=issue_data.get("line", 0),
                code_snippet=issue_data.get("code_snippet", ""),
                language=issue_data.get("language", "unknown"),
                enhancement_type=EnhancementType(enhancement_type),
                context_lines=5,
                include_suggestions=True,
                include_explanation=True
            )
            
            # Perform analysis
            result = reviewer.analyze_snippet(request)
            
            return result
            
        except Exception as e:
            logger.error(f"Error during AI enhancement: {e}")
            # Return a fallback result
            return EnhancementResult(
                original_issue=issue_data.get("issue", ""),
                enhanced_analysis=f"Error during AI enhancement: {e}",
                suggestions=["Review the code manually", "Check for common patterns in similar issues"],
                explanation="AI enhancement failed due to technical issues.",
                confidence_score=0.0,
                model_used="none",
                processing_time=0.0
            )

    def get_ai_enhancement_async(self, issue_data: Dict[str, Any], 
                                enhancement_type: str = "code_improvement",
                                callback: Optional[Callable[[EnhancementResult], None]] = None) -> str:
        """
        Get AI enhancement asynchronously.
        
        Args:
            issue_data: Dictionary containing issue details
            enhancement_type: Type of enhancement to perform
            callback: Optional callback function to call with result
            
        Returns:
            Task ID for tracking the async operation
        """
        try:
            reviewer = self.get_local_code_reviewer()
            
            # Create enhancement request
            request = EnhancementRequest(
                issue_description=issue_data.get("issue", ""),
                file_path=issue_data.get("file", ""),
                line_number=issue_data.get("line", 0),
                code_snippet=issue_data.get("code_snippet", ""),
                language=issue_data.get("language", "unknown"),
                enhancement_type=EnhancementType(enhancement_type)
            )
            
            # Start async analysis
            task_id = reviewer.analyze_snippet_async(request, callback)
            
            return task_id
            
        except Exception as e:
            logger.error(f"Error starting async AI enhancement: {e}")
            return ""

    def get_enhancement_status(self, task_id: str) -> Optional[str]:
        """Get the status of an async enhancement task."""
        try:
            reviewer = self.get_local_code_reviewer()
            return reviewer.get_enhancement_status(task_id)
        except Exception as e:
            logger.error(f"Error getting enhancement status: {e}")
            return None

    def cancel_enhancement(self, task_id: str) -> bool:
        """Cancel an async enhancement task."""
        try:
            reviewer = self.get_local_code_reviewer()
            return reviewer.cancel_enhancement(task_id)
        except Exception as e:
            logger.error(f"Error cancelling enhancement: {e}")
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available models for code review."""
        try:
            reviewer = self.get_local_code_reviewer()
            return reviewer.get_available_models()
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []

    def switch_model(self, model_name: str) -> bool:
        """Switch to a different model for code review."""
        try:
            reviewer = self.get_local_code_reviewer()
            return reviewer.switch_model(model_name)
        except Exception as e:
            logger.error(f"Error switching model: {e}")
            return False

    # Security Intelligence Methods

    async def fetch_security_feeds(self):
        """Fetch security feeds."""
        try:
            await self.get_llm_manager().fetch_security_feeds()
        except Exception as e:
            logger.error(f"Error fetching security feeds: {e}")
            raise

    def get_security_vulnerabilities(
        self, severity: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get security vulnerabilities."""
        try:
            vulnerabilities = self.get_llm_manager().get_security_vulnerabilities(
                severity, limit
            )
            # Convert dataclass objects to dictionaries
            result: List[Dict[str, Any]] = []
            for vuln in vulnerabilities:
                vuln_dict: Dict[str, Any] = {
                    "id": vuln.id,
                    "title": vuln.title,
                    "description": vuln.description,
                    "severity": vuln.severity,
                    "cvss_score": vuln.cvss_score,
                    "affected_products": vuln.affected_products,
                    "affected_versions": vuln.affected_versions,
                    "published_date": (
                        vuln.published_date.isoformat() if vuln.published_date else None
                    ),
                    "last_updated": (
                        vuln.last_updated.isoformat() if vuln.last_updated else None
                    ),
                    "references": vuln.references,
                    "patches": vuln.patches,
                    "source": vuln.source,
                    "tags": vuln.tags,
                    "is_patched": vuln.is_patched,
                    "patch_available": vuln.patch_available,
                }
                result.append(vuln_dict)
            return result
        except Exception as e:
            logger.error(f"Error getting vulnerabilities: {e}")
            return []

    def get_security_breaches(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get security breaches."""
        try:
            breaches = self.get_llm_manager().get_security_breaches(limit)
            # Convert dataclass objects to dictionaries
            result: List[Dict[str, Any]] = []
            for breach in breaches:
                breach_dict: Dict[str, Any] = {
                    "id": breach.id,
                    "title": breach.title,
                    "description": breach.description,
                    "company": breach.company,
                    "breach_date": (
                        breach.breach_date.isoformat() if breach.breach_date else None
                    ),
                    "affected_users": breach.affected_users,
                    "data_types": breach.data_types,
                    "source": breach.source,
                    "references": breach.references,
                }
                result.append(breach_dict)
            return result
        except Exception as e:
            logger.error(f"Error getting breaches: {e}")
            return []

    def get_security_patches(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get security patches."""
        try:
            patches = self.get_llm_manager().get_security_patches(limit)
            # Convert dataclass objects to dictionaries
            result: List[Dict[str, Any]] = []
            for patch in patches:
                patch_dict: Dict[str, Any] = {
                    "id": patch.id,
                    "title": patch.title,
                    "description": patch.description,
                    "release_date": (
                        patch.release_date.isoformat() if patch.release_date else None
                    ),
                    "severity": patch.severity,
                    "source": patch.source,
                    "tested": patch.tested,
                    "applied": patch.applied,
                }
                result.append(patch_dict)
            return result
        except Exception as e:
            logger.error(f"Error getting patches: {e}")
            return []

    def get_security_training_data(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get security training data."""
        try:
            return self.get_llm_manager().get_security_training_data(limit)
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return []

    def add_security_feed(self, feed_data: Dict[str, Any]):
        """Add a security feed."""
        try:
            from backend.services.security_intelligence import SecurityFeed

            feed = SecurityFeed(**feed_data)
            self.get_llm_manager().add_security_feed(feed)
        except Exception as e:
            logger.error(f"Error adding security feed: {e}")
            raise

    def remove_security_feed(self, feed_name: str):
        """Remove a security feed."""
        try:
            self.get_llm_manager().remove_security_feed(feed_name)
        except Exception as e:
            logger.error(f"Error removing security feed: {e}")
            raise

    def get_security_feeds(self) -> List[Dict[str, Any]]:
        """Get security feeds."""
        try:
            feeds = self.get_llm_manager().get_security_feeds()
            # Convert dataclass objects to dictionaries
            result: List[Dict[str, Any]] = []
            for feed in feeds:
                feed_dict: Dict[str, Any] = {
                    "name": feed.name,
                    "url": feed.url,
                    "type": feed.type,
                    "enabled": feed.enabled,
                    "last_fetch": (
                        feed.last_fetch.isoformat() if feed.last_fetch else None
                    ),
                    "fetch_interval": feed.fetch_interval,
                }
                result.append(feed_dict)
            return result
        except Exception as e:
            logger.error(f"Error getting security feeds: {e}")
            return []

    def mark_patch_applied(self, patch_id: str):
        """Mark a security patch as applied."""
        try:
            self.get_llm_manager().mark_patch_applied(patch_id)
        except Exception as e:
            logger.error(f"Error marking patch as applied: {e}")
            raise

    def mark_vulnerability_patched(self, vuln_id: str):
        """Mark a vulnerability as patched."""
        try:
            self.get_llm_manager().mark_vulnerability_patched(vuln_id)
        except Exception as e:
            logger.error(f"Error marking vulnerability as patched: {e}")
            raise

    # Code Standards Methods

    def get_code_standards(self) -> List[Dict[str, Any]]:
        """Get all code standards."""
        try:
            standards = self.get_llm_manager().get_code_standards()
            # Convert dataclass objects to dictionaries
            result: List[Dict[str, Any]] = []
            for standard in standards:
                standard_dict: Dict[str, Any] = {
                    "name": standard.name,
                    "description": standard.description,
                    "language": standard.language,
                    "rules": standard.rules,
                    "enabled": standard.enabled,
                    "created_at": (
                        standard.created_at.isoformat() if standard.created_at else None
                    ),
                    "updated_at": (
                        standard.updated_at.isoformat() if standard.updated_at else None
                    ),
                }
                result.append(standard_dict)
            return result
        except Exception as e:
            logger.error(f"Error getting code standards: {e}")
            return []

    def get_current_code_standard(self) -> Optional[Dict[str, Any]]:
        """Get the currently active code standard."""
        try:
            standard = self.get_llm_manager().get_current_code_standard()
            if standard:
                return {
                    "name": standard.name,
                    "description": standard.description,
                    "language": standard.language,
                    "rules": standard.rules,
                    "enabled": standard.enabled,
                    "created_at": (
                        standard.created_at.isoformat() if standard.created_at else None
                    ),
                    "updated_at": (
                        standard.updated_at.isoformat() if standard.updated_at else None
                    ),
                }
            return None
        except Exception as e:
            logger.error(f"Error getting current code standard: {e}")
            return None

    def add_code_standard(self, standard_data: Dict[str, Any]):
        """Add a new code standard."""
        try:
            from backend.services.code_standards import CodeStandard

            standard = CodeStandard(**standard_data)
            self.get_llm_manager().add_code_standard(standard)
        except Exception as e:
            logger.error(f"Error adding code standard: {e}")
            raise

    def remove_code_standard(self, standard_name: str):
        """Remove a code standard."""
        try:
            self.get_llm_manager().remove_code_standard(standard_name)
        except Exception as e:
            logger.error(f"Error removing code standard: {e}")
            raise

    def set_current_code_standard(self, standard_name: str):
        """Set the current code standard."""
        try:
            self.get_llm_manager().set_current_code_standard(standard_name)
        except Exception as e:
            logger.error(f"Error setting current code standard: {e}")
            raise

    def analyze_code_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single code file."""
        try:
            result = self.get_llm_manager().analyze_code_file(file_path)
            return result
        except Exception as e:
            logger.error(f"Error analyzing code file: {e}")
            return {"error": str(e)}

    def analyze_code_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """Analyze all code files in a directory."""
        try:
            results = self.get_llm_manager().analyze_code_directory(directory_path)
            return results
        except Exception as e:
            logger.error(f"Error analyzing code directory: {e}")
            return [{"error": str(e)}]

    def export_code_standard(self, standard_name: str, export_path: str):
        """Export a code standard to a file."""
        try:
            self.get_llm_manager().export_code_standard(standard_name, export_path)
        except Exception as e:
            logger.error(f"Error exporting code standard: {e}")
            raise

    def import_code_standard(self, import_path: str):
        """Import a code standard from a file."""
        try:
            self.get_llm_manager().import_code_standard(import_path)
        except Exception as e:
            logger.error(f"Error importing code standard: {e}")
            raise

    def save_secret(self, secret_name: str, secret_value: str):
        """Save a secret."""
        try:
            get_secrets_manager().save_secret(secret_name, secret_value)
        except Exception as e:
            logger.error(f"Error saving secret: {e}")
            raise

    def load_secret(self, secret_name: str) -> Optional[str]:
        """Load a secret."""
        try:
            return get_secrets_manager().load_secret(secret_name)
        except Exception as e:
            logger.error(f"Error loading secret: {e}")
            return None
