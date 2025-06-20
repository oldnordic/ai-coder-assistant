"""
Test Ollama Provider with Remote Configurations

Tests the enhanced OllamaProvider with support for remote instances,
authentication, and custom endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.services.providers import OllamaProvider
from backend.services.models import ProviderConfig, ProviderType, ChatMessage, ChatCompletionRequest
from src.backend.utils.constants import TEST_PORT


class TestOllamaRemoteConfigurations:
    """Test Ollama provider with remote configurations."""
    
    def test_ollama_remote_configuration(self):
        """Test Ollama provider with remote configuration."""
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            api_key="remote-api-key",
            base_url="https://remote-ollama.example.com",
            timeout=60,
            priority=1,
            is_enabled=True,
            instance_name="Remote Ollama Server",
            auth_token="bearer-token-123",
            verify_ssl=False,
            custom_endpoints={
                "chat": "/api/v1/chat",
                "list_models": "/api/v1/models",
                "health": "/api/v1/health"
            },
            metadata={
                "verify_ssl": False,
                "custom_endpoints": {
                    "chat": "/api/v1/chat",
                    "list_models": "/api/v1/models",
                    "health": "/api/v1/health"
                },
                "headers": {
                    "X-Custom-Header": "custom-value"
                }
            }
        )
        
        provider = OllamaProvider(config)
        
        # Verify configuration
        assert provider.base_url == "https://remote-ollama.example.com"
        assert provider.verify_ssl is False
        assert provider.custom_endpoints["chat"] == "/api/v1/chat"
        assert provider.custom_endpoints["list_models"] == "/api/v1/models"
        assert provider.custom_endpoints["health"] == "/api/v1/health"
    
    def test_ollama_local_configuration(self):
        """Test Ollama provider with local configuration."""
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            api_key="dummy_key",
            base_url=f"http://localhost:{TEST_PORT}",
            timeout=30,
            priority=5,
            is_enabled=True,
            instance_name="Local Ollama",
            verify_ssl=True
        )
        
        provider = OllamaProvider(config)
        
        # Verify configuration
        assert provider.base_url == f"http://localhost:{TEST_PORT}"
        assert provider.verify_ssl is True
        assert provider.custom_endpoints == {}
    
    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_ollama_remote_chat_completion(self, mock_post):
        """Test Ollama chat completion with remote configuration."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "llama2",
            "message": {"content": "Hello from remote Ollama!"},
            "done": True
        }
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response
        
        # Create provider with remote config
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            api_key="remote-key",
            base_url="https://remote-ollama.example.com",
            instance_name="Remote Server",
            custom_endpoints={"chat": "/api/v1/chat"}
        )
        
        provider = OllamaProvider(config)
        
        # Test chat completion
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            model="llama2"
        )
        
        response = await provider.chat_completion(request)
        
        # Verify response
        assert response.content == "Hello from remote Ollama!"
        assert response.model == "llama2"
        assert response.provider == ProviderType.OLLAMA
        
        # Verify custom endpoint was used
        mock_post.assert_called_once_with("/api/v1/chat", json={
            "model": "llama2",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False
        })
    
    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_ollama_remote_list_models(self, mock_get):
        """Test Ollama list models with remote configuration."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2", "size": 4096},
                {"name": "codellama", "size": 8192}
            ]
        }
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response
        
        # Create provider with remote config
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            api_key="remote-key",
            base_url="https://remote-ollama.example.com",
            instance_name="Remote Server",
            custom_endpoints={"list_models": "/api/v1/models"}
        )
        
        provider = OllamaProvider(config)
        
        # Test list models
        models = await provider.list_models()
        
        # Verify response
        assert len(models) == 2
        assert models[0].name == "llama2"
        assert models[1].name == "codellama"
        
        # Verify custom endpoint was used
        mock_get.assert_called_once_with("/api/v1/models")
    
    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_ollama_health_check(self, mock_get):
        """Test Ollama health check."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response
        
        # Create provider
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            api_key="dummy_key",
            base_url=f"http://localhost:{TEST_PORT}",
            instance_name="Test Instance"
        )
        
        provider = OllamaProvider(config)
        
        # Test health check
        is_healthy = await provider.health_check()
        
        # Verify response
        assert is_healthy is True
        mock_get.assert_called_once_with("/api/tags")
    
    @patch('httpx.AsyncClient.get')
    @pytest.mark.asyncio
    async def test_ollama_health_check_custom_endpoint(self, mock_get):
        """Test Ollama health check with custom endpoint."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response
        
        # Create provider with custom health endpoint
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            api_key="remote-key",
            base_url="https://remote-ollama.example.com",
            instance_name="Remote Server",
            custom_endpoints={"health": "/api/v1/health"}
        )
        
        provider = OllamaProvider(config)
        
        # Test health check
        is_healthy = await provider.health_check()
        
        # Verify response
        assert is_healthy is True
        mock_get.assert_called_once_with("/api/v1/health")
    
    def test_ollama_authentication_headers(self):
        """Test Ollama provider sets authentication headers correctly."""
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            api_key="bearer-token-123",
            base_url="https://remote-ollama.example.com",
            instance_name="Authenticated Server",
            metadata={
                "headers": {
                    "X-Custom-Header": "custom-value",
                    "Authorization": "Bearer custom-token"
                }
            }
        )
        
        provider = OllamaProvider(config)
        
        # Verify headers are set correctly
        # Custom Authorization header should override the default one
        assert provider.client.headers["Authorization"] == "Bearer custom-token"
        assert provider.client.headers["X-Custom-Header"] == "custom-value"


class TestOllamaErrorHandling:
    """Test Ollama provider error handling."""
    
    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_ollama_authentication_error(self, mock_post):
        """Test Ollama authentication error handling."""
        # Setup mock to return 401 error
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_post.return_value = mock_response
        
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            api_key="invalid-key",
            base_url="https://remote-ollama.example.com"
        )
        
        provider = OllamaProvider(config)
        
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            model="llama2"
        )
        
        # Test that authentication error is properly handled
        with pytest.raises(Exception, match="Ollama authentication failed"):
            await provider.chat_completion(request)
    
    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_ollama_model_not_found_error(self, mock_post):
        """Test Ollama model not found error handling."""
        # Setup mock to return 404 error
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_post.return_value = mock_response
        
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            api_key="dummy_key",
            base_url=f"http://localhost:{TEST_PORT}"
        )
        
        provider = OllamaProvider(config)
        
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            model="nonexistent-model"
        )
        
        # Test that model not found error is properly handled
        with pytest.raises(Exception, match="Ollama model not found"):
            await provider.chat_completion(request)
    
    @patch('httpx.AsyncClient.post')
    @pytest.mark.asyncio
    async def test_ollama_connection_error(self, mock_post):
        """Test Ollama connection error handling."""
        # Setup mock to raise connection error
        mock_post.side_effect = Exception("Connection failed")
        
        config = ProviderConfig(
            provider_type=ProviderType.OLLAMA,
            api_key="dummy_key",
            base_url=f"http://localhost:{TEST_PORT}"
        )
        
        provider = OllamaProvider(config)
        
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            model="llama2"
        )
        
        # Test that connection error is properly handled
        with pytest.raises(Exception, match="Ollama connection failed"):
            await provider.chat_completion(request) 