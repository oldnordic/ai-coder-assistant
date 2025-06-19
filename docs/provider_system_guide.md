# Provider System Guide (Updated v2.6.0)

## Overview
The unified provider system supports multiple LLM providers (OpenAI, Anthropic, Google, Ollama) with automatic failover, cost tracking, and health monitoring.

## Features
- Add/manage multiple providers
- Automatic failover and retry
- Cost tracking and optimization
- Health monitoring for all providers
- Unified API for all operations

## Usage
1. Open the **Cloud Models** tab.
2. Add providers and configure API keys.
3. Monitor provider health and usage.
4. Use cost tracking to optimize usage.

## Configuration
- Providers are managed in the UI or in `llm_studio_config.json`.
- Supports custom endpoints and advanced settings.

## Integration
- All features are accessible via the BackendController and REST API.
- For automation, use the API endpoints for provider management and health checks.

## Architecture

### Core Components

1. **BaseProvider** (`src/backend/services/providers.py`)
   - Abstract base class defining the provider interface
   - Common functionality for all providers
   - Standardized error handling and response formatting

2. **Provider Implementations**
   - **OpenAIProvider**: OpenAI GPT models (GPT-3.5, GPT-4, etc.)
   - **ClaudeProvider**: Anthropic Claude models (Claude-3, Claude-2, etc.)
   - **GoogleGeminiProvider**: Google Gemini models (Gemini Pro, etc.)
   - **OllamaProvider**: Local Ollama models (Llama2, CodeLlama, etc.)

3. **LLMManager** (`src/backend/services/llm_manager.py`)
   - Orchestrates provider selection and failover
   - Manages provider configuration and health monitoring
   - Handles cost tracking and usage analytics

## Setup and Configuration

### Environment Variables

Set up your API keys as environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Google AI
export GOOGLE_API_KEY="your-google-api-key"

# Ollama (optional - for local models)
export OLLAMA_BASE_URL="http://localhost:11434"
```

### Provider Configuration

Create a provider configuration file or use the UI to configure providers:

```python
from backend.services.models import ProviderConfig, ProviderType

# OpenAI Configuration
openai_config = ProviderConfig(
    provider_type=ProviderType.OPENAI,
    api_key="your-openai-api-key",
    base_url="https://api.openai.com/v1",
    models=["gpt-3.5-turbo", "gpt-4"],
    cost_multiplier=1.0,
    priority=1
)

# Claude Configuration
claude_config = ProviderConfig(
    provider_type=ProviderType.ANTHROPIC,
    api_key="your-anthropic-api-key",
    base_url="https://api.anthropic.com",
    models=["claude-3-sonnet-20240229", "claude-3-opus-20240229"],
    cost_multiplier=1.2,
    priority=2
)

# Google Configuration
google_config = ProviderConfig(
    provider_type=ProviderType.GOOGLE,
    api_key="your-google-api-key",
    base_url="https://generativelanguage.googleapis.com",
    models=["gemini-pro", "gemini-pro-vision"],
    cost_multiplier=0.8,
    priority=3
)

# Ollama Configuration (Local)
ollama_config = ProviderConfig(
    provider_type=ProviderType.OLLAMA,
    api_key="",  # Not needed for local Ollama
    base_url="http://localhost:11434",
    models=["llama2", "codellama", "mistral"],
    cost_multiplier=0.1,  # Very low cost for local models
    priority=4
)
```

## Usage

### Basic Usage

```python
from backend.services.llm_manager import LLMManager
from backend.services.models import ChatCompletionRequest, ChatMessage

# Initialize the manager
manager = LLMManager()

# Create a chat completion request
request = ChatCompletionRequest(
    messages=[
        ChatMessage(role="user", content="Hello, how are you?")
    ],
    model="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=100
)

# Get completion from any available provider
response = await manager.chat_completion(request)
print(response.content)
```

### Provider-Specific Usage

```python
from backend.services.providers import OpenAIProvider, ClaudeProvider

# Use specific provider
openai_provider = OpenAIProvider(openai_config)
response = await openai_provider.chat_completion(request)

