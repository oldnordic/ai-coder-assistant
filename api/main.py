#!/usr/bin/env python3
"""
AI Coder Assistant REST API
Provides programmatic access to code analysis and security scanning features
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn
import logging

# Import our modules
from src.core.scanner import CodeScanner
from src.core.intelligent_analyzer import IntelligentAnalyzer
from src.core.ai_tools import AITools
from src.config.settings import Settings
from src.core import scanner, ai_tools, ollama_client
from src.processing import acquire
from src.training import trainer
from src.config import settings
from src.cli.git_utils import PRCreationConfig, create_ai_powered_pr
from src.llm_studio import LLMManager
from src.llm_studio.models import ProviderConfig, ProviderType, ChatMessage, ModelInfo

# Initialize FastAPI app
app = FastAPI(
    title="AI Coder Assistant API",
    description="REST API for AI-powered code analysis and security scanning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize components
settings = Settings()
scanner = CodeScanner()
analyzer = IntelligentAnalyzer()
ai_tools = AITools()

# Pydantic models
class ScanRequest(BaseModel):
    """Request model for code scanning"""
    path: str = Field(..., description="Path to scan")
    language: Optional[str] = Field(None, description="Programming language")
    severity_filter: Optional[List[str]] = Field(None, description="Filter by severity levels")
    type_filter: Optional[List[str]] = Field(None, description="Filter by issue types")
    compliance: Optional[List[str]] = Field(None, description="Compliance standards to check")
    output_format: str = Field("json", description="Output format (json, sarif, junit)")

class SecurityScanRequest(BaseModel):
    """Request model for security scanning"""
    path: str = Field(..., description="Path to scan")
    compliance: Optional[List[str]] = Field(None, description="Compliance standards to check")
    output_format: str = Field("json", description="Output format (json, sarif, junit)")

class AnalyzeRequest(BaseModel):
    """Request model for file analysis"""
    file_path: str = Field(..., description="Path to file to analyze")
    language: str = Field(..., description="Programming language")
    include_suggestions: bool = Field(True, description="Include AI suggestions")

class ScanResult(BaseModel):
    """Response model for scan results"""
    file_path: str
    line_number: int
    severity: str
    issue_type: str
    description: str
    suggestion: str
    compliance_standards: Optional[List[str]] = None

class ScanResponse(BaseModel):
    """Response model for scan operations"""
    success: bool
    message: str
    results: List[ScanResult]
    summary: Dict[str, Any]
    timestamp: datetime
    scan_duration: float

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    components: Dict[str, str]

# Authentication dependency
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API token"""
    # In production, implement proper token validation
    # For now, accept any valid Bearer token
    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(),
        components={
            "scanner": "operational",
            "analyzer": "operational",
            "ai_tools": "operational"
        }
    )

