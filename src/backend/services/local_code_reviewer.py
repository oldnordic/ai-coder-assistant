"""
local_code_reviewer.py

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
Local Code Reviewer Service

This service provides AI-powered code analysis using fine-tuned local models.
It implements the second stage of the two-stage analysis approach:
1. Quick Scan (handled by IntelligentAnalyzer)
2. AI Enhancement (handled by this service)
"""

import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import json
import threading
from concurrent.futures import ThreadPoolExecutor, Future

from src.backend.services.ollama_client import OllamaClient, get_available_models_sync, get_ollama_response
from src.backend.utils.secrets import get_secrets_manager
from src.core.config import Config

logger = logging.getLogger(__name__)


class EnhancementType(Enum):
    """Types of AI enhancements available."""
    CODE_IMPROVEMENT = "code_improvement"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    BEST_PRACTICES = "best_practices"
    DOCUMENTATION = "documentation"
    ARCHITECTURAL_REVIEW = "architectural_review"


@dataclass
class EnhancementRequest:
    """Request for AI enhancement of a code issue."""
    issue_description: str
    file_path: str
    line_number: int
    code_snippet: str
    language: str
    enhancement_type: EnhancementType
    context_lines: int = 5
    include_suggestions: bool = True
    include_explanation: bool = True


@dataclass
class EnhancementResult:
    """Result of AI enhancement analysis."""
    original_issue: str
    enhanced_analysis: str
    suggestions: List[str]
    explanation: str
    confidence_score: float
    model_used: str
    processing_time: float
    code_changes: Optional[List[Dict[str, Any]]] = None
    security_implications: Optional[str] = None
    performance_impact: Optional[str] = None