# Use Claude provider
claude_provider = ClaudeProvider(claude_config)
response = await claude_provider.chat_completion(request)
```

### Automatic Failover

The LLMManager automatically handles failover between providers:

```python
# The manager will try providers in priority order
# If one fails, it automatically tries the next
response = await manager.chat_completion(request)
```

## UI Integration

### Cloud Models Tab

The main application includes a "Cloud Models" tab that provides:

1. **Provider Management**
   - Add, edit, and remove providers
   - Configure API keys and settings
   - Set provider priorities and cost multipliers

2. **Model Testing**
   - Test provider connectivity
   - Verify API key validity
   - Check model availability

3. **Usage Monitoring**
   - Real-time cost tracking
   - Usage statistics and analytics
   - Provider health monitoring

4. **Configuration**
   - Environment variable setup
   - Provider priority management
   - Cost optimization settings

### Accessing the UI

1. Launch the AI Coder Assistant
2. Navigate to the "Cloud Models" tab
3. Configure your providers using the interface
4. Test connectivity and monitor usage

## Advanced Features

### Cost Tracking

The system automatically tracks costs across all providers:

```python
# Get cost information
costs = manager.get_cost_analysis()
print(f"Total cost: ${costs.total_cost}")
print(f"Cost by provider: {costs.provider_costs}")
```

### Health Monitoring

Monitor provider health and availability:

```python
# Check provider health
health = await manager.check_provider_health()
for provider, status in health.items():
    print(f"{provider}: {'Healthy' if status else 'Unhealthy'}")
```

### Model Listing

List available models for each provider:

```python
# Get available models
models = await manager.list_models()
for provider, model_list in models.items():
    print(f"{provider}: {model_list}")
```

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Verify API keys are correctly set in environment variables
   - Check API key permissions and quotas
   - Ensure proper formatting (no extra spaces or characters)

2. **Connection Issues**
   - Verify internet connectivity
   - Check firewall settings
   - Ensure provider services are available

3. **Model Not Found**
   - Verify model names are correct
   - Check if models are available in your region
   - Ensure you have access to the requested models

4. **Rate Limiting**
   - Implement exponential backoff
   - Use multiple providers for high-volume usage
   - Monitor usage and adjust accordingly

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Provider operations will now show detailed logs
response = await manager.chat_completion(request)
```

### Error Handling

The system provides comprehensive error handling:

```python
try:
    response = await manager.chat_completion(request)
except ProviderError as e:
    print(f"Provider error: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
```

## Best Practices

### Provider Selection

1. **Cost Optimization**
   - Use local Ollama models for development and testing
   - Use cost-effective providers for routine tasks
   - Reserve expensive providers for critical operations

2. **Reliability**
   - Configure multiple providers for redundancy
   - Set appropriate priorities based on reliability
   - Monitor provider health regularly

3. **Performance**
   - Choose providers based on response time requirements
   - Use appropriate models for different tasks
   - Implement caching for repeated requests

### Security

1. **API Key Management**
   - Store API keys securely (environment variables)
   - Rotate keys regularly
   - Use least-privilege access

2. **Data Privacy**
   - Be aware of data sent to external providers
   - Use local models for sensitive data
   - Review provider privacy policies

### Monitoring

1. **Usage Tracking**
   - Monitor costs regularly
   - Track usage patterns
   - Set up alerts for unusual activity

2. **Performance Monitoring**
   - Track response times
   - Monitor error rates
   - Analyze provider performance

## Migration from Old System

If you were using the old `cloud_models.py` system:

1. **Update Imports**
   ```python
   # Old
   from backend.services.cloud_models import OpenAIProvider
   
   # New
   from backend.services.providers import OpenAIProvider
   ```

2. **Update Configuration**
   - Use the new `ProviderConfig` model
   - Configure providers through the UI or programmatically
   - Update any custom provider implementations

3. **Test Functionality**
   - Verify all providers work correctly
   - Test failover functionality
   - Check cost tracking and monitoring

## Support

For additional support:

1. Check the test suite in `src/tests/test_cloud_models.py` for usage examples
2. Review the provider implementations in `src/backend/services/providers.py`
3. Examine the LLM manager in `src/backend/services/llm_manager.py`
4. Use the UI for configuration and testing

The unified provider system provides a robust, scalable foundation for LLM integration with comprehensive features for cost management, reliability, and ease of use. 