# Ollama Remote Guide (Updated v2.6.0)

## Overview
The Ollama Manager supports multiple local and remote Ollama instances, with authentication, health checks, and model management.

## Features
- Add/remove/manage multiple Ollama instances
- Configure authentication (bearer tokens), custom headers, SSL
- Health check and model listing for each instance
- Test chat with models

## Usage
1. Open the **Ollama Manager** tab.
2. Click **Add Instance** and configure details (name, URL, auth, headers, SSL).
3. Use **Health Check** to test connectivity.
4. Use **Model Listing** to view available models.
5. Use **Test Chat** to test model responses.

## Troubleshooting
- Check URLs, network, and authentication.
- Use health check to verify connectivity.

## Integration
- All features are accessible via the BackendController and REST API.
- For automation, use the API endpoints for instance management and model listing.

## Configuration

### Basic Remote Configuration

```python
from backend.services.models import ProviderConfig, ProviderType

# Remote Ollama server configuration
remote_config = ProviderConfig(
    provider_type=ProviderType.OLLAMA,
    api_key="your-bearer-token",  # Optional for some deployments
    base_url="https://remote-ollama.example.com",
    timeout=60,
    priority=1,
    is_enabled=True,
    instance_name="Production Ollama Server",
    auth_token="bearer-token-123",
    verify_ssl=True,
    custom_endpoints={
        "chat": "/api/v1/chat",
        "list_models": "/api/v1/models",
        "health": "/api/v1/health"
    }
)
```

### Local Configuration (Default)

```python
# Local Ollama configuration
local_config = ProviderConfig(
    provider_type=ProviderType.OLLAMA,
    api_key="dummy_key",  # Not needed for local instances
    base_url="http://localhost:11434",
    timeout=30,
    priority=5,
    is_enabled=True,
    instance_name="Local Ollama",
    verify_ssl=True
)
```

### Advanced Configuration with Custom Headers

```python
# Configuration with custom authentication headers
advanced_config = ProviderConfig(
    provider_type=ProviderType.OLLAMA,
    api_key="primary-token",
    base_url="https://enterprise-ollama.company.com",
    timeout=120,
    priority=1,
    is_enabled=True,
    instance_name="Enterprise Ollama",
    auth_token="enterprise-token",
    verify_ssl=True,
    custom_endpoints={
        "chat": "/api/ollama/chat",
        "list_models": "/api/ollama/models",
        "health": "/api/ollama/health"
    },
    metadata={
        "headers": {
            "X-API-Key": "enterprise-api-key",
            "X-Client-ID": "ai-coder-assistant",
            "Authorization": "Bearer enterprise-token"
        },
        "verify_ssl": True,
        "custom_endpoints": {
            "chat": "/api/ollama/chat",
            "list_models": "/api/ollama/models",
            "health": "/api/ollama/health"
        }
    }
)
```

## UI Configuration

### Adding Remote Instances

1. **Open the Ollama Manager Tab**
   - Launch the AI Coder Assistant
   - Navigate to the "Ollama Manager" tab

2. **Add New Instance**
   - Click "Add Instance" button
   - Fill in the configuration form:
     - **Instance Name**: Descriptive name (e.g., "Production Server")
     - **Base URL**: Remote server URL (e.g., `https://remote-ollama.example.com`)
     - **Auth Token**: Bearer token if required
     - **SSL Verification**: Enable/disable SSL verification
     - **Timeout**: Request timeout in seconds
     - **Priority**: Instance priority (1-10, lower is higher priority)
     - **Enabled**: Enable/disable the instance

3. **Custom Endpoints (Optional)**
   - **Chat Endpoint**: Custom chat completion endpoint
   - **Models Endpoint**: Custom model listing endpoint
   - **Health Endpoint**: Custom health check endpoint

4. **Save Configuration**
   - Click "OK" to save the instance
   - The instance will appear in the instances table

### Managing Instances

#### Instance Table
The instances table shows:
- **Name**: Instance name
- **URL**: Base URL
- **Status**: Enabled/Disabled
- **Priority**: Priority level
- **Actions**: Edit/Delete buttons

#### Health Monitoring
- **Health Tab**: Real-time health status of all instances
- **Status Colors**: Green for healthy, red for unhealthy
- **Last Check**: Timestamp of last health check

#### Model Discovery
- **Models Tab**: Lists all models from all instances
- **Instance Column**: Shows which instance each model belongs to
- **Context Length**: Model context window size
- **Capabilities**: Model capabilities (chat, vision, etc.)

## Usage Examples

### Programmatic Configuration

```python
from backend.services.llm_manager import LLMManager
from backend.services.models import ProviderConfig, ProviderType

# Initialize manager
manager = LLMManager()

# Add remote instance
remote_config = ProviderConfig(
    provider_type=ProviderType.OLLAMA,
    api_key="remote-token",
    base_url="https://remote-ollama.example.com",
    instance_name="Remote Server",
    priority=1
)
manager.add_provider(remote_config)

# Add local instance
local_config = ProviderConfig(
    provider_type=ProviderType.OLLAMA,
    api_key="dummy_key",
    base_url="http://localhost:11434",
    instance_name="Local Server",
    priority=2
)
manager.add_provider(local_config)

# Use any instance for chat completion
from backend.services.models import ChatMessage, ChatCompletionRequest

request = ChatCompletionRequest(
    messages=[ChatMessage(role="user", content="Hello")],
    model="llama2"
)

# Manager will automatically select the best available instance
response = await manager.chat_completion(request)
```

