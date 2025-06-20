"""
PR Automation Service

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
PR Automation Service - Automated PR creation with JIRA and ServiceNow integration.
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import shlex
import concurrent.futures
import threading

import httpx
from git import Repo, GitCommandError
from core.config import Config
from core.logging import LogManager
from core.error import ErrorHandler
from core.events import EventBus
from backend.services.intelligent_analyzer import IntelligentCodeAnalyzer
from backend.utils.constants import MAX_FILE_SIZE_KB

# Constants
REVIEW_TIMEOUT_SECONDS = 300  # 5 minutes

logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Configuration for external services (JIRA, ServiceNow)."""
    service_type: str  # "jira" or "servicenow"
    name: str
    base_url: str
    username: str
    api_token: str
    project_key: Optional[str] = None  # JIRA project key
    is_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PRTemplate:
    """PR template configuration."""
    name: str
    title_template: str
    body_template: str
    branch_prefix: str = "feature/"
    auto_assign: bool = True
    labels: List[str] = field(default_factory=list)
    reviewers: List[str] = field(default_factory=list)
    is_default: bool = False


@dataclass
class PRRequest:
    """Request for PR creation."""
    title: str
    description: str
    base_branch: str = "main"
    source_branch: Optional[str] = None
    template_name: Optional[str] = None
    jira_ticket: Optional[str] = None
    servicenow_ticket: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    reviewers: List[str] = field(default_factory=list)
    auto_create_tickets: bool = True


@dataclass
class PRResult:
    """Result of PR creation."""
    success: bool
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    branch_name: Optional[str] = None
    jira_ticket: Optional[str] = None
    servicenow_ticket: Optional[str] = None
    error_message: Optional[str] = None


class JIRAService:
    """JIRA API integration service."""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            auth=(config.username, config.api_token),
            headers={"Accept": "application/json", "Content-Type": "application/json"}
        )
    
    async def create_issue(self, summary: str, description: str, issue_type: str = "Task") -> Optional[str]:
        """Create a JIRA issue and return the issue key."""
        try:
            data = {
                "fields": {
                    "project": {"key": self.config.project_key},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": issue_type}
                }
            }
            
            response = await self.client.post("/rest/api/2/issue", json=data)
            response.raise_for_status()
            result = response.json()
            return result["key"]
            
        except Exception as e:
            logger.error(f"Failed to create JIRA issue: {e}")
            return None
    
    async def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> bool:
        """Update a JIRA issue."""
        try:
            data = {"fields": fields}
            response = await self.client.put(f"/rest/api/2/issue/{issue_key}", json=data)
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update JIRA issue {issue_key}: {e}")
            return False
    
    async def add_comment(self, issue_key: str, comment: str) -> bool:
        """Add a comment to a JIRA issue."""
        try:
            data = {"body": comment}
            response = await self.client.post(f"/rest/api/2/issue/{issue_key}/comment", json=data)
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Failed to add comment to JIRA issue {issue_key}: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test JIRA connection."""
        try:
            response = await self.client.get("/rest/api/2/myself")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"JIRA connection test failed: {e}")
            return False


class ServiceNowService:
    """ServiceNow API integration service."""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            auth=(config.username, config.api_token),
            headers={"Accept": "application/json", "Content-Type": "application/json"}
        )
    
    async def create_change_request(self, short_description: str, description: str) -> Optional[str]:
        """Create a ServiceNow change request and return the ticket number."""
        try:
            data = {
                "short_description": short_description,
                "description": description,
                "type": "change_request",
                "state": "draft"
            }
            
            response = await self.client.post("/api/now/table/change_request", json=data)
            response.raise_for_status()
            result = response.json()
            return result["result"]["number"]
            
        except Exception as e:
            logger.error(f"Failed to create ServiceNow change request: {e}")
            return None
    
    async def update_change_request(self, ticket_number: str, fields: Dict[str, Any]) -> bool:
        """Update a ServiceNow change request."""
        try:
            response = await self.client.put(f"/api/now/table/change_request/{ticket_number}", json=fields)
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update ServiceNow change request {ticket_number}: {e}")
            return False
    
    async def add_comment(self, ticket_number: str, comment: str) -> bool:
        """Add a comment to a ServiceNow ticket."""
        try:
            data = {"value": comment}
            response = await self.client.post(f"/api/now/table/change_request/{ticket_number}/comments", json=data)
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Failed to add comment to ServiceNow ticket {ticket_number}: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test ServiceNow connection."""
        try:
            response = await self.client.get("/api/now/table/sys_user")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"ServiceNow connection test failed: {e}")
            return False


