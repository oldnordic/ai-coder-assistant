# Cloud Model Integration Guide

## Overview

The Cloud Model Integration feature provides a unified interface for multiple AI providers, including automatic failover, cost tracking, and comprehensive monitoring. This guide covers setup, configuration, and usage of the multi-provider LLM system. Configuration files are now organized in the `config/` directory for better maintainability.

---

## UI Navigation

- **Cloud Models Tab**: Configure and monitor all cloud-based LLM providers ([see UI Inventory](ui_inventory.md))
- **Model Manager Tab**: Manage, install, and update all models (cloud and local)
- **Ollama Manager Tab**: Manage local and remote Ollama instances and models ([see Ollama Guide](ollama_remote_guide.md))
- **Usage Monitoring/Analytics**: Real-time usage, cost, and health dashboards in the UI

---

## Features

- **Multi-Provider Support**: OpenAI, Anthropic, Google AI, Ollama (local/remote), and more
- **Automatic Failover**: Seamless switching between providers
- **Cost Tracking**: Real-time usage monitoring and cost analysis
- **Health Monitoring**: Automated provider health checks
- **Unified API**: Single interface for all LLM operations
- **PyQt6 UI**: Complete management interface (see tabs above)
- **CLI Support**: Command-line provider management
- **Organized Configuration**: All settings stored in `config/llm_studio_config.json`
- **Remote Ollama Support**: Manage multiple local/remote Ollama instances, with authentication and health checks

---

## Quick Start

### 1. Environment Setup

Set your API keys as environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_BASE_URL="https://api.openai.com"  # Optional
export OPENAI_ORGANIZATION="your-org-id"  # Optional

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Google AI
export GOOGLE_API_KEY="your-google-api-key"

# Azure (optional)
export AZURE_API_KEY="your-azure-api-key"
export AZURE_ENDPOINT="your-azure-endpoint"

# AWS Bedrock (optional)
export AWS_ACCESS_KEY="your-aws-access-key"
export AWS_SECRET_KEY="your-aws-secret-key"
export AWS_REGION="us-east-1"

# Cohere (optional)
export COHERE_API_KEY="your-cohere-api-key"
```

### 2. Configuration File Setup

The application automatically creates and manages the configuration file at `config/llm_studio_config.json`:

```bash
# View current configuration
cat config/llm_studio_config.json

# Edit configuration manually (optional)
vim config/llm_studio_config.json
```

### 3. Using the PyQt6 UI

- **Cloud Models Tab**: Add/edit/remove cloud providers, set priorities, test connections, monitor usage/cost/health
- **Model Manager Tab**: Install, update, and configure models
- **Ollama Manager Tab**: Add/remove/manage local and remote Ollama instances, pull models, check health, set priorities
- **Analytics/Monitoring**: View real-time usage, cost, and health dashboards

### 4. Using the CLI

```bash
# Check status
python -m src.cli.main llm-studio status

# Add a provider
python -m src.cli.main llm-studio add-provider --provider openai --api-key "your-key"

# List providers
python -m src.cli.main llm-studio list-providers

# Test provider
python -m src.cli.main llm-studio test-provider --provider openai
```

---

## Ollama & Remote Model Management

The system supports both local and remote Ollama instances for running LLMs on your own hardware or on remote servers.

- **Add Ollama Instance**: In the Ollama Manager tab, add a new instance by specifying the URL, authentication (if needed), and priority.
- **Model Discovery**: Automatically lists all models available on each Ollama instance.
- **Health Checks**: Monitors the status of each instance and model.
- **Remote Management**: Supports secure connections, bearer tokens, and SSL configuration for remote Ollama.
- **Priority/Failover**: Ollama instances participate in the same priority/failover system as cloud providers.
- **Model Usage**: Use local models for privacy/cost, cloud for scale/availability.

For more, see the [Ollama Remote Guide](ollama_remote_guide.md).

---

## Configuration File Structure

The `config/llm_studio_config.json` file contains all provider configurations:

```json
{
  "providers": {
    "openai": {
      "provider_type": "openai",
      "api_key": "your-api-key",
      "base_url": "https://api.openai.com",
      "organization": "your-org-id",
      "priority": 1,
      "timeout": 30,
      "enabled": true
    },
    "anthropic": {
      "provider_type": "anthropic", 
      "api_key": "your-api-key",
      "priority": 2,
      "timeout": 30,
      "enabled": true
    },
    "google": {
      "provider_type": "google",
      "api_key": "your-api-key", 
      "priority": 3,
      "timeout": 30,
      "enabled": true
    }
  },
  "default_model": "gpt-4",
  "cost_tracking": {
    "enabled": true,
    "currency": "USD"
  },
  "health_check": {
    "enabled": true,
    "interval": 300
  }
}
```

---

## Provider Configuration

### OpenAI

**Models Available**:
- `gpt-4`: Most capable model (8192 tokens, $0.03/1K tokens)
- `gpt-4-turbo`: Fast and efficient (4096 tokens, $0.01/1K tokens)
- `gpt-3.5-turbo`: Cost-effective (4096 tokens, $0.002/1K tokens)

**Configuration**:
```python
from src.backend.services.cloud_models import ProviderConfig, ProviderType