### Direct Provider Usage

```python
from backend.services.providers import OllamaProvider
from backend.services.models import ProviderConfig, ProviderType

# Create remote provider
config = ProviderConfig(
    provider_type=ProviderType.OLLAMA,
    api_key="remote-token",
    base_url="https://remote-ollama.example.com",
    instance_name="Remote Server"
)

provider = OllamaProvider(config)

# List available models
models = await provider.list_models()
for model in models:
    print(f"Model: {model.name}, Context: {model.context_length}")

# Health check
is_healthy = await provider.health_check()
print(f"Instance healthy: {is_healthy}")

# Chat completion
request = ChatCompletionRequest(
    messages=[ChatMessage(role="user", content="Hello")],
    model="llama2"
)

response = await provider.chat_completion(request)
print(f"Response: {response.choices[0]['message']['content']}")
```

## Deployment Scenarios

### 1. Local Development
```python
# Simple local configuration
local_config = ProviderConfig(
    provider_type=ProviderType.OLLAMA,
    api_key="dummy_key",
    base_url="http://localhost:11434",
    instance_name="Local Development"
)
```

### 2. Remote Development Server
```python
# Remote development server
dev_config = ProviderConfig(
    provider_type=ProviderType.OLLAMA,
    api_key="dev-token",
    base_url="https://dev-ollama.company.com",
    instance_name="Development Server",
    priority=2
)
```

### 3. Production Cluster
```python
# Production cluster with load balancing
prod_config = ProviderConfig(
    provider_type=ProviderType.OLLAMA,
    api_key="prod-token",
    base_url="https://prod-ollama.company.com",
    instance_name="Production Cluster",
    priority=1,
    timeout=120,
    custom_endpoints={
        "chat": "/api/v1/chat",
        "list_models": "/api/v1/models",
        "health": "/api/v1/health"
    }
)
```

### 4. Cloud Provider Integration
```python
# Cloud provider with custom authentication
cloud_config = ProviderConfig(
    provider_type=ProviderType.OLLAMA,
    api_key="cloud-api-key",
    base_url="https://api.cloudprovider.com/ollama",
    instance_name="Cloud Ollama",
    priority=1,
    metadata={
        "headers": {
            "X-API-Key": "cloud-api-key",
            "X-Client-ID": "ai-coder-assistant"
        }
    }
)
```

## Error Handling

### Common Error Scenarios

1. **Authentication Errors (401)**
   ```python
   # Error: Ollama authentication failed
   # Solution: Check API key and authentication headers
   ```

2. **Connection Errors**
   ```python
   # Error: Ollama connection failed
   # Solution: Verify network connectivity and server availability
   ```

3. **Model Not Found (404)**
   ```python
   # Error: Ollama model not found
   # Solution: Check model name and availability on the instance
   ```

4. **SSL Certificate Errors**
   ```python
   # Error: SSL verification failed
   # Solution: Set verify_ssl=False for self-signed certificates
   ```

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Provider operations will show detailed logs
response = await provider.chat_completion(request)
```

## Best Practices

### Security
1. **Use HTTPS**: Always use HTTPS for remote connections
2. **Token Management**: Store authentication tokens securely
3. **Network Security**: Use VPN or private networks for sensitive deployments
4. **SSL Verification**: Enable SSL verification in production

### Performance
1. **Instance Priority**: Set appropriate priorities for load balancing
2. **Timeout Configuration**: Adjust timeouts based on network latency
3. **Health Monitoring**: Regular health checks for all instances
4. **Failover Strategy**: Configure multiple instances for redundancy

### Monitoring
1. **Health Checks**: Monitor instance health regularly
2. **Usage Tracking**: Track usage across all instances
3. **Error Logging**: Log and monitor errors for troubleshooting
4. **Performance Metrics**: Monitor response times and throughput

## Troubleshooting

### Connection Issues
1. **Verify Network**: Check network connectivity to remote server
2. **Firewall Rules**: Ensure firewall allows connections to Ollama port
3. **DNS Resolution**: Verify DNS resolution for remote hostname
4. **SSL Certificates**: Check SSL certificate validity

### Authentication Issues
1. **Token Validity**: Verify authentication token is valid and not expired
2. **Header Format**: Ensure authentication headers are correctly formatted
3. **Permissions**: Check if token has required permissions
4. **Rate Limiting**: Monitor for rate limiting issues

### Performance Issues
1. **Network Latency**: Check network latency to remote server
2. **Server Load**: Monitor remote server load and capacity
3. **Timeout Settings**: Adjust timeout values based on network conditions
4. **Load Balancing**: Distribute load across multiple instances

## Migration from Local-Only

If you're migrating from local-only Ollama to include remote instances:

1. **Backup Configuration**: Export current configuration
2. **Add Remote Instances**: Add remote instances through UI or programmatically
3. **Test Connectivity**: Verify all instances are accessible
4. **Update Priorities**: Set appropriate priorities for load balancing
5. **Monitor Health**: Ensure all instances are healthy
6. **Update Documentation**: Update any documentation or scripts

The enhanced Ollama provider provides enterprise-grade capabilities for managing distributed Ollama deployments while maintaining the simplicity of local development. 