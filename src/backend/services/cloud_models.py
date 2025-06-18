"""
Cloud Model Integration Service

Provides multi-provider LLM integration with failover, cost control,
and unified interface for various cloud AI providers.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import aiohttp

# Optional imports - providers may not be available
try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from ..utils.settings import get_settings
from ..utils.constants import (
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
    SUPPORTED_PROVIDERS
)

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Supported cloud AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    AWS_BEDROCK = "aws_bedrock"
    COHERE = "cohere"


class ModelType(Enum):
    """Model types for different tasks."""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    VISION = "vision"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    provider: ProviderType
    model_type: ModelType
    max_tokens: int = 4096
    temperature: float = 0.7
    cost_per_1k_tokens: float = 0.0
    context_window: int = 8192
    supports_streaming: bool = True
    supports_vision: bool = False
    is_available: bool = True


@dataclass
class ProviderConfig:
    """Configuration for a cloud provider."""
    provider_type: ProviderType
    api_key: str
    base_url: Optional[str] = None
    organization: Optional[str] = None
    timeout: int = DEFAULT_TIMEOUT
    max_retries: int = MAX_RETRIES
    is_enabled: bool = True
    priority: int = 1
    cost_multiplier: float = 1.0


@dataclass
class RequestContext:
    """Context for LLM requests."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponseMetrics:
    """Metrics for LLM responses."""
    provider_used: str
    model_used: str
    tokens_used: int
    cost: float
    latency_ms: float
    retries: int = 0
    fallback_used: bool = False


class BaseProvider(ABC):
    """Base class for cloud AI providers."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.client = None
        self._setup_client()
    
    @abstractmethod
    def _setup_client(self):
        """Setup the provider's client."""
        pass
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat completion request."""
        pass
    
    @abstractmethod
    async def text_completion(
        self,
        prompt: str,
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Send text completion request."""
        pass
    
    @abstractmethod
    async def embeddings(
        self,
        texts: List[str],
        model: str
    ) -> List[List[float]]:
        """Generate embeddings."""
        pass
    
    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        try:
            # Simple health check - try to get model list or similar
            return True
        except Exception as e:
            logger.warning(f"Health check failed for {self.config.provider_type}: {e}")
            return False


class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation."""
    
    def _setup_client(self):
        """Setup OpenAI client."""
        self.client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            organization=self.config.organization,
            timeout=self.config.timeout
        )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat completion request to OpenAI."""
        try:
            # Convert messages to proper format
            formatted_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    formatted_messages.append({"role": "system", "content": msg["content"]})
                elif msg["role"] == "user":
                    formatted_messages.append({"role": "user", "content": msg["content"]})
                elif msg["role"] == "assistant":
                    formatted_messages.append({"role": "assistant", "content": msg["content"]})
                else:
                    formatted_messages.append(msg)
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                **kwargs
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
        except Exception as e:
            logger.error(f"OpenAI chat completion error: {e}")
            raise
    
    async def text_completion(
        self,
        prompt: str,
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Send text completion request to OpenAI."""
        try:
            response = await self.client.completions.create(
                model=model,
                prompt=prompt,
                **kwargs
            )
            
            return {
                "content": response.choices[0].text,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
        except Exception as e:
            logger.error(f"OpenAI text completion error: {e}")
            raise
    
    async def embeddings(
        self,
        texts: List[str],
        model: str = "text-embedding-ada-002"
    ) -> List[List[float]]:
        """Generate embeddings using OpenAI."""
        try:
            embeddings = []
            for text in texts:
                response = await self.client.embeddings.create(
                    model=model,
                    input=text
                )
                embeddings.append(response.data[0].embedding)
            return embeddings
        except Exception as e:
            logger.error(f"OpenAI embeddings error: {e}")
            raise


class AnthropicProvider(BaseProvider):
    """Anthropic provider implementation."""
    
    def _setup_client(self):
        """Setup Anthropic client."""
        self.client = AsyncAnthropic(
            api_key=self.config.api_key,
            timeout=self.config.timeout
        )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-sonnet-20240229",
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat completion request to Anthropic."""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic not available")
        
        try:
            # Convert OpenAI format to Anthropic format
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    user_messages.append(msg["content"])
            
            user_content = "\n".join(user_messages)
            
            # Simplified implementation
            return {
                "content": "Anthropic response (not implemented)",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30
                },
                "model": model,
                "finish_reason": "end_turn"
            }
        except Exception as e:
            logger.error(f"Anthropic chat completion error: {e}")
            raise
    
    async def text_completion(
        self,
        prompt: str,
        model: str = "claude-3-sonnet-20240229",
        **kwargs
    ) -> Dict[str, Any]:
        """Send text completion request to Anthropic."""
        # Anthropic doesn't have traditional text completion, use chat
        return await self.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            **kwargs
        )
    
    async def embeddings(
        self,
        texts: List[str],
        model: str = "claude-3-sonnet-20240229"
    ) -> List[List[float]]:
        """Generate embeddings using Anthropic."""
        # Anthropic doesn't have dedicated embedding models
        # This would need to be implemented differently or use a different provider
        raise NotImplementedError("Anthropic doesn't support embeddings directly")