config = ProviderConfig(
    provider_type=ProviderType.OPENAI,
    api_key="your-api-key",
    base_url="https://api.openai.com",  # Optional
    organization="your-org-id",  # Optional
    priority=1,  # Higher priority = tried first
    timeout=30
)
```

### Anthropic

**Models Available**:
- `claude-3-opus`: Most capable (4096 tokens, $0.015/1K tokens)
- `claude-3-sonnet`: Balanced (4096 tokens, $0.003/1K tokens)
- `claude-3-haiku`: Fast and cheap (4096 tokens, $0.00025/1K tokens)

**Configuration**:
```python
config = ProviderConfig(
    provider_type=ProviderType.ANTHROPIC,
    api_key="your-api-key",
    priority=2,
    timeout=30
)
```

### Google AI

**Models Available**:
- `gemini-pro`: General purpose (8192 tokens, $0.0005/1K tokens)
- `gemini-pro-vision`: Vision capable (8192 tokens, $0.0005/1K tokens)

**Configuration**:
```python
config = ProviderConfig(
    provider_type=ProviderType.GOOGLE,
    api_key="your-api-key",
    priority=3,
    timeout=30
)
```

---

## API Usage

### Basic Chat Completion

```python
from src.backend.services.cloud_models import cloud_model_manager

# Simple chat completion
messages = [
    {"role": "user", "content": "Hello, how are you?"}
]

response = await cloud_model_manager.chat_completion(
    messages=messages,
    model="gpt-4",  # Optional - will use best available
    temperature=0.7,
    max_tokens=1000
)

print(response["content"])
print(f"Cost: ${response['metrics'].cost:.4f}")
print(f"Provider used: {response['metrics'].provider_used}")
```

### Text Completion

```python
# Text completion
response = await cloud_model_manager.text_completion(
    prompt="Write a Python function to sort a list",
    model="gpt-3.5-turbo",
    temperature=0.5,
    max_tokens=500
)

print(response["content"])
```

### Embeddings

```python
# Generate embeddings
texts = ["Hello world", "AI is amazing", "Python programming"]
embeddings = await cloud_model_manager.embeddings(
    texts=texts,
    model="text-embedding-ada-002"
)

print(f"Generated {len(embeddings)} embeddings")
```

### With Request Context

```python
from src.backend.services.cloud_models import RequestContext

context = RequestContext(
    user_id="user123",
    session_id="session456",
    request_id="req789",
    metadata={"source": "web_interface"}
)

response = await cloud_model_manager.chat_completion(
    messages=messages,
    context=context
)
```

---

## Cost Management

### Monitoring Usage

```python
# Get usage statistics
stats = cloud_model_manager.get_usage_stats()

print(f"Total requests: {stats['total_requests']}")
print(f"Total cost: ${stats['total_cost']:.4f}")
print(f"Total tokens: {stats['total_tokens']}")

# Provider breakdown
for provider, count in stats['providers_used'].items():
    print(f"{provider}: {count} requests")

# Model breakdown
for model, count in stats['models_used'].items():
    print(f"{model}: {count} requests")
```

### Cost Optimization

1. **Set Provider Priorities**: Put cheaper providers first
2. **Use Appropriate Models**: Choose cost-effective models for simple tasks
3. **Monitor Usage**: Track costs in real-time
4. **Set Limits**: Implement usage limits in your application

```python
# Example: Cost-optimized configuration
configs = [
    ProviderConfig(provider_type=ProviderType.GOOGLE, priority=1),  # Cheapest
    ProviderConfig(provider_type=ProviderType.ANTHROPIC, priority=2),  # Medium
    ProviderConfig(provider_type=ProviderType.OPENAI, priority=3),  # Most expensive
]
```

---

## Health Monitoring

### Check Provider Health

```python
# Check all providers
health_status = await cloud_model_manager.health_check_all()

for provider, is_healthy in health_status.items():
    status = "✅ Healthy" if is_healthy else "❌ Unhealthy"
    print(f"{provider}: {status}")
```

### Automatic Failover

The system automatically handles failover:

1. **Primary Provider**: Tries the highest priority provider first
2. **Fallback**: If primary fails, tries next provider
3. **Error Handling**: Graceful degradation with detailed error reporting
4. **Metrics**: Tracks which provider was used and why

---

## Advanced Configuration

### Custom Model Configuration

```python
from src.backend.services.cloud_models import ModelConfig, ModelType