class GitService:
    """Git operations service."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo = Repo(repo_path)
    
    def get_current_branch(self) -> str:
        """Get current branch name."""
        return self.repo.active_branch.name
    
    def create_branch(self, branch_name: str) -> bool:
        """Create and checkout a new branch."""
        try:
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()
            return True
        except GitCommandError as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            return False
    
    def commit_changes(self, message: str) -> bool:
        """Commit current changes."""
        try:
            self.repo.index.add("*")
            self.repo.index.commit(message)
            return True
        except GitCommandError as e:
            logger.error(f"Failed to commit changes: {e}")
            return False
    
    def push_branch(self, branch_name: str) -> bool:
        """Push branch to remote."""
        try:
            origin = self.repo.remote("origin")
            origin.push(branch_name)
            return True
        except GitCommandError as e:
            logger.error(f"Failed to push branch {branch_name}: {e}")
            return False
    
    def get_remote_url(self) -> Optional[str]:
        """Get remote repository URL."""
        try:
            origin = self.repo.remote("origin")
            return origin.url
        except Exception:
            return None


class PRAutomationService:
    """
    PR automation service with intelligent code review and automation.
    Uses the core modules for configuration, logging, error handling, and threading.
    """
    
    def __init__(self):
        self.config = Config()
        self.logger = LogManager().get_logger('pr_automation')
        self.error_handler = ErrorHandler()
        self.event_bus = EventBus()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
        # Initialize analyzers
        self.intelligent_analyzer = IntelligentCodeAnalyzer()
        
        # Thread-safe locks
        self.review_lock = threading.Lock()
        
        # Load configuration
        self.max_file_size_kb = self.config.get('pr_automation.max_file_size_kb', MAX_FILE_SIZE_KB)
        self.review_timeout = self.config.get('pr_automation.timeout_seconds', REVIEW_TIMEOUT_SECONDS)
        
        self.logger.info("PR automation service initialized")
    
    def load_config(self):
        """Load configuration from file."""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                # Load service configurations
                for service_data in data.get("services", []):
                    config = ServiceConfig(**service_data)
                    if config.service_type == "jira":
                        self.services[config.name] = JIRAService(config)
                    elif config.service_type == "servicenow":
                        self.services[config.name] = ServiceNowService(config)
                
                # Load PR templates
                for template_data in data.get("templates", []):
                    template = PRTemplate(**template_data)
                    self.templates[template.name] = template
                    
        except Exception as e:
            logger.error(f"Error loading PR automation config: {e}")
        return data
    
    def save_config(self):
        """Save configuration to file."""
        try:
            config_data = {
                "services": [],
                "templates": []
            }
            
            # Save service configurations
            for service in self.services.values():
                config_data["services"].append(service.config.__dict__)
            
            # Save PR templates
            for template in self.templates.values():
                config_data["templates"].append(template.__dict__)
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving PR automation config: {e}")
    
    def add_service(self, config: ServiceConfig):
        """Add a new service configuration."""
        if config.service_type == "jira":
            self.services[config.name] = JIRAService(config)
        elif config.service_type == "servicenow":
            self.services[config.name] = ServiceNowService(config)
        self.save_config()
    
    def remove_service(self, service_name: str):
        """Remove a service configuration."""
        if service_name in self.services:
            del self.services[service_name]
            self.save_config()
    
    def add_template(self, template: PRTemplate):
        """Add a new PR template."""
        self.templates[template.name] = template
        self.save_config()
    
    def remove_template(self, template_name: str):
        """Remove a PR template."""
        if template_name in self.templates:
            del self.templates[template_name]
            self.save_config()
    
    def get_default_template(self) -> Optional[PRTemplate]:
        """Get the default PR template."""
        for template in self.templates.values():
            if template.is_default:
                return template
        return None
    
    async def create_pr(self, request: PRRequest, repo_path: str) -> PRResult:
        """Create a PR with optional ticket creation."""
        try:
            # Initialize git service
            git_service = GitService(repo_path)
            
            # Get template
            template = None
            if request.template_name:
                template = self.templates.get(request.template_name)
            if not template:
                template = self.get_default_template()
            
            if not template:
                return PRResult(success=False, error_message="No PR template available")
            
            # Generate branch name
            if request.source_branch:
                branch_name = request.source_branch
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', request.title)
                branch_name = f"{template.branch_prefix}{safe_title}_{timestamp}"
            
            # Create branch
            if not git_service.create_branch(branch_name):
                return PRResult(success=False, error_message="Failed to create branch")
            
            # Create tickets if requested
            jira_ticket = None
            servicenow_ticket = None
            
            if request.auto_create_tickets:
                # Create JIRA ticket
                if request.jira_ticket:
                    jira_ticket = request.jira_ticket
                else:
                    for service in self.services.values():
                        if isinstance(service, JIRAService):
                            jira_ticket = await service.create_issue(
                                summary=request.title,
                                description=request.description
                            )
                            break
                
                # Create ServiceNow ticket
                for service in self.services.values():
                    if isinstance(service, ServiceNowService):
                        servicenow_ticket = await service.create_change_request(
                            short_description=request.title,
                            description=request.description
                        )
                        break
            
            # Generate PR title and body
            pr_title = template.title_template.format(
                title=request.title,
                jira_ticket=jira_ticket or "",
                servicenow_ticket=servicenow_ticket or ""
            )
            
            pr_body = template.body_template.format(
                description=request.description,
                jira_ticket=jira_ticket or "N/A",
                servicenow_ticket=servicenow_ticket or "N/A",
                branch_name=branch_name,
                base_branch=request.base_branch
            )
            
            # Add ticket links to PR body
            if jira_ticket:
                jira_service = next((s for s in self.services.values() if isinstance(s, JIRAService)), None)
                if jira_service:
                    jira_url = f"{jira_service.config.base_url}/browse/{jira_ticket}"
                    pr_body += f"\n\n**JIRA Ticket:** [{jira_ticket}]({jira_url})"
            
            if servicenow_ticket:
                servicenow_service = next((s for s in self.services.values() if isinstance(s, ServiceNowService)), None)
                if servicenow_service:
                    servicenow_url = f"{servicenow_service.config.base_url}/nav_to.do?uri=change_request.do?sys_id={servicenow_ticket}"
                    pr_body += f"\n\n**ServiceNow Ticket:** [{servicenow_ticket}]({servicenow_url})"
            
            # Commit changes
            if not git_service.commit_changes(f"feat: {request.title}"):
                return PRResult(success=False, error_message="Failed to commit changes")
            
            # Push branch
            if not git_service.push_branch(branch_name):
                return PRResult(success=False, error_message="Failed to push branch")
            
            # Create PR using GitHub CLI or API
            pr_url = await self._create_github_pr(
                repo_path, branch_name, request.base_branch, pr_title, pr_body, request.labels, request.reviewers
            )
            
            return PRResult(
                success=True,
                pr_url=pr_url,
                branch_name=branch_name,
                jira_ticket=jira_ticket,
                servicenow_ticket=servicenow_ticket
            )
            
        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
            return PRResult(success=False, error_message=str(e))
    
    async def _create_github_pr(self, repo_path: str, branch: str, base: str, title: str, body: str, labels: List[str], reviewers: List[str]) -> Optional[str]:
        """Create GitHub PR using GitHub CLI."""
        try:
            # Sanitize all inputs to prevent command injection
            sanitized_title = shlex.quote(title)
            sanitized_body = shlex.quote(body)
            sanitized_branch = shlex.quote(branch)
            sanitized_base = shlex.quote(base)
            
            # Sanitize labels and reviewers
            sanitized_labels = [shlex.quote(label) for label in labels]
            sanitized_reviewers = [shlex.quote(reviewer) for reviewer in reviewers]
            
            cmd = ["gh", "pr", "create", "--title", sanitized_title, "--body", sanitized_body, "--head", sanitized_branch, "--base", sanitized_base]
            
            if sanitized_labels:
                cmd.extend(["--label", ",".join(sanitized_labels)])
            
            if sanitized_reviewers:
                cmd.extend(["--reviewer", ",".join(sanitized_reviewers)])
            
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Extract PR URL from output
                for line in result.stdout.split('\n'):
                    if line.startswith('https://github.com/'):
                        return line.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create GitHub PR: {e}")
            return None
    
    async def test_service_connection(self, service_name: str) -> bool:
        """Test connection to a specific service."""
        if service_name not in self.services:
            return False
        
        service = self.services[service_name]
        if isinstance(service, JIRAService):
            return await service.test_connection()
        elif isinstance(service, ServiceNowService):
            return await service.test_connection()
        
        return False


# Global instance
pr_automation_service = PRAutomationService() 