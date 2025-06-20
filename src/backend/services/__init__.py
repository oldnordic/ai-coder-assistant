"""
LLM Studio module for AI Coder Assistant.
Provides unified interface for multiple AI providers (OpenAI, Google Gemini, Claude).
"""

from .llm_manager import LLMManager
from .providers import OpenAIProvider, GoogleGeminiProvider, ClaudeProvider
from .models import LLMModel, ModelConfig, ProviderConfig
from .studio_ui import LLMStudioUI
from .ollama_client import get_available_models_sync
from .ai_tools import enhance_issues_with_ai

__all__ = [
    'LLMManager',
    'OpenAIProvider',
    'GoogleGeminiProvider', 
    'ClaudeProvider',
    'LLMModel',
    'ModelConfig',
    'ProviderConfig',
    'LLMStudioUI',
    'get_available_models_sync',
    'enhance_issues_with_ai'
] 