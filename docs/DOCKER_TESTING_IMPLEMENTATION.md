# Docker Testing Implementation

## Overview

The Docker Testing Implementation provides a comprehensive, containerized testing environment for AI-generated code fixes. This system ensures that all fixes are validated in isolated, reproducible environments before being applied to the actual codebase.

## Architecture

### Core Components

1. **DockerUtils** (`src/backend/services/docker_utils.py`)
   - Enhanced Docker utilities for testing
   - Container monitoring and health checks
   - Real-time log streaming
   - Comprehensive result analysis

2. **FeedbackLoopSystem** (`src/backend/services/feedback_loop.py`)
   - Docker-based testing orchestration
   - Test result collection and analysis
   - Feedback generation for learning
   - Statistics and reporting

3. **ContainerTestResult** & **DockerTestConfig**
   - Structured test result data
   - Configurable test parameters
   - Comprehensive error tracking

### Testing Flow

```
AI Generated Fix
    ↓
DockerUtils.build_image_for_testing()
    ↓
DockerUtils.run_container_with_monitoring()
    ↓
Real-time Log Streaming
    ↓
ContainerTestResult Analysis
    ↓
FeedbackLoopSystem.test_fix_in_docker()
    ↓
TestResult + Feedback Generation
    ↓
Learning Mechanism Integration
```

## Features

### 1. Enhanced DockerUtils

#### ContainerTestResult
```python
@dataclass
class ContainerTestResult:
    success: bool
    container_id: Optional[str] = None
    logs: str = ""
    exit_code: Optional[int] = None
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    health_status: Optional[str] = None
    test_output: Optional[str] = None
```

#### DockerTestConfig
```python
@dataclass
class DockerTestConfig:
    image_tag: str = "ai-fix-test"
    container_name: str = "ai-fix-container"
    timeout_seconds: int = 300
    health_check_interval: int = 5
    max_health_checks: int = 60
    cleanup_on_failure: bool = True
    preserve_logs: bool = True
    test_command: Optional[str] = None
    environment_vars: Optional[Dict[str, str]] = None
    volumes: Optional[Dict[str, str]] = None
    ports: Optional[Dict[str, str]] = None
```

#### Key Methods

```python
# Build image specifically for testing
DockerUtils.build_image_for_testing(
    context_dir: str,
    dockerfile_path: Optional[str] = None,
    build_args: Optional[Dict[str, str]] = None,
    tag: str = "ai-fix-test",
    timeout: int = 600
) -> Tuple[bool, str]

# Run container with comprehensive monitoring
DockerUtils.run_container_with_monitoring(
    config: DockerTestConfig,
    log_callback: Optional[Callable[[str], None]] = None
) -> ContainerTestResult

# Run comprehensive test (build + run + analyze)
DockerUtils.run_comprehensive_test(
    context_dir: str,
    test_config: DockerTestConfig,
    log_callback: Optional[Callable[[str], None]] = None
) -> ContainerTestResult

# Analyze test results
DockerUtils.analyze_test_results(result: ContainerTestResult) -> Dict[str, Any]
```

### 2. Enhanced FeedbackLoopSystem

#### TestResult with Container Integration
```python
@dataclass
class TestResult:
    test_id: str
    file_path: str
    original_code: str
    modified_code: str
    test_output: str
    test_error: Optional[str]
    success: bool
    execution_time: float
    memory_usage: Optional[float]
    timestamp: datetime
    test_type: str
    container_result: Optional[ContainerTestResult] = None
```

#### Key Methods

```python
# Test individual fix in Docker
async def test_fix_in_docker(
    self,
    file_path: str,
    original_code: str,
    modified_code: str,
    language: str = "python",
    test_types: Optional[List[str]] = None,
    log_callback: Optional[Callable[[str], None]] = None
) -> TestResult

# Test entire workspace in Docker
async def test_workspace_in_docker(
    self,
    workspace_path: str,
    language: str = "python",
    test_types: Optional[List[str]] = None,
    log_callback: Optional[Callable[[str], None]] = None
) -> ContainerTestResult
```

### 3. Test Environment Creation

The system automatically creates appropriate test environments:

#### Python Environment
- `requirements.txt` with testing dependencies
- `test_main.py` for unit testing
- Environment variables for testing

