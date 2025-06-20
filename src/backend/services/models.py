"""
models.py

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
Data models for LLM Studio.
Defines structures for models, providers, and configurations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class ProviderType(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    GOOGLE = "google"
    GOOGLE_GEMINI = "google_gemini"
    CLAUDE = "claude"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class ModelType(Enum):
    """Model types/categories."""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    VISION = "vision"
    CODE = "code"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    provider: ProviderType
    model_type: ModelType
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = field(default_factory=list)
    system_prompt: Optional[str] = None
    is_default: bool = False
    is_enabled: bool = True
    cost_per_1k_tokens: Optional[float] = None
    context_length: Optional[int] = None
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderConfig:
    """Configuration for an AI provider."""
    provider_type: ProviderType
    api_key: str
    base_url: Optional[str] = None
    organization: Optional[str] = None
    project_id: Optional[str] = None
    region: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    is_enabled: bool = True
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Ollama-specific fields
    verify_ssl: bool = True
    custom_endpoints: Optional[Dict[str, str]] = None
    auth_token: Optional[str] = None
    instance_name: Optional[str] = None  # For multiple Ollama instances


@dataclass
class LLMModel:
    """Complete LLM model information."""
    config: ModelConfig
    provider_config: ProviderConfig
    last_used: Optional[datetime] = None
    usage_stats: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ChatMessage:
    """Chat message structure."""
    role: str  # "system", "user", "assistant", "function"
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ChatCompletionRequest:
    """Request for chat completion."""
    messages: List[ChatMessage]
    model: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[List[str]] = None
    stream: bool = False
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[str] = None


@dataclass
class ChatCompletionResponse:
    """Response from chat completion."""
    id: str
    model: str
    created: datetime
    choices: List[Dict[str, Any]]
    provider: ProviderType
    response_time: float
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    cost: Optional[float] = None


@dataclass
class ModelUsage:
    """Model usage statistics."""
    model_name: str
    provider: ProviderType
    tokens_used: int
    requests_made: int
    total_cost: float
    average_response_time: float
    last_used: datetime
    success_rate: float


@dataclass
class LLMStudioConfig:
    """Global LLM Studio configuration."""
    providers: Dict[ProviderType, ProviderConfig] = field(default_factory=dict)
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    default_provider: ProviderType = ProviderType.OPENAI
    default_model: str = "gpt-3.5-turbo"
    enable_fallback: bool = True
    enable_retry: bool = True
    max_concurrent_requests: int = 5
    request_timeout: int = 30
    enable_logging: bool = True
    enable_metrics: bool = True
    cost_tracking: bool = True
    auto_switch_on_error: bool = True
    ollama_instances: List[ProviderConfig] = field(default_factory=list) 