class LocalCodeReviewer:
    """
    Local code reviewer using fine-tuned models for AI-powered analysis.
    
    This service provides in-depth analysis of specific code issues identified
    by the quick scan, offering detailed suggestions and explanations.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the local code reviewer.
        
        Args:
            config_path: Path to configuration file for model settings
        """
        self.config = Config()
        self.secrets_manager = get_secrets_manager()
        self.ollama_client = OllamaClient()
        
        # Thread pool for concurrent processing
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.active_futures: Dict[str, Future[Any]] = {}
        
        # Model configuration - prioritize fine-tuned models
        self.fine_tuned_model = "code-reviewer-v1"  # Our specialized model
        self.default_model = "codellama:7b"
        self.fallback_model = "llama2:7b"
        self.current_model: Optional[str] = None
        
        # Load configuration
        self._load_config(config_path)
        
        # Initialize model
        self._initialize_model()
        
        logger.info("LocalCodeReviewer initialized successfully")
    
    def _load_config(self, config_path: Optional[str] = None):
        """Load configuration from file or use defaults."""
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                
                self.fine_tuned_model = config_data.get('fine_tuned_model', self.fine_tuned_model)
                self.default_model = config_data.get('default_model', self.default_model)
                self.fallback_model = config_data.get('fallback_model', self.fallback_model)
                
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        # Override with environment variables if available
        env_model = self.secrets_manager.get_secret('LOCAL_CODE_REVIEWER_MODEL')
        if env_model:
            self.fine_tuned_model = env_model
    
    def _initialize_model(self):
        """Initialize the local model for code review."""
        try:
            # Check if Ollama is available by trying to get models
            available_models = get_available_models_sync()
            
            if available_models:
                # Prioritize fine-tuned model if available
                if self.fine_tuned_model in available_models:
                    self.current_model = self.fine_tuned_model
                    logger.info(f"Using fine-tuned model: {self.current_model}")
                elif self.default_model in available_models:
                    self.current_model = self.default_model
                    logger.info(f"Using default model: {self.current_model}")
                elif self.fallback_model in available_models:
                    self.current_model = self.fallback_model
                    logger.info(f"Using fallback model: {self.current_model}")
                else:
                    # Use the first available model
                    self.current_model = available_models[0]
                    logger.info(f"Using first available model: {self.current_model}")
            else:
                logger.warning("No Ollama models found. AI enhancement will be disabled.")
                self.current_model = None
                
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            self.current_model = None
    
    def analyze_snippet(
        self, 
        request: EnhancementRequest
    ) -> EnhancementResult:
        """
        Analyze a code snippet using AI enhancement.
        
        Args:
            request: Enhancement request containing issue details
            
        Returns:
            EnhancementResult with detailed analysis
        """
        if not self.current_model:
            return self._create_fallback_result(request, "No AI model available")
        
        try:
            # Prepare the prompt for the model
            prompt = self._create_enhancement_prompt(request)
            
            # Get context around the issue
            context_code = self._get_code_context(request)
            
            # Combine prompt with context
            full_prompt = f"{prompt}\n\nCode Context:\n```{request.language}\n{context_code}\n```"
            
            # Send to model using synchronous method
            response = get_ollama_response(full_prompt, self.current_model)
            
            # Parse the response
            result = self._parse_enhancement_response(response, request)
            
            return result
            
        except Exception as e:
            logger.error(f"Error during AI enhancement: {e}")
            return self._create_fallback_result(request, str(e))
    
    def analyze_snippet_async(
        self, 
        request: EnhancementRequest,
        callback: Optional[Callable[[EnhancementResult], None]] = None
    ) -> str:
        """
        Analyze a code snippet asynchronously.
        
        Args:
            request: Enhancement request
            callback: Optional callback function to call with result
            
        Returns:
            Task ID for tracking the async operation
        """
        import uuid
        task_id = str(uuid.uuid4())
        
        def _async_analysis():
            try:
                result = self.analyze_snippet(request)
                if callback:
                    callback(result)
            except Exception as e:
                logger.error(f"Async analysis failed: {e}")
                if callback:
                    callback(self._create_fallback_result(request, str(e)))
        
        future = self.executor.submit(_async_analysis)
        self.active_futures[task_id] = future
        
        return task_id
    
    def get_enhancement_status(self, task_id: str) -> Optional[str]:
        """Get the status of an async enhancement task."""
        if task_id not in self.active_futures:
            return "not_found"
        
        future = self.active_futures[task_id]
        if future.done():
            if future.exception():
                return "failed"
            else:
                return "completed"
        else:
            return "running"
    
    def cancel_enhancement(self, task_id: str) -> bool:
        """Cancel an async enhancement task."""
        if task_id in self.active_futures:
            future = self.active_futures[task_id]
            cancelled = future.cancel()
            if cancelled:
                del self.active_futures[task_id]
            return cancelled
        return False
    
    def _create_enhancement_prompt(self, request: EnhancementRequest) -> str:
        """Create a specialized prompt for the AI model based on the enhancement type."""
        
        # Enhanced prompt engineering for better code analysis
        system_prompt = """You are an expert code reviewer with deep knowledge of software engineering best practices, security vulnerabilities, and performance optimization. Your task is to analyze code and provide actionable, specific recommendations.

When analyzing code, consider:
1. Code quality and maintainability
2. Security vulnerabilities and best practices
3. Performance implications and optimization opportunities
4. Architectural patterns and design principles
5. Language-specific conventions and idioms
6. Error handling and edge cases
7. Documentation and readability

Provide your analysis in a structured, professional manner with clear explanations and specific code examples."""
        
        base_prompt = f"""{system_prompt}

**Code Review Request:**
- File: {request.file_path}
- Line: {request.line_number}
- Language: {request.language}
- Issue Type: {request.enhancement_type.value.replace('_', ' ').title()}

**Original Issue:**
{request.issue_description}

**Code to Review:**
```{request.language}
{request.code_snippet}
```

**Analysis Task:**
"""
        
        if request.enhancement_type == EnhancementType.CODE_IMPROVEMENT:
            base_prompt += """
Analyze this code for potential improvements in:
1. **Logic and Correctness**: Are there bugs, edge cases, or logical errors?
2. **Code Quality**: Can the code be made more readable, maintainable, or efficient?
3. **Best Practices**: Are there language-specific or general programming best practices being violated?
4. **Refactoring Opportunities**: Can the code be restructured for better organization?

Provide specific, actionable suggestions with code examples where appropriate.
"""
        elif request.enhancement_type == EnhancementType.SECURITY_ANALYSIS:
            base_prompt += """
Analyze this code for security vulnerabilities:
1. **Input Validation**: Are inputs properly validated and sanitized?
2. **Authentication & Authorization**: Are proper access controls in place?
3. **Data Protection**: Is sensitive data handled securely?
4. **Common Vulnerabilities**: Are there SQL injection, XSS, CSRF, or other common vulnerabilities?
5. **Cryptographic Issues**: Are cryptographic functions used correctly?
6. **Error Handling**: Do error messages leak sensitive information?

Provide specific security recommendations with secure code examples.
"""
        elif request.enhancement_type == EnhancementType.PERFORMANCE_OPTIMIZATION:
            base_prompt += """
Analyze this code for performance issues:
1. **Algorithm Efficiency**: Are there more efficient algorithms or data structures?
2. **Resource Usage**: Is memory, CPU, or I/O being used efficiently?
3. **Caching Opportunities**: Could caching improve performance?
4. **Concurrency**: Could parallel processing or async operations help?
5. **Database Queries**: Are database operations optimized?
6. **Network Calls**: Are external API calls optimized?

Provide specific performance recommendations with optimized code examples.
"""
        elif request.enhancement_type == EnhancementType.BEST_PRACTICES:
            base_prompt += """
Analyze this code for best practices violations:
1. **Code Style**: Does the code follow language-specific style guidelines?
2. **Naming Conventions**: Are variables, functions, and classes named appropriately?
3. **SOLID Principles**: Are object-oriented design principles followed?
4. **DRY Principle**: Is there code duplication that could be eliminated?
5. **Error Handling**: Are exceptions and errors handled properly?
6. **Documentation**: Is the code self-documenting and well-commented?

Provide specific recommendations for improving code quality and maintainability.
"""
        elif request.enhancement_type == EnhancementType.DOCUMENTATION:
            base_prompt += """
Analyze this code for documentation needs:
1. **Function Documentation**: Do functions have clear docstrings explaining their purpose?
2. **Inline Comments**: Are complex sections of code explained with comments?
3. **API Documentation**: Are public interfaces properly documented?
4. **Code Examples**: Would usage examples help clarify the code's purpose?
5. **README/Setup**: Is there documentation for setup and usage?

Provide specific documentation recommendations with examples.
"""
        elif request.enhancement_type == EnhancementType.ARCHITECTURAL_REVIEW:
            base_prompt += """
Analyze this code for architectural considerations:
1. **Separation of Concerns**: Are different responsibilities properly separated?
2. **Design Patterns**: Could established design patterns improve the architecture?
3. **Dependency Management**: Are dependencies properly managed and minimized?
4. **Scalability**: Will the current architecture scale with growth?
5. **Testability**: Is the code designed for easy testing?
6. **Integration**: How does this code fit into the larger system architecture?

Provide specific architectural recommendations with design suggestions.
"""
        
        base_prompt += """
Please format your response as JSON with the following structure:
{
    "analysis": "Detailed analysis of the issue",
    "suggestions": ["Specific suggestion 1", "Specific suggestion 2", ...],
    "explanation": "Clear explanation of why these changes are beneficial",
    "confidence": 0.95,
    "code_changes": [
        {
            "type": "replacement|addition|deletion",
            "line": 10,
            "old_code": "original code",
            "new_code": "improved code",
            "explanation": "Why this change is needed"
        }
    ],
    "security_implications": "Security considerations (if applicable)",
    "performance_impact": "Performance considerations (if applicable)"
}

If no issues are found, respond with:
{
    "analysis": "No significant issues found in this code",
    "suggestions": [],
    "explanation": "The code appears to follow good practices",
    "confidence": 0.9,
    "code_changes": []
}
"""
        
        return base_prompt
    
    def _get_code_context(self, request: EnhancementRequest) -> str:
        """Get code context around the issue line."""
        try:
            with open(request.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start_line = max(0, request.line_number - request.context_lines - 1)
            end_line = min(len(lines), request.line_number + request.context_lines)
            
            context_lines = lines[start_line:end_line]
            return ''.join(context_lines)
            
        except Exception as e:
            logger.warning(f"Could not read file context: {e}")
            return request.code_snippet
    
    def _parse_enhancement_response(self, response: str, request: EnhancementRequest) -> EnhancementResult:
        """Parse the AI model response into a structured result."""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)
                
                return EnhancementResult(
                    original_issue=request.issue_description,
                    enhanced_analysis=parsed.get('analysis', ''),
                    suggestions=parsed.get('suggestions', []),
                    explanation=parsed.get('explanation', ''),
                    confidence_score=parsed.get('confidence', 0.5),
                    model_used=self.current_model or "unknown",
                    processing_time=0.0,  # TODO: Track actual processing time
                    code_changes=parsed.get('code_changes', []),
                    security_implications=parsed.get('security_implications'),
                    performance_impact=parsed.get('performance_impact')
                )
            else:
                # Fallback: treat the entire response as analysis
                return EnhancementResult(
                    original_issue=request.issue_description,
                    enhanced_analysis=response,
                    suggestions=[],
                    explanation="Raw AI response",
                    confidence_score=0.5,
                    model_used=self.current_model or "unknown",
                    processing_time=0.0
                )
                
        except Exception as e:
            logger.error(f"Failed to parse enhancement response: {e}")
            return self._create_fallback_result(request, f"Failed to parse response: {e}")
    
    def _create_fallback_result(self, request: EnhancementRequest, error_message: str) -> EnhancementResult:
        """Create a fallback result when AI enhancement fails."""
        return EnhancementResult(
            original_issue=request.issue_description,
            enhanced_analysis=f"AI enhancement unavailable: {error_message}",
            suggestions=["Review the code manually", "Check for common patterns in similar issues"],
            explanation="AI enhancement could not be performed due to technical issues.",
            confidence_score=0.0,
            model_used="none",
            processing_time=0.0
        )
    
    def get_available_models(self) -> List[str]:
        """Get list of available models for code review."""
        try:
            return get_available_models_sync()
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to a different model for code review."""
        try:
            available_models = self.get_available_models()
            if model_name in available_models:
                self.current_model = model_name
                logger.info(f"Switched to model: {model_name}")
                return True
            else:
                logger.warning(f"Model {model_name} not available")
                return False
        except Exception as e:
            logger.error(f"Failed to switch model: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "current_model": self.current_model,
            "fine_tuned_model": self.fine_tuned_model,
            "default_model": self.default_model,
            "fallback_model": self.fallback_model,
            "is_fine_tuned": self.current_model == self.fine_tuned_model if self.current_model else False
        }
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Cancel all active futures
            for task_id, future in list(self.active_futures.items()):
                future.cancel()
                del self.active_futures[task_id]
            
            # Shutdown executor
            self.executor.shutdown(wait=False)
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global instance for easy access
_local_code_reviewer: Optional[LocalCodeReviewer] = None
_lock = threading.Lock()


def get_local_code_reviewer() -> LocalCodeReviewer:
    """Get the global LocalCodeReviewer instance."""
    global _local_code_reviewer
    
    if _local_code_reviewer is None:
        with _lock:
            if _local_code_reviewer is None:
                _local_code_reviewer = LocalCodeReviewer()
    
    return _local_code_reviewer


def cleanup_local_code_reviewer():
    """Clean up the global LocalCodeReviewer instance."""
    global _local_code_reviewer
    
    if _local_code_reviewer is not None:
        with _lock:
            _local_code_reviewer.cleanup()
            _local_code_reviewer = None 