#### JavaScript Environment
- `package.json` with testing scripts
- ESLint configuration
- Node.js testing setup

### 4. Real-time Log Streaming

```python
def log_callback(message: str):
    """Real-time log streaming callback."""
    logger.info(f"Container log: {message.strip()}")
    # Update UI progress, store logs, etc.

# Use in testing
container_result = DockerUtils.run_container_with_monitoring(
    test_config, log_callback
)
```

### 5. Comprehensive Error Analysis

The system analyzes container logs for various error types:

- **Syntax Errors**: Code compilation issues
- **Import Errors**: Missing dependencies
- **Permission Errors**: File access issues
- **Timeout Errors**: Performance problems
- **Connection Errors**: Network issues
- **Test Failures**: Assertion failures

## Usage Examples

### 1. Basic Fix Testing

```python
from src.backend.services.feedback_loop import FeedbackLoopSystem

feedback_system = FeedbackLoopSystem()

# Test a fix
test_result = await feedback_system.test_fix_in_docker(
    file_path="main.py",
    original_code="def add(a, b):\n    result = a + b",
    modified_code="def add(a, b):\n    result = a + b\n    return result",
    language="python",
    test_types=["syntax_check", "lint_check"]
)

print(f"Test success: {test_result.success}")
print(f"Test output: {test_result.test_output}")
```

### 2. Workspace Testing

```python
# Test entire workspace
workspace_result = await feedback_system.test_workspace_in_docker(
    workspace_path="/path/to/workspace",
    language="python",
    test_types=["syntax_check", "unit_test"]
)

print(f"Workspace test success: {workspace_result.success}")
```

### 3. Custom Docker Configuration

```python
from src.backend.services.docker_utils import DockerUtils, DockerTestConfig

# Create custom test configuration
test_config = DockerTestConfig(
    image_tag="custom-test-image",
    container_name="custom-test-container",
    timeout_seconds=600,
    test_command="python -m pytest tests/ -v",
    environment_vars={
        "PYTHONPATH": "/workspace",
        "TEST_MODE": "true"
    },
    volumes={
        "/host/data": "/container/data"
    }
)

# Run comprehensive test
result = DockerUtils.run_comprehensive_test(
    context_dir="/path/to/code",
    test_config=test_config
)
```

### 4. Real-time Monitoring

```python
def progress_callback(message: str):
    """Update UI with real-time progress."""
    print(f"Progress: {message}")

# Test with real-time updates
test_result = await feedback_system.test_fix_in_docker(
    file_path="app.py",
    original_code=original_code,
    modified_code=fixed_code,
    language="python",
    test_types=["syntax_check", "unit_test"],
    log_callback=progress_callback
)
```

## Integration with Automate Mode

### RemediationController Integration

```python
# In RemediationController.start_targeted_fix()
test_result = await self.feedback_loop.test_fix_in_docker(
    file_path=file_path,
    original_code=original_code,
    modified_code=fixed_code,
    language=language,
    test_types=["syntax_check", "lint_check"]
)

if test_result.success:
    # Apply the fix
    apply_result = self.refactoring_service.apply_code_changes(...)
else:
    # Handle test failure
    logger.error(f"Fix test failed: {test_result.test_error}")
```

### Progress Tracking

```python
# Set up progress callback
def progress_callback(message: str, percentage: float):
    self._report_progress(f"Testing fix: {message}", percentage)

# Use in testing
test_result = await feedback_system.test_fix_in_docker(
    file_path=file_path,
    original_code=original_code,
    modified_code=fixed_code,
    language=language,
    test_types=test_types,
    log_callback=lambda msg: progress_callback(msg, 0.0)
)
```

## Error Handling

### Container Failures

```python
# Automatic error detection
if not container_result.success:
    analysis = DockerUtils.analyze_test_results(container_result)
    
    if "syntax_error" in analysis["error_types"]:
        # Handle syntax errors
        logger.error("Syntax error detected in fix")
    elif "import_error" in analysis["error_types"]:
        # Handle import errors
        logger.error("Import error detected in fix")
    else:
        # Handle other errors
        logger.error(f"Test failed: {container_result.error_message}")
```

### Timeout Handling

