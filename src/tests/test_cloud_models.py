"""
Unit tests for Unified LLM Provider System

Tests the consolidated provider system from providers.py and llm_manager.py
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, List, Any

from backend.services.providers import (
    OpenAIProvider, GoogleGeminiProvider, ClaudeProvider, OllamaProvider,
    BaseProvider
)
from backend.services.llm_manager import LLMManager
from backend.services.models import (
    ProviderType, ModelType, ModelConfig, ProviderConfig, 
    ChatMessage, ChatCompletionRequest, ChatCompletionResponse
)


class TestProviderTypes:
    """Test provider type enums."""
    
    def test_provider_types(self):
        """Test provider type enum values."""
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.GOOGLE_GEMINI.value == "google_gemini"
        assert ProviderType.CLAUDE.value == "claude"
        assert ProviderType.OLLAMA.value == "ollama"
    
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
            name="gpt-4",
            provider=ProviderType.OPENAI,
            model_type=ModelType.CHAT,
            context_length=8192,
            cost_per_1k_tokens=0.03,
            capabilities=["chat", "vision"]
        )
        
        assert config.name == "gpt-4"
        assert config.provider == ProviderType.OPENAI
        assert config.model_type == ModelType.CHAT
        assert config.context_length == 8192
        assert config.cost_per_1k_tokens == 0.03
        assert config.capabilities == ["chat", "vision"]


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
            priority=1
        )
        
        assert config.provider_type == ProviderType.OPENAI
        assert config.api_key == "test-key"
        assert config.base_url == "https://api.openai.com"
        assert config.organization == "test-org"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.priority == 1
        assert config.is_enabled is True


class TestRequestResponse:
    """Test request and response models."""
    
    def test_chat_message_creation(self):
        """Test creating chat message."""
        message = ChatMessage(
            role="user",
            content="Hello, how are you?",
            name="test_user"
        )
        
        assert message.role == "user"
        assert message.content == "Hello, how are you?"
        assert message.name == "test_user"
    
    def test_chat_completion_request_creation(self):
        """Test creating chat completion request."""
        messages = [
            ChatMessage(role="user", content="Hello")
        ]
        
        request = ChatCompletionRequest(
            messages=messages,
            model="gpt-4",
            temperature=0.7,
            max_tokens=1000
        )
        
        assert request.model == "gpt-4"
        assert request.temperature == 0.7
        assert request.max_tokens == 1000
        assert len(request.messages) == 1


class TestBaseProvider:
    """Test base provider abstract class."""
    
    def test_base_provider_abstract(self):
        """Test that BaseProvider cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseProvider(MagicMock())


@pytest.fixture
def openai_config():
    return ProviderConfig(
        provider_type=ProviderType.OPENAI,
        api_key="test-key",
        base_url="https://api.openai.com",
        organization="test-org",
        timeout=30,
        max_retries=3,
        priority=1
    )


@pytest.fixture
def google_config():
    return ProviderConfig(
        provider_type=ProviderType.GOOGLE_GEMINI,
        api_key="test-key",
        timeout=30,
        max_retries=3,
        priority=1
    )


@pytest.fixture
def claude_config():
    return ProviderConfig(
        provider_type=ProviderType.CLAUDE,
        api_key="test-key",
        timeout=30,
        max_retries=3,
        priority=1
    )


@pytest.fixture
def ollama_config():
    return ProviderConfig(
        provider_type=ProviderType.OLLAMA,
        api_key="http://localhost:11434",
        timeout=30,
        max_retries=3,
        priority=1
    )