# Add custom model
custom_model = ModelConfig(
    name="my-custom-model",
    provider=ProviderType.OPENAI,
    model_type=ModelType.CHAT,
    max_tokens=8192,
    temperature=0.7,
    cost_per_1k_tokens=0.02,
    context_window=16384,
    supports_streaming=True,
    supports_vision=False
)

# Register with manager
cloud_model_manager.models["my-custom-model"] = custom_model
```

### Provider-Specific Settings

```python
# OpenAI with custom settings
openai_config = ProviderConfig(
    provider_type=ProviderType.OPENAI,
    api_key="your-key",
    base_url="https://api.openai.com/v1",
    organization="your-org",
    timeout=60,
    max_retries=5,
    priority=1,
    cost_multiplier=1.0
)
```

---

## Troubleshooting

### Common Issues

1. **Provider Not Available**
   ```
   Error: All providers failed
   ```
   **Solution**: Check API keys and network connectivity

2. **Rate Limiting**
   ```
   Error: Rate limit exceeded
   ```
   **Solution**: Implement retry logic or use different provider

3. **Invalid API Key**
   ```
   Error: Invalid API key
   ```
   **Solution**: Verify API key is correct and has proper permissions

4. **Model Not Found**
   ```
   Error: Unknown model: invalid-model
   ```
   **Solution**: Check available models with `get_available_models()`

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Providers

```python
# Test specific provider
async def test_provider(provider_type):
    try:
        response = await cloud_model_manager.chat_completion(
            messages=[{"role": "user", "content": "Test"}],
            model="gpt-3.5-turbo"
        )
        print(f"✅ {provider_type} working")
        return True
    except Exception as e:
        print(f"❌ {provider_type} failed: {e}")
        return False
```

---

## Best Practices

### 1. **Provider Selection**
- Use cost-effective providers for simple tasks
- Reserve expensive providers for complex operations
- Implement provider-specific logic when needed

### 2. **Error Handling**
- Always handle provider failures gracefully
- Implement retry logic for transient errors
- Log detailed error information for debugging

### 3. **Cost Management**
- Monitor usage in real-time
- Set up alerts for cost thresholds
- Use appropriate models for each task

### 4. **Performance**
- Use async/await for all operations
- Implement connection pooling
- Cache responses when appropriate

### 5. **Security**
- Store API keys securely
- Use environment variables
- Implement proper access controls

---

## Integration Examples

### Web Application

```python
from fastapi import FastAPI
from src.backend.services.cloud_models import cloud_model_manager

app = FastAPI()

@app.post("/chat")
async def chat_endpoint(request: dict):
    try:
        response = await cloud_model_manager.chat_completion(
            messages=request["messages"],
            model=request.get("model"),
            context=RequestContext(user_id=request.get("user_id"))
        )
        return {
            "content": response["content"],
            "cost": response["metrics"].cost,
            "provider": response["metrics"].provider_used
        }
    except Exception as e:
        return {"error": str(e)}
```

### Background Task

```python
import asyncio
from src.backend.services.cloud_models import cloud_model_manager

async def process_documents(documents):
    results = []
    for doc in documents:
        response = await cloud_model_manager.chat_completion(
            messages=[{"role": "user", "content": f"Analyze: {doc}"}],
            model="gpt-4"
        )
        results.append({
            "document": doc,
            "analysis": response["content"],
            "cost": response["metrics"].cost
        })
    return results
```

---

## Monitoring and Analytics

### Usage Dashboard

The PyQt6 UI provides real-time monitoring:

- **Provider Usage**: Requests per provider
- **Cost Tracking**: Real-time cost analysis
- **Model Performance**: Response times and success rates
- **Health Status**: Provider availability

### Custom Analytics

```python
# Custom analytics
def analyze_usage_patterns():
    stats = cloud_model_manager.get_usage_stats()
    
    # Cost per provider
    for provider, count in stats['providers_used'].items():
        cost_per_request = stats['total_cost'] / stats['total_requests']
        print(f"{provider}: ${cost_per_request:.4f} per request")
    
    # Popular models
    for model, count in stats['models_used'].items():
        print(f"{model}: {count} requests")
```

---

## Related Documentation

- [User Manual: Cloud Models](user_manual.md#cloud-models-tab)
- [Ollama Remote Guide](ollama_remote_guide.md)
- [UI Inventory](ui_inventory.md)
- [Architecture](ARCHITECTURE.md)
- [Provider System Guide](provider_system_guide.md)
- [Test Suite Guide](test_suite_guide.md)

---

_Last updated: June 2025_ 