```python
# Configurable timeouts
test_config = DockerTestConfig(
    timeout_seconds=300,  # 5 minutes
    health_check_interval=5,
    max_health_checks=60
)

# Automatic cleanup on timeout
if container_result.error_message and "timeout" in container_result.error_message:
    logger.warning("Test timed out, cleaning up resources")
    # Automatic cleanup is handled by DockerUtils
```

## Performance Optimization

### Parallel Testing

```python
import asyncio

# Test multiple fixes in parallel
async def test_multiple_fixes(fixes: List[Dict]):
    tasks = []
    for fix in fixes:
        task = feedback_system.test_fix_in_docker(
            file_path=fix["file_path"],
            original_code=fix["original_code"],
            modified_code=fix["modified_code"],
            language=fix["language"]
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### Resource Management

```python
# Automatic cleanup
test_config = DockerTestConfig(
    cleanup_on_failure=True,
    preserve_logs=False  # Don't keep logs for performance
)

# Manual cleanup
await feedback_system.cleanup_docker_containers()
```

## Testing

### Running the Docker Test Suite

```bash
# Run comprehensive Docker testing test
python test_docker_feedback_loop.py
```

This test:
- Creates test workspaces with intentional issues
- Tests Docker image building
- Tests container monitoring and health checks
- Tests real-time log streaming
- Tests comprehensive result analysis
- Tests FeedbackLoopSystem integration
- Generates detailed reports

### Test Results

The test produces:
- `test_reports/docker_feedback_loop_results.json`: Detailed test results
- `test_reports/docker_feedback_loop_report.txt`: Human-readable report

## Best Practices

### 1. Test Configuration

- **Use appropriate timeouts**: Set timeouts based on test complexity
- **Configure health checks**: Monitor container health during testing
- **Set up proper cleanup**: Ensure containers are cleaned up after testing
- **Use test-specific images**: Create images optimized for testing

### 2. Error Handling

- **Analyze error types**: Use `analyze_test_results()` for detailed error analysis
- **Handle timeouts gracefully**: Implement proper timeout handling
- **Log comprehensively**: Capture all relevant information for debugging
- **Provide user feedback**: Give meaningful error messages to users

### 3. Performance

- **Parallel testing**: Test multiple fixes concurrently when possible
- **Resource cleanup**: Clean up containers and images promptly
- **Optimize test commands**: Use efficient test commands
- **Cache images**: Reuse Docker images when possible

### 4. Security

- **Isolate containers**: Ensure containers are properly isolated
- **Limit permissions**: Use minimal required permissions
- **Scan images**: Regularly scan Docker images for vulnerabilities
- **Monitor resources**: Track container resource usage

## Troubleshooting

### Common Issues

1. **Docker Build Failures**:
   - Check Dockerfile syntax
   - Verify build context
   - Check available disk space
   - Review build arguments

2. **Container Startup Failures**:
   - Check container logs
   - Verify image exists
   - Check port conflicts
   - Review environment variables

3. **Test Timeouts**:
   - Increase timeout values
   - Optimize test commands
   - Check system resources
   - Review test complexity

4. **Log Streaming Issues**:
   - Verify callback function
   - Check container state
   - Review log collection
   - Monitor memory usage

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.getLogger('src.backend.services.docker_utils').setLevel(logging.DEBUG)
logging.getLogger('src.backend.services.feedback_loop').setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features

1. **Multi-language Support**: Enhanced support for more programming languages
2. **Custom Test Frameworks**: Support for custom testing frameworks
3. **Performance Profiling**: Detailed performance analysis
4. **Security Scanning**: Integrated security vulnerability scanning
5. **Test Result Caching**: Cache test results for improved performance

### Extension Points

1. **Custom Test Runners**: Plug-in architecture for custom test runners
2. **Alternative Container Runtimes**: Support for other container technologies
3. **Cloud Integration**: Integration with cloud-based testing services
4. **Advanced Analytics**: Machine learning-based test result analysis

## Conclusion

The Docker Testing Implementation provides a robust, scalable foundation for testing AI-generated code fixes. With comprehensive container monitoring, real-time log streaming, and detailed result analysis, it ensures that all fixes are thoroughly validated before being applied to the codebase.

The integration with the Automate Mode provides seamless testing capabilities that enhance the reliability and safety of the autonomous code remediation process. 