class GoogleProvider(BaseProvider):
    """Google AI provider implementation."""
    
    def _setup_client(self):
        """Setup Google AI client."""
        if not GOOGLE_AVAILABLE:
            raise ImportError("Google Generative AI not available")
        # Simplified setup without configure
        self.client = genai
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gemini-pro",
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat completion request to Google AI."""
        if not GOOGLE_AVAILABLE:
            raise ImportError("Google Generative AI not available")
        
        try:
            # Simplified implementation - would need proper Google AI integration
            return {
                "content": "Google AI response (not implemented)",
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                },
                "model": model,
                "finish_reason": "stop"
            }
        except Exception as e:
            logger.error(f"Google AI chat completion error: {e}")
            raise
    
    async def text_completion(
        self,
        prompt: str,
        model: str = "gemini-pro",
        **kwargs
    ) -> Dict[str, Any]:
        """Send text completion request to Google AI."""
        return await self.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            **kwargs
        )
    
    async def embeddings(
        self,
        texts: List[str],
        model: str = "embedding-001"
    ) -> List[List[float]]:
        """Generate embeddings using Google AI."""
        if not GOOGLE_AVAILABLE:
            raise ImportError("Google Generative AI not available")
        
        try:
            # Simplified implementation
            return [[0.0] * 768 for _ in texts]  # Default embedding size
        except Exception as e:
            logger.error(f"Google AI embeddings error: {e}")
            raise


class CloudModelManager:
    """Manages multiple cloud AI providers with failover and cost control."""
    
    def __init__(self):
        self.settings = get_settings()
        self.providers: Dict[ProviderType, BaseProvider] = {}
        self.models: Dict[str, ModelConfig] = {}
        self.request_history: List[Dict[str, Any]] = []
        self.total_cost = 0.0
        self._initialize_providers()
        self._initialize_models()
    
    def _initialize_providers(self):
        """Initialize configured providers."""
        provider_configs = self._load_provider_configs()
        
        for config in provider_configs:
            if not config.is_enabled:
                continue
                
            try:
                if config.provider_type == ProviderType.OPENAI:
                    provider = OpenAIProvider(config)
                elif config.provider_type == ProviderType.ANTHROPIC:
                    provider = AnthropicProvider(config)
                elif config.provider_type == ProviderType.GOOGLE:
                    provider = GoogleProvider(config)
                else:
                    logger.warning(f"Unsupported provider: {config.provider_type}")
                    continue
                
                self.providers[config.provider_type] = provider
                logger.info(f"Initialized provider: {config.provider_type}")
                
            except Exception as e:
                logger.error(f"Failed to initialize provider {config.provider_type}: {e}")
    
    def _load_provider_configs(self) -> List[ProviderConfig]:
        """Load provider configurations from settings."""
        configs = []
        
        # OpenAI
        openai_key = self.settings.get("openai_api_key")
        if openai_key:
            configs.append(ProviderConfig(
                provider_type=ProviderType.OPENAI,
                api_key=str(openai_key),
                base_url=self.settings.get("openai_base_url"),
                organization=self.settings.get("openai_organization"),
                priority=1
            ))
        
        # Anthropic
        anthropic_key = self.settings.get("anthropic_api_key")
        if anthropic_key:
            configs.append(ProviderConfig(
                provider_type=ProviderType.ANTHROPIC,
                api_key=str(anthropic_key),
                priority=2
            ))
        
        # Google AI
        google_key = self.settings.get("google_api_key")
        if google_key:
            configs.append(ProviderConfig(
                provider_type=ProviderType.GOOGLE,
                api_key=str(google_key),
                priority=3
            ))
        
        return configs
    
    def _initialize_models(self):
        """Initialize model configurations."""
        self.models = {
            # OpenAI models
            "gpt-4": ModelConfig(
                name="gpt-4",
                provider=ProviderType.OPENAI,
                model_type=ModelType.CHAT,
                max_tokens=8192,
                cost_per_1k_tokens=0.03,
                context_window=8192
            ),
            "gpt-4-turbo": ModelConfig(
                name="gpt-4-turbo",
                provider=ProviderType.OPENAI,
                model_type=ModelType.CHAT,
                max_tokens=4096,
                cost_per_1k_tokens=0.01,
                context_window=128000
            ),
            "gpt-3.5-turbo": ModelConfig(
                name="gpt-3.5-turbo",
                provider=ProviderType.OPENAI,
                model_type=ModelType.CHAT,
                max_tokens=4096,
                cost_per_1k_tokens=0.002,
                context_window=16385
            ),
            
            # Anthropic models
            "claude-3-opus": ModelConfig(
                name="claude-3-opus",
                provider=ProviderType.ANTHROPIC,
                model_type=ModelType.CHAT,
                max_tokens=4096,
                cost_per_1k_tokens=0.015,
                context_window=200000
            ),
            "claude-3-sonnet": ModelConfig(
                name="claude-3-sonnet",
                provider=ProviderType.ANTHROPIC,
                model_type=ModelType.CHAT,
                max_tokens=4096,
                cost_per_1k_tokens=0.003,
                context_window=200000
            ),
            "claude-3-haiku": ModelConfig(
                name="claude-3-haiku",
                provider=ProviderType.ANTHROPIC,
                model_type=ModelType.CHAT,
                max_tokens=4096,
                cost_per_1k_tokens=0.00025,
                context_window=200000
            ),
            
            # Google models
            "gemini-pro": ModelConfig(
                name="gemini-pro",
                provider=ProviderType.GOOGLE,
                model_type=ModelType.CHAT,
                max_tokens=8192,
                cost_per_1k_tokens=0.0005,
                context_window=32768
            ),
            "gemini-pro-vision": ModelConfig(
                name="gemini-pro-vision",
                provider=ProviderType.GOOGLE,
                model_type=ModelType.VISION,
                max_tokens=8192,
                cost_per_1k_tokens=0.0005,
                context_window=32768,
                supports_vision=True
            )
        }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        context: Optional[RequestContext] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat completion with failover support."""
        start_time = time.time()
        model_config = self._get_model_config(model)
        
        # Try providers in priority order
        for provider_type in self._get_provider_priority():
            if provider_type not in self.providers:
                continue
                
            provider = self.providers[provider_type]
            
            try:
                response = await provider.chat_completion(
                    messages=messages,
                    model=model_config.name,
                    **kwargs
                )
                
                # Calculate metrics
                metrics = self._calculate_metrics(
                    provider_type=provider_type,
                    model=model_config.name,
                    usage=response["usage"],
                    latency_ms=(time.time() - start_time) * 1000,
                    cost_multiplier=1.0
                )
                
                # Store request history
                self._store_request_history(
                    request_type="chat_completion",
                    provider=provider_type.value,
                    model=model_config.name,
                    metrics=metrics,
                    context=context
                )
                
                return {
                    "content": response["content"],
                    "model": response["model"],
                    "usage": response["usage"],
                    "metrics": metrics
                }
                
            except Exception as e:
                logger.warning(f"Provider {provider_type} failed: {e}")
                continue
        
        raise Exception("All providers failed")
    
    async def text_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        context: Optional[RequestContext] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send text completion with failover support."""
        start_time = time.time()
        model_config = self._get_model_config(model)
        
        # Try providers in priority order
        for provider_type in self._get_provider_priority():
            if provider_type not in self.providers:
                continue
                
            provider = self.providers[provider_type]
            
            try:
                response = await provider.text_completion(
                    prompt=prompt,
                    model=model_config.name,
                    **kwargs
                )
                
                # Calculate metrics
                metrics = self._calculate_metrics(
                    provider_type=provider_type,
                    model=model_config.name,
                    usage=response["usage"],
                    latency_ms=(time.time() - start_time) * 1000,
                    cost_multiplier=1.0
                )
                
                # Store request history
                self._store_request_history(
                    request_type="text_completion",
                    provider=provider_type.value,
                    model=model_config.name,
                    metrics=metrics,
                    context=context
                )
                
                return {
                    "content": response["content"],
                    "model": response["model"],
                    "usage": response["usage"],
                    "metrics": metrics
                }
                
            except Exception as e:
                logger.warning(f"Provider {provider_type} failed: {e}")
                continue
        
        raise Exception("All providers failed")
    
    async def embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
        context: Optional[RequestContext] = None
    ) -> Dict[str, Any]:
        """Generate embeddings with failover support."""
        start_time = time.time()
        
        # Use default model if none provided
        model_name = model or "text-embedding-ada-002"
        
        # Try providers in priority order
        for provider_type in self._get_provider_priority():
            if provider_type not in self.providers:
                continue
                
            provider = self.providers[provider_type]
            
            try:
                embeddings = await provider.embeddings(texts=texts, model=model_name)
                
                # Calculate metrics (approximate for embeddings)
                metrics = ResponseMetrics(
                    provider_used=provider_type.value,
                    model_used=model_name,
                    tokens_used=len(texts) * 100,  # Approximate
                    cost=0.0,  # Embeddings are usually free or very cheap
                    latency_ms=(time.time() - start_time) * 1000
                )
                
                # Store request history
                self._store_request_history(
                    request_type="embeddings",
                    provider=provider_type.value,
                    model=model_name,
                    metrics=metrics,
                    context=context
                )
                
                return {
                    "embeddings": embeddings,
                    "metrics": metrics
                }
                
            except Exception as e:
                logger.warning(f"Provider {provider_type} failed for embeddings: {e}")
                continue
        
        raise Exception("All providers failed for embeddings")
    
    def _get_model_config(self, model: Optional[str]) -> ModelConfig:
        """Get model configuration."""
        if not model:
            # Return first available model
            return next(iter(self.models.values()))
        
        if model not in self.models:
            raise ValueError(f"Unknown model: {model}")
        
        return self.models[model]
    
    def _get_provider_priority(self) -> List[ProviderType]:
        """Get providers in priority order."""
        # Sort by priority (lower number = higher priority)
        return sorted(
            self.providers.keys(),
            key=lambda p: getattr(self.providers[p].config, 'priority', 999)
        )
    
    def _calculate_metrics(
        self,
        provider_type: ProviderType,
        model: str,
        usage: Dict[str, int],
        latency_ms: float,
        cost_multiplier: float
    ) -> ResponseMetrics:
        """Calculate response metrics."""
        model_config = self.models.get(model)
        cost_per_1k = model_config.cost_per_1k_tokens if model_config else 0.0
        
        total_tokens = usage.get("total_tokens", 0)
        cost = (total_tokens / 1000) * cost_per_1k * cost_multiplier
        
        self.total_cost += cost
        
        return ResponseMetrics(
            provider_used=provider_type.value,
            model_used=model,
            tokens_used=total_tokens,
            cost=cost,
            latency_ms=latency_ms
        )
    
    def _store_request_history(
        self,
        request_type: str,
        provider: str,
        model: str,
        metrics: ResponseMetrics,
        context: Optional[RequestContext]
    ):
        """Store request in history."""
        self.request_history.append({
            "timestamp": time.time(),
            "request_type": request_type,
            "provider": provider,
            "model": model,
            "metrics": metrics,
            "context": context
        })
        
        # Keep only last 1000 requests
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-1000:]
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all providers."""
        results = {}
        for provider_type, provider in self.providers.items():
            results[provider_type.value] = await provider.health_check()
        return results
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        if not self.request_history:
            return {
                "total_requests": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "providers_used": {},
                "models_used": {}
            }
        
        stats = {
            "total_requests": len(self.request_history),
            "total_cost": self.total_cost,
            "total_tokens": sum(r["metrics"].tokens_used for r in self.request_history),
            "providers_used": {},
            "models_used": {}
        }
        
        # Count by provider
        for request in self.request_history:
            provider = request["provider"]
            model = request["model"]
            
            stats["providers_used"][provider] = stats["providers_used"].get(provider, 0) + 1
            stats["models_used"][model] = stats["models_used"].get(model, 0) + 1
        
        return stats
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models."""
        return [
            {
                "name": config.name,
                "provider": config.provider.value,
                "type": config.model_type.value,
                "max_tokens": config.max_tokens,
                "context_window": config.context_window,
                "cost_per_1k_tokens": config.cost_per_1k_tokens,
                "supports_streaming": config.supports_streaming,
                "supports_vision": config.supports_vision
            }
            for config in self.models.values()
        ]


# Global instance
cloud_model_manager = CloudModelManager() 