@patch('backend.services.providers.AsyncOpenAI', autospec=True)
class TestOpenAIProvider:
    """Test OpenAI provider implementation."""
    
    def test_openai_provider_initialization(self, mock_openai, openai_config):
        """Test OpenAI provider initialization."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        provider = OpenAIProvider(openai_config)
        
        assert provider.config == openai_config
        assert provider.client == mock_client
        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://api.openai.com",
            organization="test-org",
            timeout=30
        )
    
    @pytest.mark.asyncio
    async def test_openai_chat_completion(self, mock_openai, openai_config):
        """Test OpenAI chat completion."""
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4"
        mock_response.created = 1234567890
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].dict.return_value = {
            "message": {"role": "assistant", "content": "Hello!"},
            "finish_reason": "stop"
        }
        mock_response.usage = MagicMock()
        mock_response.usage.dict.return_value = {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
        mock_response.choices[0].finish_reason = "stop"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        provider = OpenAIProvider(openai_config)
        
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            model="gpt-4"
        )
        
        response = await provider.chat_completion(request)
        
        assert response.id == "chatcmpl-123"
        assert response.model == "gpt-4"
        assert response.provider == ProviderType.OPENAI
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 5
    
    @pytest.mark.asyncio
    async def test_openai_list_models(self, mock_openai, openai_config):
        """Test OpenAI list models."""
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # Mock models response
        mock_model = MagicMock()
        mock_model.id = "gpt-4"
        mock_response = MagicMock()
        mock_response.data = [mock_model]
        
        mock_client.models.list.return_value = mock_response
        
        provider = OpenAIProvider(openai_config)
        models = await provider.list_models()
        
        assert len(models) == 1
        assert models[0].name == "gpt-4"
        assert models[0].provider == ProviderType.OPENAI
    
    def test_openai_cost_calculation(self, mock_openai, openai_config):
        """Test OpenAI cost calculation."""
        provider = OpenAIProvider(openai_config)
        
        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        cost = provider.calculate_cost(usage, "gpt-4")
        
        # gpt-4 pricing: input $0.03/1K, output $0.06/1K
        expected_cost = (1000 / 1000) * 0.03 + (500 / 1000) * 0.06
        assert cost == expected_cost


@patch('backend.services.providers.genai', autospec=True)
class TestGoogleGeminiProvider:
    """Test Google Gemini provider implementation."""
    
    def test_google_provider_initialization(self, mock_genai, google_config):
        """Test Google Gemini provider initialization."""
        provider = GoogleGeminiProvider(google_config)
        assert provider.config == google_config
        mock_genai.configure.assert_called_once_with(api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_google_chat_completion(self, mock_genai, google_config):
        """Test Google Gemini chat completion."""
        # Mock response
        mock_response = MagicMock()
        mock_response.text = "Hello from Gemini!"
        
        # Mock model and chat
        mock_model = MagicMock()
        mock_chat = AsyncMock()
        mock_chat.send_message_async.return_value = mock_response
        mock_model.start_chat.return_value = mock_chat
        mock_genai.GenerativeModel.return_value = mock_model
        
        provider = GoogleGeminiProvider(google_config)
        
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            model="gemini-pro"
        )
        
        response = await provider.chat_completion(request)
        
        assert response.model == "gemini-pro"
        assert response.provider == ProviderType.GOOGLE_GEMINI
        assert "Hello from Gemini!" in response.choices[0]["message"]["content"]
    
    @pytest.mark.asyncio
    async def test_google_list_models(self, mock_genai, google_config):
        """Test Google Gemini list models."""
        provider = GoogleGeminiProvider(google_config)
        models = await provider.list_models()
        
        # Should return predefined Gemini models
        model_names = [model.name for model in models]
        assert "gemini-pro" in model_names
        assert "gemini-pro-vision" in model_names
        assert all(model.provider == ProviderType.GOOGLE_GEMINI for model in models)
    
    def test_google_cost_calculation(self, mock_genai, google_config):
        """Test Google Gemini cost calculation."""
        provider = GoogleGeminiProvider(google_config)
        
        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        cost = provider.calculate_cost(usage, "gemini-pro")
        
        # gemini-pro pricing: $0.0005/1K tokens
        expected_cost = (1500 / 1000) * 0.0005
        assert cost == expected_cost


@patch('backend.services.providers.AsyncAnthropic', autospec=True)
class TestClaudeProvider:
    """Test Claude provider implementation."""
    
    def test_claude_provider_initialization(self, mock_anthropic, claude_config):
        """Test Claude provider initialization."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        provider = ClaudeProvider(claude_config)
        
        assert provider.config == claude_config
        assert provider.client == mock_client
        mock_anthropic.assert_called_once_with(
            api_key="test-key",
            base_url=None
        )
    
    @pytest.mark.asyncio
    async def test_claude_chat_completion(self, mock_anthropic, claude_config):
        """Test Claude chat completion."""
        mock_client = AsyncMock()
        mock_anthropic.return_value = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Hello from Claude!"
        mock_response.model = "claude-3-sonnet-20240229"
        mock_response.stop_reason = "end_turn"
        
        mock_client.messages.create.return_value = mock_response
        
        provider = ClaudeProvider(claude_config)
        
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            model="claude-3-sonnet-20240229"
        )
        
        response = await provider.chat_completion(request)
        
        assert response.model == "claude-3-sonnet-20240229"
        assert response.provider == ProviderType.CLAUDE
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 5


