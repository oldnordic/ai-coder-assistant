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

from src.core.config import Config
from src.backend.utils.secrets import get_secrets_manager, is_provider_configured
from src.backend.services.security_intelligence import (
    SecurityBreach,
    SecurityFeed,
    SecurityIntelligenceService,
    SecurityPatch,
    SecurityVulnerability,
)
from src.backend.services.providers import (
    ClaudeProvider,
    GoogleGeminiProvider,
    OllamaProvider,
    OpenAIProvider,
    LMStudioProvider,
)
from src.backend.services.pr_automation import (
    PRAutomationService,
    PRRequest,
    PRResult,
    PRTemplate,
    ServiceConfig,
)
from src.backend.services.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    LLMModel,
    LLMStudioConfig,
    ModelConfig,
    ModelType,
    ModelUsage,
    ProviderConfig,
    ProviderType,
)
from src.backend.services.code_standards import (
    CodeAnalysisResult,
    CodeStandard,
    CodeStandardsService,
)
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading
import logging
import asyncio
import json


logger = logging.getLogger(__name__)


class LLMManager:
    """
    Main LLM manager that orchestrates multiple AI providers.
    Provides unified interface for all supported providers.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the LLMManager with a path to the configuration file."""
        self._config_manager = Config()
        self.config_path = config_path or str(
            self._config_manager.get_config_file_path("llm_studio_config.json")
        )
        self.config = self._load_config()
        self.providers: Dict[ProviderType, Any] = {}
        self.models: Dict[str, LLMModel] = {}
        self.usage_stats: Dict[str, ModelUsage] = {}
        self.ollama_instances: Dict[str, OllamaProvider] = (
            {}
        )  # instance_name -> OllamaProvider
        self.pr_automation = PRAutomationService()  # PR automation service

        # Initialize security intelligence with correct config path
        self.security_intelligence = SecurityIntelligenceService()

        # Initialize code standards with correct config path
        code_standards_config_path = str(
            self._config_manager.get_config_file_path("code_standards_config.json")
        )
        self.code_standards = CodeStandardsService(code_standards_config_path)

        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=5)

        self._initialize_providers()
        self._initialize_ollama_instances()
        self._initialize_models()

    def _load_raw_config_file(self, config_path: str) -> Optional[dict[str, Any]]:
        """Load and return the raw config file as a dictionary, or None if not found."""
        if Path(config_path).exists():
            with open(config_path, "r") as f:
                return json.load(f)
        return None

    def _load_config(self) -> LLMStudioConfig:
        """Load configuration from file or create default if not found."""
        raw_data = self._load_raw_config_file(self.config_path)
        
        if raw_data is None:
            logger.info(f"Config file not found at {self.config_path}, creating default configuration")
            config = self._create_default_config()
            # Save the default config so it exists for future use
            self._save_config()
            return config
        
        try:
            # Parse the configuration
            models = self._parse_model_configurations(raw_data)
            providers = self._parse_provider_configurations(raw_data, models)
            default_model = self._parse_studio_settings(raw_data)
            
            # Create the config object
            config = LLMStudioConfig()
            config.models = models
            config.providers = providers
            config.default_model = default_model
            
            # Parse additional studio settings if present
            studio_settings = raw_data.get("studio_settings", {})
            config.enable_fallback = studio_settings.get("enable_fallback", True)
            config.enable_retry = studio_settings.get("enable_retry", True)
            config.max_concurrent_requests = studio_settings.get("max_concurrent_requests", 5)
            config.request_timeout = studio_settings.get("request_timeout", 30)
            config.enable_logging = studio_settings.get("enable_logging", True)
            config.enable_metrics = studio_settings.get("enable_metrics", True)
            config.cost_tracking = studio_settings.get("cost_tracking", True)
            config.auto_switch_on_error = studio_settings.get("auto_switch_on_error", True)
            
            logger.info(f"Configuration loaded successfully from {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Error parsing config file {self.config_path}: {e}")
            logger.info("Creating default configuration due to parsing error")
            config = self._create_default_config()
            # Save the default config so it exists for future use
            self._save_config()
            return config

    def _parse_model_configurations(self, raw_data: dict[str, Any]) -> Dict[str, ModelConfig]:
        """Parse model configurations from raw config data."""
        models: Dict[str, ModelConfig] = {}
        default_model = raw_data.get("studio_settings", {}).get("default_model", "gpt-3.5-turbo")
        for model_name, model_data in raw_data.get("model_configurations", {}).items():
            provider_type = ProviderType(model_data["provider"])
            models[model_name] = ModelConfig(
                name=model_name,
                provider=provider_type,
                model_type=ModelType.CHAT,  # Default to chat
                max_tokens=model_data.get("max_tokens", 4096),
                temperature=0.7,  # Default temperature
                is_default=(model_name == default_model),
                cost_per_1k_tokens=model_data.get("cost_per_1k_tokens"),
                capabilities=model_data.get("supported_features", []),
            )
        return models

    def _parse_provider_configurations(self, raw_data: dict[str, Any], models: Dict[str, ModelConfig]) -> Dict[ProviderType, ProviderConfig]:
        """Parse provider configurations from raw config data and models."""
        providers: Dict[ProviderType, ProviderConfig] = {}
        for model in models.values():
            provider_type = model.provider
            if provider_type not in providers:
                providers[provider_type] = ProviderConfig(
                    provider_type=provider_type,
                    api_key="",  # Will be loaded from environment
                    is_enabled=True,
                )
        return providers

    def _parse_studio_settings(self, raw_data: dict[str, Any]) -> str:
        """Parse studio settings and return the default model name."""
        return raw_data.get("studio_settings", {}).get("default_model", "gpt-3.5-turbo")

    def _create_default_config(self) -> LLMStudioConfig:
        """Create default configuration."""
        config = LLMStudioConfig()

        # Add default models
        config.models.update(
            {
                "gpt-3.5-turbo": ModelConfig(
                    name="gpt-3.5-turbo",
                    provider=ProviderType.OPENAI,
                    model_type=ModelType.CHAT,
                    is_default=True,
                ),
                "gpt-4": ModelConfig(
                    name="gpt-4",
                    provider=ProviderType.OPENAI,
                    model_type=ModelType.CHAT,
                ),
                "gemini-pro": ModelConfig(
                    name="gemini-pro",
                    provider=ProviderType.GOOGLE_GEMINI,
                    model_type=ModelType.CHAT,
                ),
                "claude-3-sonnet": ModelConfig(
                    name="claude-3-sonnet-20240229",
                    provider=ProviderType.CLAUDE,
                    model_type=ModelType.CHAT,
                ),
                "local-model": ModelConfig(
                    name="local-model",
                    provider=ProviderType.LM_STUDIO,
                    model_type=ModelType.CHAT,
                    cost_per_1k_tokens=0.0,  # Free for local models
                    capabilities=["chat", "completion"],
                    metadata={"source": "lm_studio", "local": True},
                ),
            }
        )

        # Add default providers
        config.providers.update(
            {
                ProviderType.OPENAI: ProviderConfig(
                    provider_type=ProviderType.OPENAI,
                    api_key="",  # Will be loaded from environment
                    is_enabled=True,
                ),
                ProviderType.GOOGLE_GEMINI: ProviderConfig(
                    provider_type=ProviderType.GOOGLE_GEMINI,
                    api_key="",  # Will be loaded from environment
                    is_enabled=True,
                ),
                ProviderType.CLAUDE: ProviderConfig(
                    provider_type=ProviderType.CLAUDE,
                    api_key="",  # Will be loaded from environment
                    is_enabled=True,
                ),
            }
        )

        return config

    def _save_config(self):
        """Save configuration to file."""
        try:
            # Convert config to dictionary format
            config_data = {
                "studio_settings": {
                    "default_model": self.config.default_model,
                    "enable_fallback": self.config.enable_fallback,
                    "enable_retry": self.config.enable_retry,
                    "max_concurrent_requests": self.config.max_concurrent_requests,
                    "request_timeout": self.config.request_timeout,
                    "enable_logging": self.config.enable_logging,
                    "enable_metrics": self.config.enable_metrics,
                    "cost_tracking": self.config.cost_tracking,
                    "auto_switch_on_error": self.config.auto_switch_on_error,
                },
                "model_configurations": {},
            }

            # Convert models
            for model_name, model_config in self.config.models.items():
                config_data["model_configurations"][model_name] = {
                    "provider": model_config.provider.value,
                    "max_tokens": model_config.max_tokens,
                    "cost_per_1k_tokens": model_config.cost_per_1k_tokens,
                    "supported_features": model_config.capabilities,
                }

            # Save to file
            with open(self.config_path, "w") as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"Configuration saved to {self.config_path}")

        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def _is_provider_configured(self, provider_type: ProviderType) -> bool:
        """Check if a provider is properly configured with API keys."""
        if provider_type == ProviderType.OPENAI:
            return is_provider_configured("openai")
        elif provider_type == ProviderType.CLAUDE or provider_type == ProviderType.ANTHROPIC:
            return is_provider_configured("anthropic")
        elif provider_type == ProviderType.GOOGLE_GEMINI or provider_type == ProviderType.GOOGLE:
            return is_provider_configured("google")
        elif provider_type == ProviderType.OLLAMA:
            # Ollama is always available if it's running locally
            # We'll check availability during actual initialization
            return True
        elif provider_type == ProviderType.LM_STUDIO:
            # LM Studio is available if the local server is running
            # We'll check availability during actual initialization
            return True
        else:
            logger.warning(
                f"Unknown provider type for configuration check: {provider_type.value}"
            )
            return False

    def _initialize_providers(self):
        """Initialize only providers that are properly configured and enabled."""

        # A set to keep track of initialized providers to avoid duplicates
        initialized_providers = set()

        # Iterate over models to find out which providers are actually used
        if not self.config.models:
            logger.warning(
                "No models found in configuration. No providers will be initialized."
            )
            return

        for model_config in self.config.models.values():
            provider_type = model_config.provider

            if provider_type in initialized_providers:
                continue

            # Check if provider is enabled in config
            provider_config = self.config.providers.get(provider_type)
            if not (provider_config and provider_config.is_enabled):
                logger.debug(f"Skipping disabled provider: {provider_type.value}")
                continue

            # Check if provider is properly configured with API keys
            if not self._is_provider_configured(provider_type):
                logger.info(
                    f"Skipping unconfigured provider {provider_type.value} - no API key found"
                )
                continue

            try:
                if provider_type == ProviderType.OPENAI:
                    self.providers[provider_type] = OpenAIProvider(provider_config)
                elif provider_type == ProviderType.GOOGLE_GEMINI:
                    self.providers[provider_type] = GoogleGeminiProvider(
                        provider_config
                    )
                elif provider_type == ProviderType.CLAUDE:
                    self.providers[provider_type] = ClaudeProvider(provider_config)
                elif provider_type == ProviderType.ANTHROPIC:
                    # ANTHROPIC is the same as CLAUDE (Anthropic's Claude)
                    self.providers[provider_type] = ClaudeProvider(provider_config)
                elif provider_type == ProviderType.GOOGLE:
                    # GOOGLE is the same as GOOGLE_GEMINI
                    self.providers[provider_type] = GoogleGeminiProvider(
                        provider_config
                    )
                elif provider_type == ProviderType.OLLAMA:
                    # General Ollama provider. Specific instances are handled elsewhere.
                    if provider_type not in self.providers:
                        self.providers[provider_type] = OllamaProvider(provider_config)
                elif provider_type == ProviderType.LM_STUDIO:
                    self.providers[provider_type] = LMStudioProvider(provider_config)
                else:
                    logger.warning(
                        f"Unknown provider type encountered: {provider_type.value}"
                    )
                    continue

                logger.info(f"Initialized {provider_type.value} provider")
                initialized_providers.add(provider_type)

            except Exception as e:
                logger.error(
                    f"Failed to initialize {provider_type.value} provider: {e}"
                )

        # Log summary of initialized providers
        if initialized_providers:
            logger.info(
                f"Successfully initialized providers: {', '.join([p.value for p in initialized_providers])}"
            )
        else:
            logger.warning(
                "No providers were initialized. Check your API key configuration."
            )

    def _initialize_ollama_instances(self):
        """Initialize all Ollama instances from config."""
        self.ollama_instances = {}
        for config in getattr(self.config, "ollama_instances", []):
            if not config.is_enabled:
                continue
            try:
                provider = OllamaProvider(config)
                self.ollama_instances[config.instance_name or config.base_url] = (
                    provider
                )
                logger.info(
                    f"Initialized Ollama instance: {config.instance_name or config.base_url}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to initialize Ollama instance {config.instance_name or config.base_url}: {e}"
                )

    def _initialize_models(self):
        """Initialize models from configuration."""
        for model_name, model_config in self.config.models.items():
            if model_name in self.config.providers:
                provider_config = self.config.providers[model_config.provider]
                self.models[model_name] = LLMModel(
                    config=model_config, provider_config=provider_config
                )

    async def chat_completion(
        self, messages: List[ChatMessage], model: Optional[str] = None, **kwargs
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
        request = ChatCompletionRequest(messages=messages, model=model, **kwargs)

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
                (pt, p)
                for pt, p in self.providers.items()
                if pt != model_config.provider and p is not None
            ]

            # Sort by priority
            fallback_providers.sort(key=lambda x: x[1].config.priority)

            for provider_type, provider in fallback_providers:
                try:
                    # Find compatible model
                    compatible_model = await self._find_compatible_model(
                        provider, model_config
                    )
                    if compatible_model:
                        request.model = compatible_model
                        response = await provider.chat_completion(request)
                        await self._update_usage_stats(response)
                        logger.info(f"Used fallback provider: {provider_type.value}")
                        return response
                except Exception as e:
                    logger.warning(
                        f"Fallback provider {provider_type.value} failed: {e}"
                    )
                    continue

        raise Exception("All providers failed")

    async def _find_compatible_model(
        self, provider, target_model_config: ModelConfig
    ) -> Optional[str]:
        """Find a compatible model in the provider."""
        try:
            available_models = await provider.list_models()

            # Look for models with similar capabilities
            for model_config in available_models:
                if (
                    model_config.model_type == target_model_config.model_type
                    and model_config.is_enabled
                ):
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
                    success_rate=1.0,
                )

            stats = self.usage_stats[model_name]

            # Update statistics
            if response.usage:
                stats.tokens_used += response.usage.get(
                    "prompt_tokens", 0
                ) + response.usage.get("completion_tokens", 0)

            stats.requests_made += 1
            stats.total_cost += response.cost or 0.0

            # Update average response time
            total_time = (
                stats.average_response_time * (stats.requests_made - 1)
                + response.response_time
            )
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
            elif provider_config.provider_type == ProviderType.ANTHROPIC:
                # ANTHROPIC is the same as CLAUDE (Anthropic's Claude)
                provider = ClaudeProvider(provider_config)
            elif provider_config.provider_type == ProviderType.GOOGLE:
                # GOOGLE is the same as GOOGLE_GEMINI
                provider = GoogleGeminiProvider(provider_config)
            elif provider_config.provider_type == ProviderType.OLLAMA:
                provider = OllamaProvider(provider_config)
            elif provider_config.provider_type == ProviderType.LM_STUDIO:
                provider = LMStudioProvider(provider_config)
            else:
                raise ValueError(
                    f"Unsupported provider type: {provider_config.provider_type}"
                )

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
            temp_config = ProviderConfig(provider_type=provider_type, api_key=api_key)

            # Create temporary provider
            if provider_type == ProviderType.OPENAI:
                provider = OpenAIProvider(temp_config)
            elif provider_type == ProviderType.GOOGLE_GEMINI:
                provider = GoogleGeminiProvider(temp_config)
            elif provider_type == ProviderType.CLAUDE:
                provider = ClaudeProvider(temp_config)
            elif provider_type == ProviderType.ANTHROPIC:
                # ANTHROPIC is the same as CLAUDE (Anthropic's Claude)
                provider = ClaudeProvider(temp_config)
            elif provider_type == ProviderType.GOOGLE:
                # GOOGLE is the same as GOOGLE_GEMINI
                provider = GoogleGeminiProvider(temp_config)
            elif provider_type == ProviderType.OLLAMA:
                provider = OllamaProvider(temp_config)
            elif provider_type == ProviderType.LM_STUDIO:
                provider = LMStudioProvider(temp_config)
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
            with open(file_path, "w") as f:
                json.dump(self.config.__dict__, f, indent=2, default=str)
            logger.info(f"Configuration exported to: {file_path}")
        except Exception as e:
            logger.error(f"Error exporting config: {e}")
            raise

    def import_config(self, file_path: str):
        """Import configuration from file."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            # Convert string enums back to enum objects
            if "default_provider" in data:
                data["default_provider"] = ProviderType(data["default_provider"])

            if "providers" in data:
                for provider_type_str, provider_data in data["providers"].items():
                    provider_data["provider_type"] = ProviderType(provider_type_str)
                    data["providers"][provider_type_str] = ProviderConfig(
                        **provider_data
                    )

            if "models" in data:
                for model_name, model_data in data["models"].items():
                    model_data["provider"] = ProviderType(model_data["provider"])
                    model_data["model_type"] = ModelType(model_data["model_type"])
                    data["models"][model_name] = ModelConfig(**model_data)

            self.config = LLMStudioConfig(**data)
            self._save_config()

            # Reinitialize providers
            self._initialize_providers()
            self._initialize_models()

            logger.info(f"Configuration imported from: {file_path}")

        except Exception as e:
            logger.error(f"Error importing config: {e}")
            raise

    def add_ollama_instance(self, config: ProviderConfig):
        """Add a new Ollama instance."""
        self.config.ollama_instances.append(config)
        self._initialize_ollama_instances()
        self._save_config()

    def remove_ollama_instance(self, instance_name: str):
        """Remove an Ollama instance by name."""
        self.config.ollama_instances = [
            c for c in self.config.ollama_instances if c.instance_name != instance_name
        ]
        self._initialize_ollama_instances()
        self._save_config()

    def list_ollama_instances(self) -> List[ProviderConfig]:
        """List all Ollama instance configs."""
        return self.config.ollama_instances

    def get_ollama_models(self, instance_name: str) -> List[ModelConfig]:
        """List models for a specific Ollama instance."""
        provider = self.ollama_instances.get(instance_name)
        if not provider:
            raise Exception(f"Ollama instance '{instance_name}' not found")
        return asyncio.run(provider.list_models())

    def health_check_ollama(self, instance_name: str) -> bool:
        """Health check for a specific Ollama instance."""
        provider = self.ollama_instances.get(instance_name)
        if not provider:
            raise Exception(f"Ollama instance '{instance_name}' not found")
        return asyncio.run(provider.health_check())

    # PR Automation Methods

    async def create_pr(self, request: PRRequest, repo_path: str) -> PRResult:
        """Create a PR with optional ticket creation."""
        return await self.pr_automation.create_pr(request, repo_path)

    def add_service_config(self, config: ServiceConfig):
        """Add a new service configuration (JIRA/ServiceNow)."""
        self.pr_automation.add_service(config)

    def remove_service_config(self, service_name: str):
        """Remove a service configuration."""
        self.pr_automation.remove_service(service_name)

    def list_service_configs(self) -> List[ServiceConfig]:
        """List all service configurations."""
        return [service.config for service in self.pr_automation.services.values()]

    def add_pr_template(self, template: PRTemplate):
        """Add a new PR template."""
        self.pr_automation.add_template(template)

    def remove_pr_template(self, template_name: str):
        """Remove a PR template."""
        self.pr_automation.remove_template(template_name)

    def list_pr_templates(self) -> List[PRTemplate]:
        """List all PR templates."""
        return list(self.pr_automation.templates.values())

    def get_default_pr_template(self) -> Optional[PRTemplate]:
        """Get the default PR template."""
        return self.pr_automation.get_default_template()

    async def test_service_connection(self, service_name: str) -> bool:
        """Test connection to a specific service."""
        return await self.pr_automation.test_service_connection(service_name)

    def get_pr_automation_config(self) -> Dict[str, Any]:
        """Get PR automation configuration."""
        return {
            "services": [
                service.config.__dict__
                for service in self.pr_automation.services.values()
            ],
            "templates": [
                template.__dict__ for template in self.pr_automation.templates.values()
            ],
        }

    # Security Intelligence Methods

    async def fetch_security_feeds(self):
        """Fetch security data from configured feeds."""
        try:
            await self.security_intelligence.fetch_security_feeds()
        except Exception as e:
            logger.error(f"Error fetching security feeds: {e}")
            raise

    def get_security_vulnerabilities(
        self, severity: Optional[str] = None, limit: int = 100
    ) -> List[SecurityVulnerability]:
        """Get security vulnerabilities with optional filtering."""
        return self.security_intelligence.get_vulnerabilities(severity, limit)

    def get_security_breaches(self, limit: int = 100) -> List[SecurityBreach]:
        """Get security breaches."""
        return self.security_intelligence.get_breaches(limit)

    def get_security_patches(self, limit: int = 100) -> List[SecurityPatch]:
        """Get security patches."""
        return self.security_intelligence.get_patches(limit)

    def get_security_training_data(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get security training data for AI models."""
        return self.security_intelligence.get_training_data(limit)

    def search_security_vulnerabilities(
        self, query: str
    ) -> List[SecurityVulnerability]:
        """Search security vulnerabilities by query."""
        return self.security_intelligence.search_vulnerabilities(query)

    def add_security_feed(self, feed: SecurityFeed):
        """Add a new security feed."""
        self.security_intelligence.add_feed(feed)

    def remove_security_feed(self, feed_name: str):
        """Remove a security feed."""
        self.security_intelligence.remove_feed(feed_name)

    def get_security_feeds(self) -> List[SecurityFeed]:
        """Get all configured security feeds."""
        return self.security_intelligence.get_feeds()

    def mark_patch_applied(self, patch_id: str):
        """Mark a security patch as applied."""
        self.security_intelligence.mark_patch_applied(patch_id)

    def mark_vulnerability_patched(self, vuln_id: str):
        """Mark a vulnerability as patched."""
        self.security_intelligence.mark_vulnerability_patched(vuln_id)

    # Code Standards Methods

    def add_code_standard(self, standard: CodeStandard):
        """Add a new code standard."""
        self.code_standards.add_standard(standard)

    def remove_code_standard(self, standard_name: str):
        """Remove a code standard."""
        self.code_standards.remove_standard(standard_name)

    def get_code_standards(self) -> List[CodeStandard]:
        """Get all code standards."""
        return self.code_standards.get_standards()

    def get_current_code_standard(self) -> Optional[CodeStandard]:
        """Get current code standard."""
        return self.code_standards.current_standard

    def set_current_code_standard(self, standard_name: str):
        """Set the current active code standard."""
        self.code_standards.set_current_standard(standard_name)

    def analyze_code_file(self, file_path: str) -> CodeAnalysisResult:
        """Analyze a single file for code standard violations."""
        return self.code_standards.analyze_file(file_path)

    def analyze_code_directory(self, directory_path: str) -> List[CodeAnalysisResult]:
        """Analyze all files in a directory for code standard violations."""
        return self.code_standards.analyze_directory(directory_path)

    def auto_fix_code_violations(self, violations: List[Any]) -> List[Any]:
        """Automatically fix code violations where possible."""
        return self.code_standards.auto_fix_violations(violations)

    def export_code_standard(self, standard_name: str, export_path: str):
        """Export a code standard to a file."""
        self.code_standards.export_standard(standard_name, export_path)

    def import_code_standard(self, import_path: str):
        """Import a code standard from a file."""
        self.code_standards.import_standard(import_path)

    def get_code_standards_config(self) -> Dict[str, Any]:
        """Get code standards configuration."""
        current_standard = self.get_current_code_standard()
        return {
            "standards": [standard.__dict__ for standard in self.get_code_standards()],
            "current_standard": current_standard.name if current_standard else None,
        }

    async def list_ollama_models(
        self,
        progress_callback=None,
        log_message_callback=None,
        cancellation_callback=None,
    ) -> List[str]:
        """List all available local models from Ollama."""
        ollama_provider = self.providers.get(ProviderType.OLLAMA)
        if not ollama_provider:
            return []

        try:
            return await ollama_provider.list_models()
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []

    async def generate_with_ollama(self, prompt: str, model: str) -> str:
        """Generate text using Ollama."""
        try:
            provider = self.providers.get(ProviderType.OLLAMA)
            if not provider:
                raise Exception("Ollama provider not initialized")
            request = ChatCompletionRequest(
                messages=[ChatMessage(role="user", content=prompt)], model=model
            )
            response = await provider.chat_completion(request)
            return response.choices[0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error generating with Ollama: {e}")
            return f"Error: {e}"

    async def delete_model(self, model_name: str) -> bool:
        """Delete an Ollama model."""
        try:
            provider = self.providers.get(ProviderType.OLLAMA)
            if not provider:
                raise Exception("Ollama provider not initialized")
            await provider.delete_model(model_name)
            return True
        except Exception as e:
            logger.error(f"Error deleting model {model_name}: {e}")
            raise

    def get_code_standards_manager(self) -> "CodeStandardsService":
        """Get the CodeStandardsService instance."""
        from src.backend.services.code_standards import CodeStandardsService

        # Use centralized configuration management
        code_standards_config_path = str(
            self._config_manager.get_config_file_path("code_standards_config.json")
        )
        return CodeStandardsService(config_path=code_standards_config_path)

    def get_security_intelligence(self) -> "SecurityIntelligence":
        """Get the SecurityIntelligence instance."""
        from src.backend.services.security_intelligence import SecurityIntelligence

        # Use centralized configuration management
        security_config_path = str(
            self._config_manager.get_config_file_path(
                "security_intelligence_config.json"
            )
        )
        return SecurityIntelligence(config_path=security_config_path)