# Scan endpoint
@app.post("/scan", response_model=ScanResponse)
async def scan_code(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Scan code for quality issues"""
    try:
        start_time = datetime.now()
        
        # Validate path
        if not os.path.exists(request.path):
            raise HTTPException(status_code=404, detail="Path not found")
        
        # Perform scan
        results = await asyncio.to_thread(
            scanner.scan_directory,
            request.path,
            language=request.language,
            severity_filter=request.severity_filter,
            type_filter=request.type_filter,
            compliance=request.compliance
        )
        
        # Convert results to response format
        scan_results = []
        for result in results:
            scan_results.append(ScanResult(
                file_path=result.get('file_path', ''),
                line_number=result.get('line_number', 0),
                severity=result.get('severity', 'unknown'),
                issue_type=result.get('issue_type', 'unknown'),
                description=result.get('description', ''),
                suggestion=result.get('suggestion', ''),
                compliance_standards=result.get('compliance_standards', [])
            ))
        
        # Generate summary
        summary = {
            "total_issues": len(scan_results),
            "by_severity": {},
            "by_type": {},
            "by_language": {}
        }
        
        for result in scan_results:
            # Count by severity
            severity = result.severity
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            
            # Count by type
            issue_type = result.issue_type
            summary["by_type"][issue_type] = summary["by_type"].get(issue_type, 0) + 1
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return ScanResponse(
            success=True,
            message=f"Scan completed successfully. Found {len(scan_results)} issues.",
            results=scan_results,
            summary=summary,
            timestamp=end_time,
            scan_duration=duration
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

# Security scan endpoint
@app.post("/security-scan", response_model=ScanResponse)
async def security_scan(
    request: SecurityScanRequest,
    background_tasks: BackgroundTasks,
    token: str = Depends(verify_token)
):
    """Perform security-focused scan"""
    try:
        start_time = datetime.now()
        
        # Validate path
        if not os.path.exists(request.path):
            raise HTTPException(status_code=404, detail="Path not found")
        
        # Perform security scan
        results = await asyncio.to_thread(
            scanner.security_scan,
            request.path,
            compliance=request.compliance or ["owasp", "cwe", "pci"]
        )
        
        # Convert results to response format
        scan_results = []
        for result in results:
            scan_results.append(ScanResult(
                file_path=result.get('file_path', ''),
                line_number=result.get('line_number', 0),
                severity=result.get('severity', 'unknown'),
                issue_type=result.get('issue_type', 'security_vulnerability'),
                description=result.get('description', ''),
                suggestion=result.get('suggestion', ''),
                compliance_standards=result.get('compliance_standards', [])
            ))
        
        # Generate summary
        summary = {
            "total_security_issues": len(scan_results),
            "critical_issues": len([r for r in scan_results if r.severity == 'critical']),
            "high_issues": len([r for r in scan_results if r.severity == 'high']),
            "by_compliance": {}
        }
        
        for result in scan_results:
            for standard in result.compliance_standards or []:
                summary["by_compliance"][standard] = summary["by_compliance"].get(standard, 0) + 1
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return ScanResponse(
            success=True,
            message=f"Security scan completed. Found {len(scan_results)} security issues.",
            results=scan_results,
            summary=summary,
            timestamp=end_time,
            scan_duration=duration
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Security scan failed: {str(e)}")

# Analyze single file endpoint
@app.post("/analyze", response_model=ScanResponse)
async def analyze_file(
    request: AnalyzeRequest,
    token: str = Depends(verify_token)
):
    """Analyze a single file"""
    try:
        start_time = datetime.now()
        
        # Validate file
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Perform analysis
        results = await asyncio.to_thread(
            analyzer.analyze_file,
            request.file_path,
            request.language,
            include_suggestions=request.include_suggestions
        )
        
        # Convert results to response format
        scan_results = []
        for result in results:
            scan_results.append(ScanResult(
                file_path=result.get('file_path', request.file_path),
                line_number=result.get('line_number', 0),
                severity=result.get('severity', 'unknown'),
                issue_type=result.get('issue_type', 'unknown'),
                description=result.get('description', ''),
                suggestion=result.get('suggestion', ''),
                compliance_standards=result.get('compliance_standards', [])
            ))
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return ScanResponse(
            success=True,
            message=f"Analysis completed. Found {len(scan_results)} issues.",
            results=scan_results,
            summary={"total_issues": len(scan_results)},
            timestamp=end_time,
            scan_duration=duration
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Upload and analyze endpoint
@app.post("/upload-analyze", response_model=ScanResponse)
async def upload_and_analyze(
    file: UploadFile = File(...),
    language: str = None,
    include_suggestions: bool = True,
    token: str = Depends(verify_token)
):
    """Upload a file and analyze it"""
    try:
        start_time = datetime.now()
        
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Detect language if not provided
        if not language:
            ext = Path(file.filename).suffix.lower()
            language_map = {
                '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                '.java': 'java', '.c': 'c', '.cpp': 'cpp', '.cs': 'csharp',
                '.go': 'go', '.rs': 'rust', '.php': 'php', '.rb': 'ruby'
            }
            language = language_map.get(ext, 'unknown')
        
        # Perform analysis
        results = await asyncio.to_thread(
            analyzer.analyze_file,
            temp_path,
            language,
            include_suggestions=include_suggestions
        )
        
        # Clean up
        os.remove(temp_path)
        
        # Convert results to response format
        scan_results = []
        for result in results:
            scan_results.append(ScanResult(
                file_path=file.filename,
                line_number=result.get('line_number', 0),
                severity=result.get('severity', 'unknown'),
                issue_type=result.get('issue_type', 'unknown'),
                description=result.get('description', ''),
                suggestion=result.get('suggestion', ''),
                compliance_standards=result.get('compliance_standards', [])
            ))
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return ScanResponse(
            success=True,
            message=f"Upload analysis completed. Found {len(scan_results)} issues.",
            results=scan_results,
            summary={"total_issues": len(scan_results)},
            timestamp=end_time,
            scan_duration=duration
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload analysis failed: {str(e)}")

# Get supported languages endpoint
@app.get("/languages")
async def get_supported_languages(token: str = Depends(verify_token)):
    """Get list of supported programming languages"""
    languages = [
        "python", "javascript", "typescript", "java", "c", "cpp", "csharp",
        "go", "rust", "php", "ruby", "swift", "kotlin", "scala", "dart",
        "r", "matlab", "shell", "sql", "html", "css"
    ]
    return {"languages": languages}

# Get compliance standards endpoint
@app.get("/compliance-standards")
async def get_compliance_standards(token: str = Depends(verify_token)):
    """Get list of supported compliance standards"""
    standards = [
        {"id": "owasp", "name": "OWASP Top 10", "description": "Web application security risks"},
        {"id": "cwe", "name": "Common Weakness Enumeration", "description": "Software security weaknesses"},
        {"id": "pci", "name": "PCI DSS", "description": "Payment Card Industry Data Security Standard"},
        {"id": "nist", "name": "NIST Cybersecurity Framework", "description": "Cybersecurity best practices"},
        {"id": "soc2", "name": "SOC 2", "description": "Service Organization Control 2"},
        {"id": "iso27001", "name": "ISO 27001", "description": "Information security management"},
        {"id": "hipaa", "name": "HIPAA", "description": "Health Insurance Portability and Accountability Act"},
        {"id": "gdpr", "name": "GDPR", "description": "General Data Protection Regulation"},
        {"id": "sox", "name": "SOX", "description": "Sarbanes-Oxley Act financial controls"},
        {"id": "fedramp", "name": "FedRAMP", "description": "Federal Risk and Authorization Management Program"},
        {"id": "cis", "name": "CIS Controls", "description": "Center for Internet Security Controls"},
        {"id": "mitre", "name": "MITRE ATT&CK", "description": "Adversarial Tactics, Techniques, and Common Knowledge"}
    ]
    return {"standards": standards}

# Get scan statistics endpoint
@app.get("/stats")
async def get_scan_statistics(token: str = Depends(verify_token)):
    """Get scanning statistics"""
    # This would typically query a database
    # For now, return mock data
    stats = {
        "total_scans": 0,
        "total_issues_found": 0,
        "average_scan_duration": 0.0,
        "most_common_issues": [],
        "scan_history": []
    }
    return stats

# PR Creation endpoints
class PRCreationRequest(BaseModel):
    """Request model for PR creation"""
    scan_result_files: List[str] = Field(..., description="Paths to scan result files")
    repository_path: str = Field(".", description="Repository path")
    base_branch: str = Field("main", description="Base branch for PR")
    pr_type: str = Field("code_quality", description="Type of PR to create")
    priority_strategy: str = Field("balanced", description="Priority strategy")
    template_standard: str = Field("github_standard", description="Template standard")
    deduplicate: bool = Field(True, description="Deduplicate issues")
    auto_commit: bool = Field(True, description="Auto commit changes")
    auto_push: bool = Field(False, description="Auto push branch")
    create_pr: bool = Field(False, description="Create GitHub PR")
    dry_run: bool = Field(False, description="Dry run mode")
    labels: Optional[List[str]] = Field(None, description="PR labels")
    assignees: Optional[List[str]] = Field(None, description="PR assignees")
    reviewers: Optional[List[str]] = Field(None, description="PR reviewers")

class PRCreationResponse(BaseModel):
    """Response model for PR creation"""
    success: bool
    branch_name: str
    commit_hash: str
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    title: str
    description: str
    files_changed: Optional[List[str]] = None
    error_message: Optional[str] = None

@app.post("/create-pr", response_model=PRCreationResponse)
async def create_pr(
    request: PRCreationRequest,
    token: str = Depends(verify_token)
):
    """Create AI-powered PR from scan results"""
    try:
        # Import PR modules
        from src.pr import PRCreator, PRCreationConfig
        
        # Validate scan result files
        for scan_file in request.scan_result_files:
            if not os.path.exists(scan_file):
                raise HTTPException(status_code=404, detail=f"Scan result file not found: {scan_file}")
        
        # Create PR configuration
        config = PRCreationConfig(
            repository_path=request.repository_path,
            base_branch=request.base_branch,
            pr_type=request.pr_type,
            priority_strategy=request.priority_strategy,
            template_standard=request.template_standard,
            deduplicate=request.deduplicate,
            auto_commit=request.auto_commit,
            auto_push=request.auto_push,
            create_pr=request.create_pr,
            dry_run=request.dry_run,
            custom_labels=request.labels,
            custom_assignees=request.assignees,
            custom_reviewers=request.reviewers
        )
        
        # Create PR creator
        pr_creator = PRCreator(config)
        
        # Create PR
        result = pr_creator.create_pr_from_scan_results(request.scan_result_files)
        
        return PRCreationResponse(
            success=result.success,
            branch_name=result.branch_name,
            commit_hash=result.commit_hash,
            pr_url=result.pr_url,
            pr_number=result.pr_number,
            title=result.title,
            description=result.description,
            files_changed=result.files_changed,
            error_message=result.error_message
        )
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Missing dependencies: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating PR: {str(e)}")

@app.post("/create-pr-from-issues", response_model=PRCreationResponse)
async def create_pr_from_issues(
    request: PRCreationRequest,
    issues: List[ScanResult],
    token: str = Depends(verify_token)
):
    """Create PR directly from issues"""
    try:
        # Import PR modules
        from src.pr import PRCreator, PRCreationConfig
        from src.core.intelligent_analyzer import CodeIssue
        
        # Convert issues to CodeIssue objects
        code_issues = []
        for issue in issues:
            code_issue = CodeIssue(
                file_path=issue.file_path,
                line_number=issue.line_number,
                issue_type=issue.issue_type,
                severity=issue.severity,
                description=issue.description,
                suggestion=issue.suggestion,
                code_snippet=issue.compliance_standards or ""
            )
            code_issues.append(code_issue)
        
        # Create PR configuration
        config = PRCreationConfig(
            repository_path=request.repository_path,
            base_branch=request.base_branch,
            pr_type=request.pr_type,
            priority_strategy=request.priority_strategy,
            template_standard=request.template_standard,
            deduplicate=request.deduplicate,
            auto_commit=request.auto_commit,
            auto_push=request.auto_push,
            create_pr=request.create_pr,
            dry_run=request.dry_run,
            custom_labels=request.labels,
            custom_assignees=request.assignees,
            custom_reviewers=request.reviewers
        )
        
        # Create PR creator
        pr_creator = PRCreator(config)
        
        # Create PR
        result = pr_creator.create_pr_from_issues(code_issues)
        
        return PRCreationResponse(
            success=result.success,
            branch_name=result.branch_name,
            commit_hash=result.commit_hash,
            pr_url=result.pr_url,
            pr_number=result.pr_number,
            title=result.title,
            description=result.description,
            files_changed=result.files_changed,
            error_message=result.error_message
        )
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Missing dependencies: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating PR: {str(e)}")

@app.get("/pr-templates")
async def get_pr_templates(token: str = Depends(verify_token)):
    """Get available PR templates"""
    templates = [
        {"id": "security_fix", "name": "Security Fix", "description": "Fix security vulnerabilities"},
        {"id": "code_quality", "name": "Code Quality", "description": "Improve code quality"},
        {"id": "performance", "name": "Performance", "description": "Performance optimizations"},
        {"id": "compliance", "name": "Compliance", "description": "Compliance updates"},
        {"id": "refactoring", "name": "Refactoring", "description": "Code refactoring"},
        {"id": "bug_fix", "name": "Bug Fix", "description": "Fix bugs and issues"}
    ]
    return {"templates": templates}

@app.get("/priority-strategies")
async def get_priority_strategies(token: str = Depends(verify_token)):
    """Get available priority strategies for PR creation"""
    return {
        "strategies": [
            {
                "id": "severity_first",
                "name": "Severity First",
                "description": "Prioritize issues by severity level (Critical > High > Medium > Low)"
            },
            {
                "id": "easy_win_first",
                "name": "Easy Win First",
                "description": "Prioritize issues that are easier to fix"
            },
            {
                "id": "balanced",
                "name": "Balanced",
                "description": "Balance between severity and ease of fix"
            },
            {
                "id": "impact_first",
                "name": "Impact First",
                "description": "Prioritize issues with highest impact on codebase"
            }
        ]
    }

# LLM Studio API endpoints

class ProviderRequest(BaseModel):
    """Request model for provider management"""
    provider_type: str = Field(..., description="Provider type (openai, google_gemini, claude, ollama)")
    api_key: str = Field(..., description="API key for the provider")
    base_url: Optional[str] = Field(None, description="Base URL for the provider")
    organization: Optional[str] = Field(None, description="Organization ID (for OpenAI)")

class ProviderResponse(BaseModel):
    """Response model for provider operations"""
    success: bool
    message: str
    provider_type: Optional[str] = None
    status: Optional[str] = None

class ChatRequest(BaseModel):
    """Request model for chat completion"""
    messages: List[Dict[str, str]] = Field(..., description="List of chat messages")
    model: Optional[str] = Field(None, description="Model to use for chat")
    temperature: Optional[float] = Field(0.7, description="Temperature for generation")
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens to generate")

class ChatResponse(BaseModel):
    """Response model for chat completion"""
    success: bool
    message: str
    response: Optional[str] = None
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None

class ModelListResponse(BaseModel):
    """Response model for model listing"""
    success: bool
    models: List[Dict[str, Any]]
    total_count: int

@app.post("/llm/providers/add", response_model=ProviderResponse)
async def add_provider(
    request: ProviderRequest,
    token: str = Depends(verify_token)
):
    """Add a new LLM provider"""
    try:
        manager = LLMManager()
        
        provider_config = ProviderConfig(
            provider_type=ProviderType(request.provider_type),
            api_key=request.api_key,
            base_url=request.base_url,
            organization=request.organization
        )
        
        manager.add_provider(provider_config)
        
        return ProviderResponse(
            success=True,
            message=f"Successfully added {request.provider_type} provider",
            provider_type=request.provider_type,
            status="enabled"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error adding provider: {str(e)}")

@app.get("/llm/providers", response_model=List[Dict[str, Any]])
async def list_providers(token: str = Depends(verify_token)):
    """List configured providers"""
    try:
        manager = LLMManager()
        
        providers = []
        for provider_type, config in manager.config.providers.items():
            providers.append({
                "provider_type": provider_type.value,
                "is_enabled": config.is_enabled,
                "has_api_key": bool(config.api_key),
                "base_url": config.base_url,
                "organization": config.organization
            })
        
        return providers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing providers: {str(e)}")

@app.post("/llm/providers/test", response_model=ProviderResponse)
async def test_provider(
    request: ProviderRequest,
    token: str = Depends(verify_token)
):
    """Test provider connection"""
    try:
        manager = LLMManager()
        
        is_healthy = await manager.test_provider(
            ProviderType(request.provider_type),
            request.api_key
        )
        
        if is_healthy:
            return ProviderResponse(
                success=True,
                message=f"Provider {request.provider_type} is healthy",
                provider_type=request.provider_type,
                status="healthy"
            )
        else:
            return ProviderResponse(
                success=False,
                message=f"Provider {request.provider_type} is not responding",
                provider_type=request.provider_type,
                status="unhealthy"
            )
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error testing provider: {str(e)}")

@app.get("/llm/models", response_model=ModelListResponse)
async def list_models(token: str = Depends(verify_token)):
    """List available models"""
    try:
        manager = LLMManager()
        
        models = await manager.list_available_models()
        
        model_list = []
        for model in models:
            model_list.append({
                "name": model.name,
                "provider": model.provider.value,
                "model_type": model.model_type.value,
                "capabilities": model.capabilities or [],
                "cost_per_1k_tokens": model.cost_per_1k_tokens,
                "max_tokens": model.max_tokens,
                "is_available": model.is_available
            })
        
        return ModelListResponse(
            success=True,
            models=model_list,
            total_count=len(model_list)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing models: {str(e)}")

@app.post("/llm/chat", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    token: str = Depends(verify_token)
):
    """Send a chat message and get AI response"""
    try:
        manager = LLMManager()
        
        # Convert messages to ChatMessage objects
        messages = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in request.messages
        ]
        
        response = await manager.chat_completion(
            messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        ai_response = response.choices[0]["message"]["content"]
        
        return ChatResponse(
            success=True,
            message="Chat completion successful",
            response=ai_response,
            model=request.model or manager.config.default_model,
            usage=response.usage
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error in chat completion: {str(e)}")

@app.get("/llm/config")
async def get_llm_config(token: str = Depends(verify_token)):
    """Get LLM Studio configuration"""
    try:
        manager = LLMManager()
        
        return {
            "default_model": manager.config.default_model,
            "fallback_model": manager.config.fallback_model,
            "max_retries": manager.config.max_retries,
            "timeout": manager.config.timeout,
            "provider_count": len(manager.config.providers),
            "model_count": len(manager.config.models)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting config: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 