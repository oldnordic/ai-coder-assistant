"""
Unit tests for Cloud Model Integration Service

Tests multi-provider LLM integration, failover, cost control,
and unified interface functionality.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

from src.backend.services.cloud_models import (
    CloudModelManager, ProviderType, ModelType, ModelConfig,
    ProviderConfig, RequestContext, ResponseMetrics,
    OpenAIProvider, AnthropicProvider, GoogleProvider,
    BaseProvider
)


class TestProviderTypes:
    """Test provider type enums."""
    
    def test_provider_types(self):
        """Test provider type enum values."""
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.ANTHROPIC.value == "anthropic"
        assert ProviderType.GOOGLE.value == "google"
        assert ProviderType.AZURE.value == "azure"
        assert ProviderType.AWS_BEDROCK.value == "aws_bedrock"
        assert ProviderType.COHERE.value == "cohere"
    
    def test_model_types(self):
        """Test model type enum values."""
        assert ModelType.CHAT.value == "chat"
        assert ModelType.COMPLETION.value == "completion"
        assert ModelType.EMBEDDING.value == "embedding"
        assert ModelType.VISION.value == "vision"


class TestModelConfig:
    """Test model configuration."""
    
    def test_model_config_creation(self):
        """Test creating model configuration."""
        config = ModelConfig(
            name="test-model",
            provider=ProviderType.OPENAI,
            model_type=ModelType.CHAT,
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_tokens=0.01,
            context_window=8192
        )
        
        assert config.name == "test-model"
        assert config.provider == ProviderType.OPENAI
        assert config.model_type == ModelType.CHAT
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.cost_per_1k_tokens == 0.01
        assert config.context_window == 8192
        assert config.supports_streaming is True
        assert config.supports_vision is False
        assert config.is_available is True


class TestProviderConfig:
    """Test provider configuration."""
    
    def test_provider_config_creation(self):
        """Test creating provider configuration."""
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key="test-key",
            base_url="https://api.openai.com",
            organization="test-org",
            timeout=30,
            max_retries=3,
            priority=1,
            cost_multiplier=1.0
        )
        
        assert config.provider_type == ProviderType.OPENAI
        assert config.api_key == "test-key"
        assert config.base_url == "https://api.openai.com"
        assert config.organization == "test-org"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.priority == 1
        assert config.cost_multiplier == 1.0
        assert config.is_enabled is True


class TestRequestContext:
    """Test request context."""
    
    def test_request_context_creation(self):
        """Test creating request context."""
        context = RequestContext(
            user_id="user123",
            session_id="session456",
            request_id="req789",
            metadata={"source": "test"}
        )
        
        assert context.user_id == "user123"
        assert context.session_id == "session456"
        assert context.request_id == "req789"
        assert context.metadata == {"source": "test"}


class TestResponseMetrics:
    """Test response metrics."""
    
    def test_response_metrics_creation(self):
        """Test creating response metrics."""
        metrics = ResponseMetrics(
            provider_used="openai",
            model_used="gpt-4",
            tokens_used=1000,
            cost=0.03,
            latency_ms=1500.5,
            retries=1,
            fallback_used=True
        )
        
        assert metrics.provider_used == "openai"
        assert metrics.model_used == "gpt-4"
        assert metrics.tokens_used == 1000
        assert metrics.cost == 0.03
        assert metrics.latency_ms == 1500.5
        assert metrics.retries == 1
        assert metrics.fallback_used is True


class TestBaseProvider:
    """Test base provider abstract class."""
    
    def test_base_provider_abstract(self):
        """Test that BaseProvider cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseProvider(MagicMock())


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock provider config."""
        return ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key="test-key",
            base_url="https://api.openai.com",
            organization="test-org"
        )
    
    @pytest.fixture
    def mock_client(self):
        """Create mock OpenAI client."""
        return AsyncMock()
    
    @patch('src.backend.services.cloud_models.AsyncOpenAI')
    def test_openai_provider_initialization(self, mock_openai, mock_config):
        """Test OpenAI provider initialization."""
        mock_openai.return_value = AsyncMock()
        
        provider = OpenAIProvider(mock_config)
        
        assert provider.config == mock_config
        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.openai.com",
            organization="test-org",
            timeout=30
        )
    
    @pytest.mark.asyncio
    async def test_openai_chat_completion(self, mock_config):
        """Test OpenAI chat completion."""
        with patch('src.backend.services.cloud_models.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            # Mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response"
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 20
            mock_response.usage.total_tokens = 30
            mock_response.model = "gpt-4"
            mock_response.choices[0].finish_reason = "stop"
            
            mock_client.chat.completions.create.return_value = mock_response
            
            provider = OpenAIProvider(mock_config)
            
            messages = [{"role": "user", "content": "Hello"}]
            result = await provider.chat_completion(messages, "gpt-4")
            
            assert result["content"] == "Test response"
            assert result["usage"]["total_tokens"] == 30
            assert result["model"] == "gpt-4"
            assert result["finish_reason"] == "stop"
    
    @pytest.mark.asyncio
    async def test_openai_text_completion(self, mock_config):
        """Test OpenAI text completion."""
        with patch('src.backend.services.cloud_models.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            # Mock response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].text = "Test completion"
            mock_response.usage.prompt_tokens = 5
            mock_response.usage.completion_tokens = 15
            mock_response.usage.total_tokens = 20
            mock_response.model = "text-davinci-003"
            mock_response.choices[0].finish_reason = "stop"
            
            mock_client.completions.create.return_value = mock_response
            
            provider = OpenAIProvider(mock_config)
            
            result = await provider.text_completion("Test prompt", "text-davinci-003")
            
            assert result["content"] == "Test completion"
            assert result["usage"]["total_tokens"] == 20
            assert result["model"] == "text-davinci-003"
    
    @pytest.mark.asyncio
    async def test_openai_embeddings(self, mock_config):
        """Test OpenAI embeddings."""
        with patch('src.backend.services.cloud_models.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            # Mock response
            mock_response = MagicMock()
            mock_response.data = [MagicMock()]
            mock_response.data[0].embedding = [0.1, 0.2, 0.3]
            
            mock_client.embeddings.create.return_value = mock_response
            
            provider = OpenAIProvider(mock_config)
            
            texts = ["Test text"]
            result = await provider.embeddings(texts, "text-embedding-ada-002")
            
            assert result == [[0.1, 0.2, 0.3]]
    
    @pytest.mark.asyncio
    async def test_openai_health_check(self, mock_config):
        """Test OpenAI health check."""
        with patch('src.backend.services.cloud_models.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            provider = OpenAIProvider(mock_config)
            
            result = await provider.health_check()
            assert result is True


class TestAnthropicProvider:
    """Test Anthropic provider implementation."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock provider config."""
        return ProviderConfig(
            provider_type=ProviderType.ANTHROPIC,
            api_key="test-key"
        )
    
    @patch('src.backend.services.cloud_models.AsyncAnthropic')
    def test_anthropic_provider_initialization(self, mock_anthropic, mock_config):
        """Test Anthropic provider initialization."""
        mock_anthropic.return_value = AsyncMock()
        
        provider = AnthropicProvider(mock_config)
        
        assert provider.config == mock_config
        mock_anthropic.assert_called_once_with(
            api_key="test-key",
            timeout=30
        )
    
    @pytest.mark.asyncio
    async def test_anthropic_chat_completion(self, mock_config):
        """Test Anthropic chat completion."""
        with patch('src.backend.services.cloud_models.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client
            
            # Mock response
            mock_response = MagicMock()
            mock_response.content = [MagicMock()]
            mock_response.content[0].text = "Test response"
            mock_response.usage.input_tokens = 10
            mock_response.usage.output_tokens = 20
            mock_response.model = "claude-3-sonnet"
            mock_response.stop_reason = "end_turn"
            
            mock_client.messages.create.return_value = mock_response
            
            provider = AnthropicProvider(mock_config)
            
            messages = [{"role": "user", "content": "Hello"}]
            result = await provider.chat_completion(messages, "claude-3-sonnet")
            
            assert result["content"] == "Test response"
            assert result["usage"]["total_tokens"] == 30
            assert result["model"] == "claude-3-sonnet"
            assert result["finish_reason"] == "end_turn"
    
    @pytest.mark.asyncio
    async def test_anthropic_embeddings_not_implemented(self, mock_config):
        """Test that Anthropic embeddings raises NotImplementedError."""
        with patch('src.backend.services.cloud_models.AsyncAnthropic') as mock_anthropic:
            mock_anthropic.return_value = AsyncMock()
            
            provider = AnthropicProvider(mock_config)
            
            with pytest.raises(NotImplementedError):
                await provider.embeddings(["test"], "claude-3-sonnet")


class TestGoogleProvider:
    """Test Google AI provider implementation."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock provider config."""
        return ProviderConfig(
            provider_type=ProviderType.GOOGLE,
            api_key="test-key"
        )
    
    @patch('src.backend.services.cloud_models.genai')
    def test_google_provider_initialization(self, mock_genai, mock_config):
        """Test Google provider initialization."""
        provider = GoogleProvider(mock_config)
        
        assert provider.config == mock_config
        mock_genai.configure.assert_called_once_with(api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_google_chat_completion(self, mock_config):
        """Test Google chat completion."""
        with patch('src.backend.services.cloud_models.genai') as mock_genai:
            # Mock response
            mock_response = MagicMock()
            mock_response.text = "Test response"
            mock_response.usage_metadata.prompt_token_count = 10
            mock_response.usage_metadata.candidates_token_count = 20
            mock_response.usage_metadata.total_token_count = 30
            
            # Mock model
            mock_model = AsyncMock()
            mock_model.generate_content_async.return_value = mock_response
            
            # Mock GenerativeModel
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig = MagicMock()
            
            provider = GoogleProvider(mock_config)
            
            messages = [{"role": "user", "content": "Hello"}]
            result = await provider.chat_completion(messages, "gemini-pro")
            
            assert result["content"] == "Test response"
            assert result["usage"]["total_tokens"] == 30
            assert result["model"] == "gemini-pro"


class TestCloudModelManager:
    """Test cloud model manager."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        return {
            "openai_api_key": "openai-key",
            "anthropic_api_key": "anthropic-key",
            "google_api_key": "google-key"
        }
    
    @patch('src.backend.services.cloud_models.get_settings')
    def test_cloud_model_manager_initialization(self, mock_get_settings, mock_settings):
        """Test cloud model manager initialization."""
        mock_get_settings.return_value = mock_settings
        
        with patch('src.backend.services.cloud_models.OpenAIProvider') as mock_openai:
            with patch('src.backend.services.cloud_models.AnthropicProvider') as mock_anthropic:
                with patch('src.backend.services.cloud_models.GoogleProvider') as mock_google:
                    manager = CloudModelManager()
                    
                    assert len(manager.providers) == 3
                    assert ProviderType.OPENAI in manager.providers
                    assert ProviderType.ANTHROPIC in manager.providers
                    assert ProviderType.GOOGLE in manager.providers
                    assert len(manager.models) > 0
    
    def test_get_available_models(self):
        """Test getting available models."""
        with patch('src.backend.services.cloud_models.get_settings') as mock_get_settings:
            mock_get_settings.return_value = {}
            
            manager = CloudModelManager()
            models = manager.get_available_models()
            
            assert isinstance(models, list)
            assert len(models) > 0
            
            # Check model structure
            model = models[0]
            assert "name" in model
            assert "provider" in model
            assert "type" in model
            assert "max_tokens" in model
            assert "context_window" in model
            assert "cost_per_1k_tokens" in model
    
    def test_get_usage_stats_empty(self):
        """Test getting usage stats when no requests."""
        with patch('src.backend.services.cloud_models.get_settings') as mock_get_settings:
            mock_get_settings.return_value = {}
            
            manager = CloudModelManager()
            stats = manager.get_usage_stats()
            
            assert stats["total_requests"] == 0
            assert stats["total_cost"] == 0.0
            assert stats["total_tokens"] == 0
            assert stats["providers_used"] == {}
            assert stats["models_used"] == {}
    
    def test_get_model_config_valid(self):
        """Test getting valid model config."""
        with patch('src.backend.services.cloud_models.get_settings') as mock_get_settings:
            mock_get_settings.return_value = {}
            
            manager = CloudModelManager()
            config = manager._get_model_config("gpt-4")
            
            assert config.name == "gpt-4"
            assert config.provider == ProviderType.OPENAI
    
    def test_get_model_config_invalid(self):
        """Test getting invalid model config."""
        with patch('src.backend.services.cloud_models.get_settings') as mock_get_settings:
            mock_get_settings.return_value = {}
            
            manager = CloudModelManager()
            
            with pytest.raises(ValueError, match="Unknown model"):
                manager._get_model_config("invalid-model")
    
    def test_get_provider_priority(self):
        """Test getting provider priority order."""
        with patch('src.backend.services.cloud_models.get_settings') as mock_get_settings:
            mock_get_settings.return_value = {}
            
            manager = CloudModelManager()
            priority = manager._get_provider_priority()
            
            assert isinstance(priority, list)
            assert all(isinstance(p, ProviderType) for p in priority)
    
    @pytest.mark.asyncio
    async def test_health_check_all(self):
        """Test health check for all providers."""
        with patch('src.backend.services.cloud_models.get_settings') as mock_get_settings:
            mock_get_settings.return_value = {}
            
            manager = CloudModelManager()
            
            # Mock providers
            mock_provider = AsyncMock()
            mock_provider.health_check.return_value = True
            manager.providers = {
                ProviderType.OPENAI: mock_provider,
                ProviderType.ANTHROPIC: mock_provider
            }
            
            results = await manager.health_check_all()
            
            assert isinstance(results, dict)
            assert "openai" in results
            assert "anthropic" in results
            assert results["openai"] is True
            assert results["anthropic"] is True


class TestCloudModelManagerIntegration:
    """Integration tests for cloud model manager."""
    
    @pytest.mark.asyncio
    async def test_chat_completion_with_fallback(self):
        """Test chat completion with provider fallback."""
        with patch('src.backend.services.cloud_models.get_settings') as mock_get_settings:
            mock_get_settings.return_value = {}
            
            manager = CloudModelManager()
            
            # Mock providers with first one failing
            mock_provider1 = AsyncMock()
            mock_provider1.chat_completion.side_effect = Exception("Provider 1 failed")
            
            mock_provider2 = AsyncMock()
            mock_response = {
                "content": "Success response",
                "usage": {"total_tokens": 100},
                "model": "test-model",
                "finish_reason": "stop"
            }
            mock_provider2.chat_completion.return_value = mock_response
            
            manager.providers = {
                ProviderType.OPENAI: mock_provider1,
                ProviderType.ANTHROPIC: mock_provider2
            }
            
            # Mock model config
            manager.models = {
                "test-model": ModelConfig(
                    name="test-model",
                    provider=ProviderType.ANTHROPIC,
                    model_type=ModelType.CHAT
                )
            }
            
            messages = [{"role": "user", "content": "Hello"}]
            result = await manager.chat_completion(messages, "test-model")
            
            assert result["content"] == "Success response"
            assert result["model"] == "test-model"
    
    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        """Test when all providers fail."""
        with patch('src.backend.services.cloud_models.get_settings') as mock_get_settings:
            mock_get_settings.return_value = {}
            
            manager = CloudModelManager()
            
            # Mock providers all failing
            mock_provider = AsyncMock()
            mock_provider.chat_completion.side_effect = Exception("Provider failed")
            
            manager.providers = {
                ProviderType.OPENAI: mock_provider,
                ProviderType.ANTHROPIC: mock_provider
            }
            
            # Mock model config
            manager.models = {
                "test-model": ModelConfig(
                    name="test-model",
                    provider=ProviderType.OPENAI,
                    model_type=ModelType.CHAT
                )
            }
            
            messages = [{"role": "user", "content": "Hello"}]
            
            with pytest.raises(Exception, match="All providers failed"):
                await manager.chat_completion(messages, "test-model")
    
    def test_cost_calculation(self):
        """Test cost calculation."""
        with patch('src.backend.services.cloud_models.get_settings') as mock_get_settings:
            mock_get_settings.return_value = {}
            
            manager = CloudModelManager()
            
            # Mock model with known cost
            manager.models = {
                "test-model": ModelConfig(
                    name="test-model",
                    provider=ProviderType.OPENAI,
                    model_type=ModelType.CHAT,
                    cost_per_1k_tokens=0.01
                )
            }
            
            usage = {"total_tokens": 1000}
            metrics = manager._calculate_metrics(
                ProviderType.OPENAI,
                "test-model",
                usage,
                1000.0,  # 1 second latency
                1.0  # cost multiplier
            )
            
            assert metrics.tokens_used == 1000
            assert metrics.cost == 0.01  # 1000 tokens * $0.01/1000 tokens
            assert metrics.latency_ms == 1000.0
            assert metrics.provider_used == "openai"
            assert metrics.model_used == "test-model"
    
    def test_request_history_storage(self):
        """Test request history storage."""
        with patch('src.backend.services.cloud_models.get_settings') as mock_get_settings:
            mock_get_settings.return_value = {}
            
            manager = CloudModelManager()
            
            # Clear history
            manager.request_history = []
            
            metrics = ResponseMetrics(
                provider_used="test-provider",
                model_used="test-model",
                tokens_used=100,
                cost=0.001,
                latency_ms=500.0
            )
            
            manager._store_request_history(
                "chat_completion",
                "test-provider",
                "test-model",
                metrics,
                None
            )
            
            assert len(manager.request_history) == 1
            request = manager.request_history[0]
            assert request["request_type"] == "chat_completion"
            assert request["provider"] == "test-provider"
            assert request["model"] == "test-model"
            assert request["metrics"] == metrics
    
    def test_request_history_limit(self):
        """Test request history limit enforcement."""
        with patch('src.backend.services.cloud_models.get_settings') as mock_get_settings:
            mock_get_settings.return_value = {}
            
            manager = CloudModelManager()
            
            # Fill history beyond limit
            manager.request_history = [{"test": i} for i in range(1100)]
            
            metrics = ResponseMetrics(
                provider_used="test-provider",
                model_used="test-model",
                tokens_used=100,
                cost=0.001,
                latency_ms=500.0
            )
            
            manager._store_request_history(
                "chat_completion",
                "test-provider",
                "test-model",
                metrics,
                None
            )
            
            # Should keep only last 1000 requests
            assert len(manager.request_history) == 1000


if __name__ == "__main__":
    pytest.main([__file__]) 