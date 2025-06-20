"""
API Service

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
API Service - REST API endpoints for PR automation and external integrations.
"""

import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from .llm_manager import LLMManager
from .pr_automation import ServiceConfig, PRTemplate, PRRequest
from .security_intelligence import SecurityFeed
from .code_standards import CodeStandard, CodeRule, Language, Severity

logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class ServiceConfigRequest(BaseModel):
    service_type: str
    name: str
    base_url: str
    username: str
    api_token: str
    project_key: Optional[str] = None
    is_enabled: bool = True


class ServiceConfigResponse(BaseModel):
    name: str
    service_type: str
    base_url: str
    username: str
    project_key: Optional[str] = None
    is_enabled: bool


class PRTemplateRequest(BaseModel):
    name: str
    title_template: str
    body_template: str
    branch_prefix: str = "feature/"
    auto_assign: bool = True
    labels: List[str] = Field(default_factory=list)
    reviewers: List[str] = Field(default_factory=list)
    is_default: bool = False


class PRTemplateResponse(BaseModel):
    name: str
    title_template: str
    body_template: str
    branch_prefix: str
    auto_assign: bool
    labels: List[str]
    reviewers: List[str]
    is_default: bool


class PRCreationRequest(BaseModel):
    title: str
    description: str
    base_branch: str = "main"
    source_branch: Optional[str] = None
    template_name: Optional[str] = None
    jira_ticket: Optional[str] = None
    servicenow_ticket: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    reviewers: List[str] = Field(default_factory=list)
    auto_create_tickets: bool = True
    repo_path: str


class PRCreationResponse(BaseModel):
    success: bool
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    branch_name: Optional[str] = None
    jira_ticket: Optional[str] = None
    servicenow_ticket: Optional[str] = None
    error_message: Optional[str] = None


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str


class ConfigResponse(BaseModel):
    services: List[ServiceConfigResponse]
    templates: List[PRTemplateResponse]


# Security Intelligence Models
class SecurityFeedRequest(BaseModel):
    name: str
    url: str
    feed_type: str
    enabled: bool = True
    fetch_interval: int = 3600
    tags: List[str] = Field(default_factory=list)


class SecurityFeedResponse(BaseModel):
    name: str
    url: str
    feed_type: str
    enabled: bool
    last_fetch: Optional[str] = None
    fetch_interval: int
    tags: List[str]


