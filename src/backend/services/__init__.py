"""
LLM Studio module for AI Coder Assistant.
Provides unified interface for multiple AI providers (OpenAI, Google Gemini, Claude).
"""

from .ai_tools import enhance_issues_with_ai
from .intelligent_analyzer import IntelligentCodeAnalyzer
from .llm_manager import LLMManager
from .models import LLMModel, ModelConfig, ProviderConfig
from .ollama_client import get_available_models_sync
from .providers import ClaudeProvider, GoogleGeminiProvider, OpenAIProvider
from .scanner import ScannerService, ScanStatus, TaskStatus
from .studio_ui import LLMStudioUI

__all__ = [
    "LLMManager",
    "OpenAIProvider",
    "GoogleGeminiProvider",
    "ClaudeProvider",
    "LLMModel",
    "ModelConfig",
    "ProviderConfig",
    "LLMStudioUI",
    "get_available_models_sync",
    "enhance_issues_with_ai",
    "ScannerService",
    "TaskStatus",
    "ScanStatus",
    "IntelligentCodeAnalyzer",
]
