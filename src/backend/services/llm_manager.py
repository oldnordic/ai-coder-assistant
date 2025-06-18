"""
llm_manager.py

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
LLM Manager - Main orchestrator for multiple AI providers.
Manages providers, models, and provides unified interface.
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

from .models import ProviderType, ModelType, ModelConfig, ProviderConfig, LLMModel, ChatMessage, ChatCompletionRequest, ChatCompletionResponse, ModelUsage, LLMStudioConfig
from .providers import OpenAIProvider, GoogleGeminiProvider, ClaudeProvider, OllamaProvider

logger = logging.getLogger(__name__)


class LLMManager:
    """
    Main LLM manager that orchestrates multiple AI providers.
    Provides unified interface for all supported providers.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "llm_studio_config.json"
        self.config = self._load_config()
        self.providers: Dict[ProviderType, Any] = {}
        self.models: Dict[str, LLMModel] = {}
        self.usage_stats: Dict[str, ModelUsage] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=5)
        
        self._initialize_providers()
        self._initialize_models()
    
    def _load_config(self) -> LLMStudioConfig:
        """Load configuration from file."""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                # Convert string enums back to enum objects
                if 'default_provider' in data:
                    data['default_provider'] = ProviderType(data['default_provider'])
                
                if 'providers' in data:
                    for provider_type_str, provider_data in data['providers'].items():
                        provider_data['provider_type'] = ProviderType(provider_type_str)
                        data['providers'][provider_type_str] = ProviderConfig(**provider_data)
                
                if 'models' in data:
                    for model_name, model_data in data['models'].items():
                        model_data['provider'] = ProviderType(model_data['provider'])
                        model_data['model_type'] = ModelType(model_data['model_type'])
                        data['models'][model_name] = ModelConfig(**model_data)
                
                return LLMStudioConfig(**data)
            else:
                return self._create_default_config()
                
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> LLMStudioConfig:
        """Create default configuration."""
        config = LLMStudioConfig()
        
        # Add default models
        config.models.update({
            "gpt-3.5-turbo": ModelConfig(
                name="gpt-3.5-turbo",
                provider=ProviderType.OPENAI,
                model_type=ModelType.CHAT,
                is_default=True
            ),
            "gpt-4": ModelConfig(
                name="gpt-4",
                provider=ProviderType.OPENAI,
                model_type=ModelType.CHAT
            ),
            "gemini-pro": ModelConfig(
                name="gemini-pro",
                provider=ProviderType.GOOGLE_GEMINI,
                model_type=ModelType.CHAT
            ),
            "claude-3-sonnet": ModelConfig(
                name="claude-3-sonnet-20240229",
                provider=ProviderType.CLAUDE,
                model_type=ModelType.CHAT
            )
        })
        
        return config
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                # Convert enums to strings for JSON serialization
                config_dict = {
                    'default_provider': self.config.default_provider.value,
                    'default_model': self.config.default_model,
                    'enable_fallback': self.config.enable_fallback,
                    'enable_retry': self.config.enable_retry,
                    'max_concurrent_requests': self.config.max_concurrent_requests,
                    'request_timeout': self.config.request_timeout,
                    'enable_logging': self.config.enable_logging,
                    'enable_metrics': self.config.enable_metrics,
                    'cost_tracking': self.config.cost_tracking,
                    'auto_switch_on_error': self.config.auto_switch_on_error,
                    'providers': {},
                    'models': {}
                }
                
                # Convert providers
                for provider_type, provider_config in self.config.providers.items():
                    provider_dict = provider_config.__dict__.copy()
                    provider_dict['provider_type'] = provider_type.value
                    config_dict['providers'][provider_type.value] = provider_dict
                
                # Convert models
                for model_name, model_config in self.config.models.items():
                    model_dict = model_config.__dict__.copy()
                    model_dict['provider'] = model_config.provider.value
                    model_dict['model_type'] = model_config.model_type.value
                    config_dict['models'][model_name] = model_dict
                
                json.dump(config_dict, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def _initialize_providers(self):
        """Initialize all configured providers."""
        for provider_type, provider_config in self.config.providers.items():
            if not provider_config.is_enabled:
                continue
                
            try:
                if provider_type == ProviderType.OPENAI:
                    self.providers[provider_type] = OpenAIProvider(provider_config)
                elif provider_type == ProviderType.GOOGLE_GEMINI:
                    self.providers[provider_type] = GoogleGeminiProvider(provider_config)
                elif provider_type == ProviderType.CLAUDE:
                    self.providers[provider_type] = ClaudeProvider(provider_config)
                elif provider_type == ProviderType.OLLAMA:
                    self.providers[provider_type] = OllamaProvider(provider_config)
                
                logger.info(f"Initialized {provider_type.value} provider")
                
            except Exception as e:
                logger.error(f"Failed to initialize {provider_type.value} provider: {e}")
    
    def _initialize_models(self):
        """Initialize models from configuration."""
        for model_name, model_config in self.config.models.items():
            if model_name in self.config.providers:
                provider_config = self.config.providers[model_config.provider]
                self.models[model_name] = LLMModel(
                    config=model_config,
                    provider_config=provider_config
                )
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        **kwargs
    ) -> ChatCompletionResponse:
        """
        Send chat completion request with fallback support.
        
        Args:
            messages: List of chat messages
            model: Model to use (uses default if not specified)
            **kwargs: Additional parameters for the request
            
        Returns:
            ChatCompletionResponse from the successful provider
        """
        if not model:
            model = self.config.default_model
        
        # Create request
        request = ChatCompletionRequest(
            messages=messages,
            model=model,
            **kwargs
        )
        
        # Get model configuration
        model_config = self.config.models.get(model)
        if not model_config:
            raise ValueError(f"Model {model} not found in configuration")
        
        # Try primary provider
        primary_provider = self.providers.get(model_config.provider)
        if primary_provider:
            try:
                response = await primary_provider.chat_completion(request)
                await self._update_usage_stats(response)
                return response
            except Exception as e:
                logger.warning(f"Primary provider failed: {e}")
                if not self.config.enable_fallback:
                    raise
        
        # Try fallback providers
        if self.config.enable_fallback:
            fallback_providers = [
                (pt, p) for pt, p in self.providers.items()
                if pt != model_config.provider and p is not None
            ]
            
            # Sort by priority
            fallback_providers.sort(key=lambda x: x[1].config.priority)
            
            for provider_type, provider in fallback_providers:
                try:
                    # Find compatible model
                    compatible_model = await self._find_compatible_model(provider, model_config)
                    if compatible_model:
                        request.model = compatible_model
                        response = await provider.chat_completion(request)
                        await self._update_usage_stats(response)
                        logger.info(f"Used fallback provider: {provider_type.value}")
                        return response
                except Exception as e:
                    logger.warning(f"Fallback provider {provider_type.value} failed: {e}")
                    continue
        
        raise Exception("All providers failed")
    
    async def _find_compatible_model(self, provider, target_model_config: ModelConfig) -> Optional[str]:
        """Find a compatible model in the provider."""
        try:
            available_models = await provider.list_models()
            
            # Look for models with similar capabilities
            for model_config in available_models:
                if (model_config.model_type == target_model_config.model_type and
                    model_config.is_enabled):
                    return model_config.name
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding compatible model: {e}")
            return None
    
    async def _update_usage_stats(self, response: ChatCompletionResponse):
        """Update usage statistics."""
        if not self.config.cost_tracking:
            return
        
        model_name = response.model
        provider = response.provider
        
        with self._lock:
            if model_name not in self.usage_stats:
                self.usage_stats[model_name] = ModelUsage(
                    model_name=model_name,
                    provider=provider,
                    tokens_used=0,
                    requests_made=0,
                    total_cost=0.0,
                    average_response_time=0.0,
                    last_used=datetime.now(),
                    success_rate=1.0
                )
            
            stats = self.usage_stats[model_name]
            
            # Update statistics
            if response.usage:
                stats.tokens_used += response.usage.get("prompt_tokens", 0) + response.usage.get("completion_tokens", 0)
            
            stats.requests_made += 1
            stats.total_cost += response.cost or 0.0
            
            # Update average response time
            total_time = stats.average_response_time * (stats.requests_made - 1) + response.response_time
            stats.average_response_time = total_time / stats.requests_made
            
            stats.last_used = datetime.now()
    
    def add_provider(self, provider_config: ProviderConfig):
        """Add a new provider."""
        try:
            if provider_config.provider_type == ProviderType.OPENAI:
                provider = OpenAIProvider(provider_config)
            elif provider_config.provider_type == ProviderType.GOOGLE_GEMINI:
                provider = GoogleGeminiProvider(provider_config)
            elif provider_config.provider_type == ProviderType.CLAUDE:
                provider = ClaudeProvider(provider_config)
            elif provider_config.provider_type == ProviderType.OLLAMA:
                provider = OllamaProvider(provider_config)
            else:
                raise ValueError(f"Unsupported provider type: {provider_config.provider_type}")
            
            self.providers[provider_config.provider_type] = provider
            self.config.providers[provider_config.provider_type] = provider_config
            self._save_config()
            
            logger.info(f"Added provider: {provider_config.provider_type.value}")
            
        except Exception as e:
            logger.error(f"Error adding provider: {e}")
            raise
    
    def remove_provider(self, provider_type: ProviderType):
        """Remove a provider."""
        if provider_type in self.providers:
            del self.providers[provider_type]
            if provider_type in self.config.providers:
                del self.config.providers[provider_type]
            self._save_config()
            logger.info(f"Removed provider: {provider_type.value}")
    
    def add_model(self, model_config: ModelConfig):
        """Add a new model."""
        self.config.models[model_config.name] = model_config
        self._save_config()
        logger.info(f"Added model: {model_config.name}")
    
    def remove_model(self, model_name: str):
        """Remove a model."""
        if model_name in self.config.models:
            del self.config.models[model_name]
            self._save_config()
            logger.info(f"Removed model: {model_name}")
    
    async def list_available_models(self) -> List[ModelConfig]:
        """List all available models from all providers."""
        models = []
        
        for provider_type, provider in self.providers.items():
            try:
                provider_models = await provider.list_models()
                models.extend(provider_models)
            except Exception as e:
                logger.error(f"Error listing models for {provider_type.value}: {e}")
        
        return models
    
    async def health_check(self) -> Dict[ProviderType, bool]:
        """Check health of all providers."""
        health_status = {}
        
        for provider_type, provider in self.providers.items():
            try:
                health_status[provider_type] = await provider.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {provider_type.value}: {e}")
                health_status[provider_type] = False
        
        return health_status
    
    def get_usage_stats(self) -> Dict[str, ModelUsage]:
        """Get usage statistics for all models."""
        with self._lock:
            return self.usage_stats.copy()
    
    def get_total_cost(self) -> float:
        """Get total cost across all models."""
        with self._lock:
            return sum(stats.total_cost for stats in self.usage_stats.values())
    
    def reset_usage_stats(self):
        """Reset usage statistics."""
        with self._lock:
            self.usage_stats.clear()
    
    def get_config(self) -> LLMStudioConfig:
        """Get current configuration."""
        return self.config
    
    def update_config(self, **kwargs):
        """Update configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        self._save_config()
    
    async def test_provider(self, provider_type: ProviderType, api_key: str) -> bool:
        """Test a provider with given API key."""
        try:
            # Create temporary provider config
            temp_config = ProviderConfig(
                provider_type=provider_type,
                api_key=api_key
            )
            
            # Create temporary provider
            if provider_type == ProviderType.OPENAI:
                provider = OpenAIProvider(temp_config)
            elif provider_type == ProviderType.GOOGLE_GEMINI:
                provider = GoogleGeminiProvider(temp_config)
            elif provider_type == ProviderType.CLAUDE:
                provider = ClaudeProvider(temp_config)
            elif provider_type == ProviderType.OLLAMA:
                provider = OllamaProvider(temp_config)
            else:
                return False
            
            # Test health check
            return await provider.health_check()
            
        except Exception as e:
            logger.error(f"Provider test failed: {e}")
            return False
    
    def export_config(self, file_path: str):
        """Export configuration to file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.config.__dict__, f, indent=2, default=str)
            logger.info(f"Configuration exported to: {file_path}")
        except Exception as e:
            logger.error(f"Error exporting config: {e}")
            raise
    
    def import_config(self, file_path: str):
        """Import configuration from file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert string enums back to enum objects
            if 'default_provider' in data:
                data['default_provider'] = ProviderType(data['default_provider'])
            
            if 'providers' in data:
                for provider_type_str, provider_data in data['providers'].items():
                    provider_data['provider_type'] = ProviderType(provider_type_str)
                    data['providers'][provider_type_str] = ProviderConfig(**provider_data)
            
            if 'models' in data:
                for model_name, model_data in data['models'].items():
                    model_data['provider'] = ProviderType(model_data['provider'])
                    model_data['model_type'] = ModelType(model_data['model_type'])
                    data['models'][model_name] = ModelConfig(**model_data)
            
            self.config = LLMStudioConfig(**data)
            self._save_config()
            
            # Reinitialize providers
            self._initialize_providers()
            self._initialize_models()
            
            logger.info(f"Configuration imported from: {file_path}")
            
        except Exception as e:
            logger.error(f"Error importing config: {e}")
            raise 