@patch('httpx.AsyncClient.post')
def test_ollama_chat_completion(mock_post, ollama_config):
    """Test Ollama provider chat completion as a standalone function."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "model": "llama2",
        "message": {"content": "Hello from Ollama!"},
        "done": True
    }
    mock_response.raise_for_status = AsyncMock()
    mock_post.return_value = mock_response

    provider = OllamaProvider(ollama_config)

    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="Hello")],
        model="llama2"
    )

    response = asyncio.run(provider.chat_completion(request))

    assert response.model == "llama2"
    assert response.provider == ProviderType.OLLAMA
    assert "Hello from Ollama!" in response.choices[0]["message"]["content"]


@patch('backend.services.llm_manager.LLMManager._load_config')
@patch('backend.services.llm_manager.LLMManager._save_config')
class TestLLMManager:
    """Test LLM Manager."""
    
    def test_llm_manager_initialization(self, mock_save, mock_load):
        """Test LLM manager initialization."""
        mock_load.return_value = MagicMock()
        
        manager = LLMManager()
        
        assert hasattr(manager, 'providers')
        assert hasattr(manager, 'models')
        assert hasattr(manager, 'config')
        mock_load.assert_called_once()
    
    def test_add_provider(self, mock_save, mock_load):
        """Test adding a provider."""
        mock_load.return_value = MagicMock()
        mock_load.return_value.providers = {}
        
        manager = LLMManager()
        
        config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key="test-key"
        )
        
        with patch('backend.services.llm_manager.OpenAIProvider') as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider
            
            manager.add_provider(config)
            
            assert ProviderType.OPENAI in manager.providers
            mock_provider_class.assert_called_once_with(config)
            mock_save.assert_called()
    
    def test_remove_provider(self, mock_save, mock_load):
        """Test removing a provider."""
        mock_load.return_value = MagicMock()
        mock_load.return_value.providers = {ProviderType.OPENAI: MagicMock()}
        
        manager = LLMManager()
        manager.providers = {ProviderType.OPENAI: MagicMock()}
        
        manager.remove_provider(ProviderType.OPENAI)
        
        assert ProviderType.OPENAI not in manager.providers
        mock_save.assert_called()
    
    @pytest.mark.asyncio
    async def test_test_provider(self, mock_save, mock_load):
        """Test provider testing."""
        mock_load.return_value = MagicMock()
        
        manager = LLMManager()
        
        with patch('backend.services.llm_manager.OpenAIProvider') as mock_provider_class:
            mock_provider = AsyncMock()
            mock_provider.health_check.return_value = True
            mock_provider_class.return_value = mock_provider
            
            result = await manager.test_provider(ProviderType.OPENAI, "test-key")
            
            assert result is True
            mock_provider.health_check.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__]) 