class SecurityVulnerabilityResponse(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    cvss_score: Optional[float] = None
    affected_products: List[str]
    published_date: Optional[str] = None
    source: str
    tags: List[str]
    is_patched: bool
    patch_available: bool


class SecurityBreachResponse(BaseModel):
    id: str
    title: str
    description: str
    company: str
    breach_date: Optional[str] = None
    affected_users: Optional[int] = None
    data_types: List[str]
    attack_vector: str
    severity: str
    source: str
    lessons_learned: List[str]
    mitigation_strategies: List[str]


class SecurityPatchResponse(BaseModel):
    id: str
    title: str
    description: str
    affected_products: List[str]
    patch_version: str
    release_date: Optional[str] = None
    severity: str
    source: str
    download_url: str
    installation_instructions: str
    tested: bool
    applied: bool


# Code Standards Models
class CodeRuleRequest(BaseModel):
    id: str
    name: str
    description: str
    language: str
    severity: str
    pattern: str
    message: str
    category: str
    enabled: bool = True
    auto_fix: bool = False
    fix_template: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class CodeRuleResponse(BaseModel):
    id: str
    name: str
    description: str
    language: str
    severity: str
    pattern: str
    message: str
    category: str
    enabled: bool
    auto_fix: bool
    fix_template: Optional[str] = None
    tags: List[str]


class CodeStandardRequest(BaseModel):
    name: str
    description: str
    company: str
    version: str
    languages: List[str] = Field(default_factory=list)
    rules: List[CodeRuleRequest] = Field(default_factory=list)
    enabled: bool = True


class CodeStandardResponse(BaseModel):
    name: str
    description: str
    company: str
    version: str
    languages: List[str]
    rules: List[CodeRuleResponse]
    created_date: str
    last_updated: str
    enabled: bool


class CodeViolationResponse(BaseModel):
    rule_id: str
    rule_name: str
    severity: str
    message: str
    line_number: int
    column: int
    line_content: str
    file_path: str
    category: str
    auto_fixable: bool
    suggested_fix: Optional[str] = None


class CodeAnalysisResponse(BaseModel):
    file_path: str
    language: str
    violations: List[CodeViolationResponse]
    total_violations: int
    error_count: int
    warning_count: int
    info_count: int
    auto_fixable_count: int


# FastAPI app
app = FastAPI(
    title="AI Coder Assistant API",
    description="API for PR automation, security intelligence, and code standards",
    version="2.4.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global LLM manager instance
llm_manager = LLMManager()


# Dependency to get LLM manager
def get_llm_manager() -> LLMManager:
    return llm_manager


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.3.0"}


# Service Configuration Endpoints

@app.get("/api/services", response_model=List[ServiceConfigResponse])
async def list_services(llm_manager: LLMManager = Depends(get_llm_manager)):
    """List all configured services."""
    try:
        services = llm_manager.list_service_configs()
        return [
            ServiceConfigResponse(
                name=service.name,
                service_type=service.service_type,
                base_url=service.base_url,
                username=service.username,
                project_key=service.project_key,
                is_enabled=service.is_enabled
            )
            for service in services
        ]
    except Exception as e:
        logger.error(f"Error listing services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/services", response_model=ServiceConfigResponse)
async def add_service(
    service_config: ServiceConfigRequest,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Add a new service configuration."""
    try:
        config = ServiceConfig(
            service_type=service_config.service_type,
            name=service_config.name,
            base_url=service_config.base_url,
            username=service_config.username,
            api_token=service_config.api_token,
            project_key=service_config.project_key,
            is_enabled=service_config.is_enabled
        )
        
        llm_manager.add_service_config(config)
        
        return ServiceConfigResponse(
            name=config.name,
            service_type=config.service_type,
            base_url=config.base_url,
            username=config.username,
            project_key=config.project_key,
            is_enabled=config.is_enabled
        )
    except Exception as e:
        logger.error(f"Error adding service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/services/{service_name}")
async def remove_service(
    service_name: str,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Remove a service configuration."""
    try:
        llm_manager.remove_service_config(service_name)
        return {"message": f"Service {service_name} removed successfully"}
    except Exception as e:
        logger.error(f"Error removing service: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/services/{service_name}/test", response_model=ConnectionTestResponse)
async def test_service_connection(
    service_name: str,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Test connection to a specific service."""
    try:
        success = await llm_manager.test_service_connection(service_name)
        return ConnectionTestResponse(
            success=success,
            message="Connection successful" if success else "Connection failed"
        )
    except Exception as e:
        logger.error(f"Error testing service connection: {e}")
        return ConnectionTestResponse(
            success=False,
            message=str(e)
        )


# PR Template Endpoints

@app.get("/api/templates", response_model=List[PRTemplateResponse])
async def list_templates(llm_manager: LLMManager = Depends(get_llm_manager)):
    """List all PR templates."""
    try:
        templates = llm_manager.list_pr_templates()
        return [
            PRTemplateResponse(
                name=template.name,
                title_template=template.title_template,
                body_template=template.body_template,
                branch_prefix=template.branch_prefix,
                auto_assign=template.auto_assign,
                labels=template.labels,
                reviewers=template.reviewers,
                is_default=template.is_default
            )
            for template in templates
        ]
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/templates", response_model=PRTemplateResponse)
async def add_template(
    template: PRTemplateRequest,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Add a new PR template."""
    try:
        pr_template = PRTemplate(
            name=template.name,
            title_template=template.title_template,
            body_template=template.body_template,
            branch_prefix=template.branch_prefix,
            auto_assign=template.auto_assign,
            labels=template.labels,
            reviewers=template.reviewers,
            is_default=template.is_default
        )
        
        llm_manager.add_pr_template(pr_template)
        
        return PRTemplateResponse(
            name=pr_template.name,
            title_template=pr_template.title_template,
            body_template=pr_template.body_template,
            branch_prefix=pr_template.branch_prefix,
            auto_assign=pr_template.auto_assign,
            labels=pr_template.labels,
            reviewers=pr_template.reviewers,
            is_default=pr_template.is_default
        )
    except Exception as e:
        logger.error(f"Error adding template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/templates/{template_name}")
async def remove_template(
    template_name: str,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Remove a PR template."""
    try:
        llm_manager.remove_pr_template(template_name)
        return {"message": f"Template {template_name} removed successfully"}
    except Exception as e:
        logger.error(f"Error removing template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/templates/default", response_model=Optional[PRTemplateResponse])
async def get_default_template(llm_manager: LLMManager = Depends(get_llm_manager)):
    """Get the default PR template."""
    try:
        template = llm_manager.get_default_pr_template()
        if template:
            return PRTemplateResponse(
                name=template.name,
                title_template=template.title_template,
                body_template=template.body_template,
                branch_prefix=template.branch_prefix,
                auto_assign=template.auto_assign,
                labels=template.labels,
                reviewers=template.reviewers,
                is_default=template.is_default
            )
        return None
    except Exception as e:
        logger.error(f"Error getting default template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# PR Creation Endpoints

@app.post("/api/pr/create", response_model=PRCreationResponse)
async def create_pr(
    request: PRCreationRequest,
    background_tasks: BackgroundTasks,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Create a PR with optional ticket creation."""
    try:
        pr_request = PRRequest(
            title=request.title,
            description=request.description,
            base_branch=request.base_branch,
            source_branch=request.source_branch,
            template_name=request.template_name,
            jira_ticket=request.jira_ticket,
            servicenow_ticket=request.servicenow_ticket,
            labels=request.labels,
            reviewers=request.reviewers,
            auto_create_tickets=request.auto_create_tickets
        )
        
        result = await llm_manager.create_pr(pr_request, request.repo_path)
        
        return PRCreationResponse(
            success=result.success,
            pr_url=result.pr_url,
            pr_number=result.pr_number,
            branch_name=result.branch_name,
            jira_ticket=result.jira_ticket,
            servicenow_ticket=result.servicenow_ticket,
            error_message=result.error_message
        )
    except Exception as e:
        logger.error(f"Error creating PR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Configuration Endpoints

@app.get("/api/config", response_model=ConfigResponse)
async def get_config(llm_manager: LLMManager = Depends(get_llm_manager)):
    """Get complete PR automation configuration."""
    try:
        config = llm_manager.get_pr_automation_config()
        
        services = [
            ServiceConfigResponse(
                name=service["name"],
                service_type=service["service_type"],
                base_url=service["base_url"],
                username=service["username"],
                project_key=service.get("project_key"),
                is_enabled=service["is_enabled"]
            )
            for service in config["services"]
        ]
        
        templates = [
            PRTemplateResponse(
                name=template["name"],
                title_template=template["title_template"],
                body_template=template["body_template"],
                branch_prefix=template["branch_prefix"],
                auto_assign=template["auto_assign"],
                labels=template["labels"],
                reviewers=template["reviewers"],
                is_default=template["is_default"]
            )
            for template in config["templates"]
        ]
        
        return ConfigResponse(services=services, templates=templates)
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# JIRA Integration Endpoints

@app.post("/api/jira/issues")
async def create_jira_issue(
    summary: str,
    description: str,
    issue_type: str = "Task",
    service_name: Optional[str] = None,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Create a JIRA issue."""
    try:
        # Find JIRA service
        services = llm_manager.list_service_configs()
        jira_service = None
        
        if service_name:
            # Find specific service
            for service in services:
                if service.name == service_name and service.service_type == "jira":
                    jira_service = service
                    break
        else:
            # Find first JIRA service
            for service in services:
                if service.service_type == "jira" and service.is_enabled:
                    jira_service = service
                    break
        
        if not jira_service:
            raise HTTPException(status_code=404, detail="No JIRA service configured")
        
        # Create issue using the PR automation service
        pr_automation = llm_manager.pr_automation
        jira_provider = pr_automation.services.get(jira_service.name)
        
        if not jira_provider:
            raise HTTPException(status_code=404, detail="JIRA service not found")
        
        issue_key = await jira_provider.create_issue(summary, description, issue_type)
        
        if issue_key:
            return {"success": True, "issue_key": issue_key}
        else:
            raise HTTPException(status_code=500, detail="Failed to create JIRA issue")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating JIRA issue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ServiceNow Integration Endpoints

@app.post("/api/servicenow/change-requests")
async def create_servicenow_change_request(
    short_description: str,
    description: str,
    service_name: Optional[str] = None,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Create a ServiceNow change request."""
    try:
        # Find ServiceNow service
        services = llm_manager.list_service_configs()
        servicenow_service = None
        
        if service_name:
            # Find specific service
            for service in services:
                if service.name == service_name and service.service_type == "servicenow":
                    servicenow_service = service
                    break
        else:
            # Find first ServiceNow service
            for service in services:
                if service.service_type == "servicenow" and service.is_enabled:
                    servicenow_service = service
                    break
        
        if not servicenow_service:
            raise HTTPException(status_code=404, detail="No ServiceNow service configured")
        
        # Create change request using the PR automation service
        pr_automation = llm_manager.pr_automation
        servicenow_provider = pr_automation.services.get(servicenow_service.name)
        
        if not servicenow_provider:
            raise HTTPException(status_code=404, detail="ServiceNow service not found")
        
        ticket_number = await servicenow_provider.create_change_request(short_description, description)
        
        if ticket_number:
            return {"success": True, "ticket_number": ticket_number}
        else:
            raise HTTPException(status_code=500, detail="Failed to create ServiceNow change request")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ServiceNow change request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Security Intelligence Endpoints

@app.get("/api/security/feeds", response_model=List[SecurityFeedResponse])
async def list_security_feeds(llm_manager: LLMManager = Depends(get_llm_manager)):
    """List all configured security feeds."""
    try:
        feeds = llm_manager.get_security_feeds()
        return [
            SecurityFeedResponse(
                name=feed.name,
                url=feed.url,
                feed_type=feed.feed_type,
                enabled=feed.enabled,
                last_fetch=feed.last_fetch.isoformat() if feed.last_fetch else None,
                fetch_interval=feed.fetch_interval,
                tags=feed.tags
            )
            for feed in feeds
        ]
    except Exception as e:
        logger.error(f"Error listing security feeds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/security/feeds", response_model=SecurityFeedResponse)
async def add_security_feed(
    feed: SecurityFeedRequest,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Add a new security feed."""
    try:
        security_feed = SecurityFeed(
            name=feed.name,
            url=feed.url,
            feed_type=feed.feed_type,
            enabled=feed.enabled,
            fetch_interval=feed.fetch_interval,
            tags=feed.tags
        )
        
        llm_manager.add_security_feed(security_feed)
        
        return SecurityFeedResponse(
            name=security_feed.name,
            url=security_feed.url,
            feed_type=security_feed.feed_type,
            enabled=security_feed.enabled,
            last_fetch=None,
            fetch_interval=security_feed.fetch_interval,
            tags=security_feed.tags
        )
    except Exception as e:
        logger.error(f"Error adding security feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/security/feeds/{feed_name}")
async def remove_security_feed(
    feed_name: str,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Remove a security feed."""
    try:
        llm_manager.remove_security_feed(feed_name)
        return {"success": True, "message": f"Security feed '{feed_name}' removed"}
    except Exception as e:
        logger.error(f"Error removing security feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/security/feeds/fetch")
async def fetch_security_feeds(llm_manager: LLMManager = Depends(get_llm_manager)):
    """Fetch security data from all configured feeds."""
    try:
        await llm_manager.fetch_security_feeds()
        return {"success": True, "message": "Security feeds fetched successfully"}
    except Exception as e:
        logger.error(f"Error fetching security feeds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/security/vulnerabilities", response_model=List[SecurityVulnerabilityResponse])
async def get_security_vulnerabilities(
    severity: Optional[str] = None,
    limit: int = 100,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Get security vulnerabilities with optional filtering."""
    try:
        vulnerabilities = llm_manager.get_security_vulnerabilities(severity, limit)
        return [
            SecurityVulnerabilityResponse(
                id=vuln.id,
                title=vuln.title,
                description=vuln.description,
                severity=vuln.severity,
                cvss_score=vuln.cvss_score,
                affected_products=vuln.affected_products,
                published_date=vuln.published_date.isoformat() if vuln.published_date else None,
                source=vuln.source,
                tags=vuln.tags,
                is_patched=vuln.is_patched,
                patch_available=vuln.patch_available
            )
            for vuln in vulnerabilities
        ]
    except Exception as e:
        logger.error(f"Error getting vulnerabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/security/breaches", response_model=List[SecurityBreachResponse])
async def get_security_breaches(
    limit: int = 100,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Get security breaches."""
    try:
        breaches = llm_manager.get_security_breaches(limit)
        return [
            SecurityBreachResponse(
                id=breach.id,
                title=breach.title,
                description=breach.description,
                company=breach.company,
                breach_date=breach.breach_date.isoformat() if breach.breach_date else None,
                affected_users=breach.affected_users,
                data_types=breach.data_types,
                attack_vector=breach.attack_vector,
                severity=breach.severity,
                source=breach.source,
                lessons_learned=breach.lessons_learned,
                mitigation_strategies=breach.mitigation_strategies
            )
            for breach in breaches
        ]
    except Exception as e:
        logger.error(f"Error getting breaches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/security/patches", response_model=List[SecurityPatchResponse])
async def get_security_patches(
    limit: int = 100,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Get security patches."""
    try:
        patches = llm_manager.get_security_patches(limit)
        return [
            SecurityPatchResponse(
                id=patch.id,
                title=patch.title,
                description=patch.description,
                affected_products=patch.affected_products,
                patch_version=patch.patch_version,
                release_date=patch.release_date.isoformat() if patch.release_date else None,
                severity=patch.severity,
                source=patch.source,
                download_url=patch.download_url,
                installation_instructions=patch.installation_instructions,
                tested=patch.tested,
                applied=patch.applied
            )
            for patch in patches
        ]
    except Exception as e:
        logger.error(f"Error getting patches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/security/training-data")
async def get_security_training_data(
    limit: int = 1000,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Get security training data for AI models."""
    try:
        training_data = llm_manager.get_security_training_data(limit)
        return {"training_data": training_data}
    except Exception as e:
        logger.error(f"Error getting training data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/security/patches/{patch_id}/apply")
async def apply_security_patch(
    patch_id: str,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Mark a security patch as applied."""
    try:
        llm_manager.mark_patch_applied(patch_id)
        return {"success": True, "message": f"Patch '{patch_id}' marked as applied"}
    except Exception as e:
        logger.error(f"Error applying patch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/security/vulnerabilities/{vuln_id}/patch")
async def mark_vulnerability_patched(
    vuln_id: str,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Mark a vulnerability as patched."""
    try:
        llm_manager.mark_vulnerability_patched(vuln_id)
        return {"success": True, "message": f"Vulnerability '{vuln_id}' marked as patched"}
    except Exception as e:
        logger.error(f"Error marking vulnerability as patched: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Code Standards Endpoints

@app.get("/api/code-standards", response_model=List[CodeStandardResponse])
async def list_code_standards(llm_manager: LLMManager = Depends(get_llm_manager)):
    """List all code standards."""
    try:
        standards = llm_manager.get_code_standards()
        return [
            CodeStandardResponse(
                name=standard.name,
                description=standard.description,
                company=standard.company,
                version=standard.version,
                languages=[lang.value for lang in standard.languages],
                rules=[
                    CodeRuleResponse(
                        id=rule.id,
                        name=rule.name,
                        description=rule.description,
                        language=rule.language.value,
                        severity=rule.severity.value,
                        pattern=rule.pattern,
                        message=rule.message,
                        category=rule.category,
                        enabled=rule.enabled,
                        auto_fix=rule.auto_fix,
                        fix_template=rule.fix_template,
                        tags=rule.tags
                    )
                    for rule in standard.rules
                ],
                created_date=standard.created_date.isoformat(),
                last_updated=standard.last_updated.isoformat(),
                enabled=standard.enabled
            )
            for standard in standards
        ]
    except Exception as e:
        logger.error(f"Error listing code standards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/code-standards", response_model=CodeStandardResponse)
async def add_code_standard(
    standard: CodeStandardRequest,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Add a new code standard."""
    try:
        # Convert language strings to Language enum
        languages = [Language(lang) for lang in standard.languages]
        
        # Convert rules
        rules = []
        for rule_data in standard.rules:
            rule = CodeRule(
                id=rule_data.id,
                name=rule_data.name,
                description=rule_data.description,
                language=Language(rule_data.language),
                severity=Severity(rule_data.severity),
                pattern=rule_data.pattern,
                message=rule_data.message,
                category=rule_data.category,
                enabled=rule_data.enabled,
                auto_fix=rule_data.auto_fix,
                fix_template=rule_data.fix_template,
                tags=rule_data.tags
            )
            rules.append(rule)
        
        code_standard = CodeStandard(
            name=standard.name,
            description=standard.description,
            company=standard.company,
            version=standard.version,
            languages=languages,
            rules=rules,
            enabled=standard.enabled
        )
        
        llm_manager.add_code_standard(code_standard)
        
        return CodeStandardResponse(
            name=code_standard.name,
            description=code_standard.description,
            company=code_standard.company,
            version=code_standard.version,
            languages=[lang.value for lang in code_standard.languages],
            rules=[
                CodeRuleResponse(
                    id=rule.id,
                    name=rule.name,
                    description=rule.description,
                    language=rule.language.value,
                    severity=rule.severity.value,
                    pattern=rule.pattern,
                    message=rule.message,
                    category=rule.category,
                    enabled=rule.enabled,
                    auto_fix=rule.auto_fix,
                    fix_template=rule.fix_template,
                    tags=rule.tags
                )
                for rule in code_standard.rules
            ],
            created_date=code_standard.created_date.isoformat(),
            last_updated=code_standard.last_updated.isoformat(),
            enabled=code_standard.enabled
        )
    except Exception as e:
        logger.error(f"Error adding code standard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/code-standards/{standard_name}")
async def remove_code_standard(
    standard_name: str,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Remove a code standard."""
    try:
        llm_manager.remove_code_standard(standard_name)
        return {"success": True, "message": f"Code standard '{standard_name}' removed"}
    except Exception as e:
        logger.error(f"Error removing code standard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/code-standards/current", response_model=Optional[CodeStandardResponse])
async def get_current_code_standard(llm_manager: LLMManager = Depends(get_llm_manager)):
    """Get the current active code standard."""
    try:
        standard = llm_manager.get_current_code_standard()
        if not standard:
            return None
        
        return CodeStandardResponse(
            name=standard.name,
            description=standard.description,
            company=standard.company,
            version=standard.version,
            languages=[lang.value for lang in standard.languages],
            rules=[
                CodeRuleResponse(
                    id=rule.id,
                    name=rule.name,
                    description=rule.description,
                    language=rule.language.value,
                    severity=rule.severity.value,
                    pattern=rule.pattern,
                    message=rule.message,
                    category=rule.category,
                    enabled=rule.enabled,
                    auto_fix=rule.auto_fix,
                    fix_template=rule.fix_template,
                    tags=rule.tags
                )
                for rule in standard.rules
            ],
            created_date=standard.created_date.isoformat(),
            last_updated=standard.last_updated.isoformat(),
            enabled=standard.enabled
        )
    except Exception as e:
        logger.error(f"Error getting current code standard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/code-standards/{standard_name}/set-current")
async def set_current_code_standard(
    standard_name: str,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Set the current active code standard."""
    try:
        llm_manager.set_current_code_standard(standard_name)
        return {"success": True, "message": f"Code standard '{standard_name}' set as current"}
    except Exception as e:
        logger.error(f"Error setting current code standard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/code-standards/analyze-file", response_model=CodeAnalysisResponse)
async def analyze_code_file(
    file_path: str,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Analyze a single file for code standard violations."""
    try:
        result = llm_manager.analyze_code_file(file_path)
        return CodeAnalysisResponse(
            file_path=result.file_path,
            language=result.language.value,
            violations=[
                CodeViolationResponse(
                    rule_id=violation.rule_id,
                    rule_name=violation.rule_name,
                    severity=violation.severity.value,
                    message=violation.message,
                    line_number=violation.line_number,
                    column=violation.column,
                    line_content=violation.line_content,
                    file_path=violation.file_path,
                    category=violation.category,
                    auto_fixable=violation.auto_fixable,
                    suggested_fix=violation.suggested_fix
                )
                for violation in result.violations
            ],
            total_violations=result.total_violations,
            error_count=result.error_count,
            warning_count=result.warning_count,
            info_count=result.info_count,
            auto_fixable_count=result.auto_fixable_count
        )
    except Exception as e:
        logger.error(f"Error analyzing code file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/code-standards/analyze-directory")
async def analyze_code_directory(
    directory_path: str,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Analyze all files in a directory for code standard violations."""
    try:
        results = llm_manager.analyze_code_directory(directory_path)
        return {
            "results": [
                CodeAnalysisResponse(
                    file_path=result.file_path,
                    language=result.language.value,
                    violations=[
                        CodeViolationResponse(
                            rule_id=violation.rule_id,
                            rule_name=violation.rule_name,
                            severity=violation.severity.value,
                            message=violation.message,
                            line_number=violation.line_number,
                            column=violation.column,
                            line_content=violation.line_content,
                            file_path=violation.file_path,
                            category=violation.category,
                            auto_fixable=violation.auto_fixable,
                            suggested_fix=violation.suggested_fix
                        )
                        for violation in result.violations
                    ],
                    total_violations=result.total_violations,
                    error_count=result.error_count,
                    warning_count=result.warning_count,
                    info_count=result.info_count,
                    auto_fixable_count=result.auto_fixable_count
                )
                for result in results
            ]
        }
    except Exception as e:
        logger.error(f"Error analyzing code directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/code-standards/export/{standard_name}")
async def export_code_standard(
    standard_name: str,
    export_path: str,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Export a code standard to a file."""
    try:
        llm_manager.export_code_standard(standard_name, export_path)
        return {"success": True, "message": f"Code standard '{standard_name}' exported to {export_path}"}
    except Exception as e:
        logger.error(f"Error exporting code standard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/code-standards/import")
async def import_code_standard(
    import_path: str,
    llm_manager: LLMManager = Depends(get_llm_manager)
):
    """Import a code standard from a file."""
    try:
        llm_manager.import_code_standard(import_path)
        return {"success": True, "message": f"Code standard imported from {import_path}"}
    except Exception as e:
        logger.error(f"Error importing code standard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Run the API server
def run_api_server(host: str = "0.0.0.0", port: int = 8000):  # nosec B104 - Web server needs to bind to all interfaces
    """Run the API server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_api_server() 