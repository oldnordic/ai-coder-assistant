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

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import os

from backend.services.llm_manager import LLMManager

logger = logging.getLogger(__name__)


class BackendController:
    """Controller for backend services."""
    
    def __init__(self):
        # Use the correct config path relative to the project root
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "llm_studio_config.json")
        self.llm_manager = LLMManager(config_path)
    
    # Security Intelligence Methods
    
    def fetch_security_feeds(self):
        """Fetch security feeds."""
        try:
            # This would be async in a real implementation
            return self.llm_manager.fetch_security_feeds()
        except Exception as e:
            logger.error(f"Error fetching security feeds: {e}")
            raise
    
    def get_security_vulnerabilities(self, severity: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get security vulnerabilities."""
        try:
            vulnerabilities = self.llm_manager.get_security_vulnerabilities(severity, limit)
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
                    "published_date": vuln.published_date.isoformat() if vuln.published_date else None,
                    "last_updated": vuln.last_updated.isoformat() if vuln.last_updated else None,
                    "references": vuln.references,
                    "patches": vuln.patches,
                    "source": vuln.source,
                    "tags": vuln.tags,
                    "is_patched": vuln.is_patched,
                    "patch_available": vuln.patch_available
                }
                result.append(vuln_dict)
            return result
        except Exception as e:
            logger.error(f"Error getting vulnerabilities: {e}")
            return []
    
    def get_security_breaches(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get security breaches."""
        try:
            breaches = self.llm_manager.get_security_breaches(limit)
            # Convert dataclass objects to dictionaries
            result: List[Dict[str, Any]] = []
            for breach in breaches:
                breach_dict: Dict[str, Any] = {
                    "id": breach.id,
                    "title": breach.title,
                    "description": breach.description,
                    "company": breach.company,
                    "breach_date": breach.breach_date.isoformat() if breach.breach_date else None,
                    "discovered_date": breach.discovered_date.isoformat() if breach.discovered_date else None,
                    "affected_users": breach.affected_users,
                    "data_types": breach.data_types,
                    "attack_vector": breach.attack_vector,
                    "severity": breach.severity,
                    "source": breach.source,
                    "references": breach.references,
                    "lessons_learned": breach.lessons_learned,
                    "mitigation_strategies": breach.mitigation_strategies
                }
                result.append(breach_dict)
            return result
        except Exception as e:
            logger.error(f"Error getting breaches: {e}")
            return []
    
    def get_security_patches(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get security patches."""
        try:
            patches = self.llm_manager.get_security_patches(limit)
            # Convert dataclass objects to dictionaries
            result: List[Dict[str, Any]] = []
            for patch in patches:
                patch_dict: Dict[str, Any] = {
                    "id": patch.id,
                    "title": patch.title,
                    "description": patch.description,
                    "affected_products": patch.affected_products,
                    "patch_version": patch.patch_version,
                    "release_date": patch.release_date.isoformat() if patch.release_date else None,
                    "severity": patch.severity,
                    "source": patch.source,
                    "download_url": patch.download_url,
                    "installation_instructions": patch.installation_instructions,
                    "rollback_instructions": patch.rollback_instructions,
                    "tested": patch.tested,
                    "applied": patch.applied
                }
                result.append(patch_dict)
            return result
        except Exception as e:
            logger.error(f"Error getting patches: {e}")
            return []
    
    def get_security_training_data(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get security training data."""
        try:
            return self.llm_manager.get_security_training_data(limit)
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return []
    
    def add_security_feed(self, feed_data: Dict[str, Any]):
        """Add a security feed."""
        try:
            from backend.services.security_intelligence import SecurityFeed
            feed = SecurityFeed(**feed_data)
            self.llm_manager.add_security_feed(feed)
        except Exception as e:
            logger.error(f"Error adding security feed: {e}")
            raise
    
    def remove_security_feed(self, feed_name: str):
        """Remove a security feed."""
        try:
            self.llm_manager.remove_security_feed(feed_name)
        except Exception as e:
            logger.error(f"Error removing security feed: {e}")
            raise
    
    def get_security_feeds(self) -> List[Dict[str, Any]]:
        """Get security feeds."""
        try:
            feeds = self.llm_manager.get_security_feeds()
            # Convert dataclass objects to dictionaries
            result: List[Dict[str, Any]] = []
            for feed in feeds:
                feed_dict: Dict[str, Any] = {
                    "name": feed.name,
                    "url": feed.url,
                    "feed_type": feed.feed_type,
                    "enabled": feed.enabled,
                    "last_fetch": feed.last_fetch.isoformat() if feed.last_fetch else None,
                    "fetch_interval": feed.fetch_interval,
                    "tags": feed.tags
                }
                result.append(feed_dict)
            return result
        except Exception as e:
            logger.error(f"Error getting security feeds: {e}")
            return []
    
    def mark_patch_applied(self, patch_id: str):
        """Mark a patch as applied."""
        try:
            self.llm_manager.mark_patch_applied(patch_id)
        except Exception as e:
            logger.error(f"Error marking patch as applied: {e}")
            raise
    
    def mark_vulnerability_patched(self, vuln_id: str):
        """Mark a vulnerability as patched."""
        try:
            self.llm_manager.mark_vulnerability_patched(vuln_id)
        except Exception as e:
            logger.error(f"Error marking vulnerability as patched: {e}")
            raise
    
    # Code Standards Methods
    
    def get_code_standards(self) -> List[Dict[str, Any]]:
        """Get code standards."""
        try:
            standards = self.llm_manager.get_code_standards()
            # Convert dataclass objects to dictionaries
            result: List[Dict[str, Any]] = []
            for standard in standards:
                standard_dict: Dict[str, Any] = {
                    "name": standard.name,
                    "description": standard.description,
                    "company": standard.company,
                    "version": standard.version,
                    "languages": [lang.value for lang in standard.languages],
                    "rules": [rule.__dict__ for rule in standard.rules],
                    "created_date": standard.created_date.isoformat() if standard.created_date else None,
                    "last_updated": standard.last_updated.isoformat() if standard.last_updated else None,
                    "enabled": standard.enabled
                }
                result.append(standard_dict)
            return result
        except Exception as e:
            logger.error(f"Error getting code standards: {e}")
            return []
    
    def get_current_code_standard(self) -> Optional[Dict[str, Any]]:
        """Get current code standard."""
        try:
            standard = self.llm_manager.get_current_code_standard()
            if not standard:
                return None
            
            # Convert dataclass object to dictionary
            standard_dict: Dict[str, Any] = {
                "name": standard.name,
                "description": standard.description,
                "company": standard.company,
                "version": standard.version,
                "languages": [lang.value for lang in standard.languages],
                "rules": [rule.__dict__ for rule in standard.rules],
                "created_date": standard.created_date.isoformat() if standard.created_date else None,
                "last_updated": standard.last_updated.isoformat() if standard.last_updated else None,
                "enabled": standard.enabled
            }
            return standard_dict
        except Exception as e:
            logger.error(f"Error getting current code standard: {e}")
            return None
    
    def add_code_standard(self, standard_data: Dict[str, Any]):
        """Add a code standard."""
        try:
            from backend.services.code_standards import CodeStandard, CodeRule, Language
            from backend.services.code_standards import Severity
            
            # Convert language strings to Language enum
            languages = []
            for lang in standard_data.get("languages", []):
                if isinstance(lang, str):
                    languages.append(Language(lang))
                elif hasattr(lang, 'value'):  # Handle enum objects
                    languages.append(lang)
                else:
                    languages.append(Language(str(lang)))
            
            # Convert rules
            rules = []
            for rule_data in standard_data.get("rules", []):
                # Handle language conversion in rules too
                rule_language = rule_data["language"]
                if isinstance(rule_language, str):
                    rule_language = Language(rule_language)
                elif hasattr(rule_language, 'value'):  # Handle enum objects
                    rule_language = rule_language
                else:
                    rule_language = Language(str(rule_language))
                
                # Handle severity conversion
                rule_severity = rule_data["severity"]
                if isinstance(rule_severity, str):
                    rule_severity = Severity(rule_severity)
                elif hasattr(rule_severity, 'value'):  # Handle enum objects
                    rule_severity = rule_severity
                else:
                    rule_severity = Severity(str(rule_severity))
                
                rule = CodeRule(
                    id=rule_data["id"],
                    name=rule_data["name"],
                    description=rule_data["description"],
                    language=rule_language,
                    severity=rule_severity,
                    pattern=rule_data["pattern"],
                    message=rule_data["message"],
                    category=rule_data["category"],
                    enabled=rule_data.get("enabled", True),
                    auto_fix=rule_data.get("auto_fix", False),
                    fix_template=rule_data.get("fix_template"),
                    tags=rule_data.get("tags", [])
                )
                rules.append(rule)
            
            standard = CodeStandard(
                name=standard_data["name"],
                description=standard_data["description"],
                company=standard_data.get("company", "Unknown"),
                version=standard_data.get("version", "1.0.0"),
                languages=languages,
                rules=rules,
                enabled=standard_data.get("enabled", True)
            )
            
            self.llm_manager.add_code_standard(standard)
        except Exception as e:
            logger.error(f"Error adding code standard: {e}")
            raise
    
    def remove_code_standard(self, standard_name: str):
        """Remove a code standard."""
        try:
            self.llm_manager.remove_code_standard(standard_name)
        except Exception as e:
            logger.error(f"Error removing code standard: {e}")
            raise
    
    def set_current_code_standard(self, standard_name: str):
        """Set current code standard."""
        try:
            self.llm_manager.set_current_code_standard(standard_name)
        except Exception as e:
            logger.error(f"Error setting current code standard: {e}")
            raise
    
    def analyze_code_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single file for code standard violations."""
        try:
            result = self.llm_manager.analyze_code_file(file_path)
            # Convert dataclass object to dictionary
            result_dict: Dict[str, Any] = {
                "file_path": result.file_path,
                "language": result.language.value,
                "violations": [violation.__dict__ for violation in result.violations],
                "total_violations": result.total_violations,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "info_count": result.info_count,
                "auto_fixable_count": result.auto_fixable_count
            }
            return result_dict
        except Exception as e:
            logger.error(f"Error analyzing code file: {e}")
            return {}
    
    def analyze_code_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """Analyze all files in a directory for code standard violations."""
        try:
            results = self.llm_manager.analyze_code_directory(directory_path)
            # Convert dataclass objects to dictionaries
            result_list: List[Dict[str, Any]] = []
            for result in results:
                result_dict: Dict[str, Any] = {
                    "file_path": result.file_path,
                    "language": result.language.value,
                    "violations": [violation.__dict__ for violation in result.violations],
                    "total_violations": result.total_violations,
                    "error_count": result.error_count,
                    "warning_count": result.warning_count,
                    "info_count": result.info_count,
                    "auto_fixable_count": result.auto_fixable_count
                }
                result_list.append(result_dict)
            return result_list
        except Exception as e:
            logger.error(f"Error analyzing code directory: {e}")
            return []
    
    def export_code_standard(self, standard_name: str, export_path: str):
        """Export a code standard to a file."""
        try:
            self.llm_manager.export_code_standard(standard_name, export_path)
        except Exception as e:
            logger.error(f"Error exporting code standard: {e}")
            raise
    
    def import_code_standard(self, import_path: str):
        """Import a code standard from a file."""
        try:
            self.llm_manager.import_code_standard(import_path)
        except Exception as e:
            logger.error(f"Error importing code standard: {e}")
            raise 