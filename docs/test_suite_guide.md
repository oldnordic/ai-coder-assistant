# Test Suite Guide (Updated v3.0.0)

## Overview
The test suite covers all major features, including security intelligence, code standards, PR automation, Ollama management, and performance optimization. The tests are designed to work with the new organized file structure using `config/` and `data/` directories.

## Project Structure for Testing

The test suite works with the organized file structure:

```
ai_coder_assistant/
├── config/                     # Configuration files for testing
│   ├── code_standards_config.json
│   ├── llm_studio_config.json
│   ├── pr_automation_config.json
│   └── security_intelligence_config.json
├── data/                       # Data files for testing
│   ├── security_breaches.json
│   ├── security_patches.json
│   ├── security_training_data.json
│   └── security_vulnerabilities.json
├── src/tests/                  # Test files
│   ├── __init__.py
│   ├── test_cloud_models.py
│   ├── test_ai_tools.py
│   ├── test_refactoring.py
│   ├── test_scanner.py
│   ├── test_continuous_learning.py
│   └── frontend_backend/
└── ...
```

## Features
- Cross-platform compatibility (Linux, macOS, Windows)
- Async/await and background task testing
- Comprehensive mocking of external dependencies
- Timeout mechanisms to prevent hangs
- Debugging and logging support
- Support for organized file structure with config/ and data/ directories

## Usage
1. Set up the test environment as described in the README.
2. Ensure configuration files are in the `config/` directory.
3. Ensure data files are in the `data/` directory.
4. Run tests with `pytest -v`.
5. Review test output and logs for results.

## CI Integration
- Integrate with GitHub Actions, GitLab CI, or other CI systems.
- Use environment variables for API keys and config paths.
- Mock external services for reliable CI runs.
- Ensure CI environment has proper file structure with config/ and data/ directories.

## Troubleshooting
- Ensure all dependencies are installed.
- Verify configuration files are in the `config/` directory.
- Verify data files are in the `data/` directory.
- Use debug logs to diagnose failures.
- Check for network or config issues if tests fail.

## Architecture

### Test Structure

```
src/tests/
├── __init__.py
├── test_cloud_models.py          # Provider system tests
├── test_ai_tools.py              # AI tools functionality tests
├── test_refactoring.py           # Refactoring engine tests
├── test_scanner.py               # Code scanning tests
├── test_continuous_learning.py   # Continuous learning tests
└── frontend_backend/             # Frontend-backend integration tests
    ├── __init__.py
    ├── test_main_window_backend_calls.py
    ├── test_ai_tab_widgets_backend.py
    ├── test_data_tab_widgets_backend.py
    ├── test_markdown_viewer_backend.py
    ├── test_ollama_export_tab_backend.py
    └── test_worker_threads_backend.py
```

### Key Features

- **Modern src-layout**: Tests use absolute imports for reliability
- **Cross-platform compatibility**: Works on Linux, macOS, and Windows
- **Async/await support**: Professional testing of async operations
- **Comprehensive mocking**: Robust mocking of external dependencies
- **Timeout mechanisms**: Prevents test hangs and infinite loops
- **Debug capabilities**: Built-in debugging and logging
- **Organized file structure**: Tests work with config/ and data/ directories

## Setup

### Environment Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set PYTHONPATH**
   
   **Linux/macOS:**
   ```bash
   export PYTHONPATH="$PYTHONPATH:$(pwd)/src"
   ```
   
   **Windows (PowerShell):**
   ```powershell
   $env:PYTHONPATH="$env:PYTHONPATH;$(Get-Location)\src"
   ```
   
   **Windows (CMD):**
   ```cmd
   set PYTHONPATH=%PYTHONPATH%;%CD%\src
   ```

3. **Verify Configuration Files**
   ```bash
   # Ensure configuration files exist
   ls config/
   # Should show: code_standards_config.json, llm_studio_config.json, etc.
   
   # Ensure data files exist
   ls data/
   # Should show: security_breaches.json, security_patches.json, etc.
   ```

4. **Verify Setup**
   ```bash
   python -c "from backend.services.providers import OpenAIProvider; print('Setup successful!')"
   ```

### Test Configuration

The project includes `pytest.ini` for test configuration:

```ini
[tool:pytest]
testpaths = src/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --maxfail=5
```

### Configuration File Management

Tests should handle configuration files in their new locations:

```python
import os
from pathlib import Path

class TestConfiguration:
    """Test configuration file handling."""
    
    def test_config_files_exist(self):
        """Test that configuration files exist in config/ directory."""
        config_dir = Path("config")
        assert config_dir.exists(), "config/ directory should exist"
        
        expected_files = [
            "code_standards_config.json",
            "llm_studio_config.json", 
            "pr_automation_config.json",
            "security_intelligence_config.json"
        ]
        
        for file_name in expected_files:
            file_path = config_dir / file_name
            assert file_path.exists(), f"{file_name} should exist in config/ directory"
    
    def test_data_files_exist(self):
        """Test that data files exist in data/ directory."""
        data_dir = Path("data")
        assert data_dir.exists(), "data/ directory should exist"
        
        expected_files = [
            "security_breaches.json",
            "security_patches.json",
            "security_training_data.json",
            "security_vulnerabilities.json"
        ]
        
        for file_name in expected_files:
            file_path = data_dir / file_name
            assert file_path.exists(), f"{file_name} should exist in data/ directory"
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest src/tests/test_cloud_models.py

# Run specific test class
pytest src/tests/test_cloud_models.py::TestOpenAIProvider

# Run specific test method
pytest src/tests/test_cloud_models.py::TestOpenAIProvider::test_openai_chat_completion
```

### Advanced Test Execution

```bash
# Run tests with coverage
pytest --cov=src

# Run tests in parallel
pytest -n auto

# Run tests with detailed output
pytest -v -s

# Run tests and stop on first failure
pytest --maxfail=1

# Run tests with timeout (requires pytest-timeout)
pytest --timeout=30
```

### Cross-Platform Testing

```bash
# Linux/macOS
export PYTHONPATH="$PYTHONPATH:$(pwd)/src"
pytest -v

# Windows PowerShell
$env:PYTHONPATH="$env:PYTHONPATH;$(Get-Location)\src"
pytest -v

# Windows CMD
set PYTHONPATH=%PYTHONPATH%;%CD%\src
pytest -v
```

## Writing Tests

### Test Structure

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.services.providers import OpenAIProvider
from backend.services.models import ProviderConfig, ProviderType

class TestOpenAIProvider:
    """Test OpenAI provider functionality."""
    
    @pytest.fixture
    def openai_config(self):
        """Create OpenAI provider configuration."""
        return ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            models=["gpt-3.5-turbo"],
            cost_multiplier=1.0,
            priority=1
        )
    
    @patch('openai.AsyncOpenAI')
    @pytest.mark.asyncio
    async def test_openai_chat_completion(self, mock_openai, openai_config):
        """Test OpenAI chat completion."""
        # Setup mocks
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from OpenAI!"
        mock_response.usage.total_tokens = 15
        mock_response.model = "gpt-3.5-turbo"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test provider
        provider = OpenAIProvider(openai_config)
        request = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            model="gpt-3.5-turbo"
        )
        
        response = await provider.chat_completion(request)
        
        # Assertions
        assert response.content == "Hello from OpenAI!"
        assert response.model == "gpt-3.5-turbo"
        assert response.usage.total_tokens == 15
```

### Best Practices

1. **Use Fixtures**
   ```python
   @pytest.fixture
   def sample_data(self):
       """Provide test data."""
       return {"key": "value"}
   ```

2. **Mock External Dependencies**
   ```python
   @patch('httpx.AsyncClient.post')
   async def test_http_call(self, mock_post):
       # Mock the HTTP call
       mock_post.return_value = mock_response
   ```

3. **Test Async Code Properly**
   ```python
   @pytest.mark.asyncio
   async def test_async_function(self):
       result = await async_function()
       assert result == expected_value
   ```

4. **Use Descriptive Test Names**
   ```python
   def test_openai_provider_initialization_with_valid_config():
       """Test that OpenAI provider initializes correctly with valid config."""
   ```

5. **Include Edge Cases**
   ```python
   def test_openai_provider_initialization_with_invalid_api_key():
       """Test OpenAI provider initialization with invalid API key."""
   ```

### Mocking Patterns

#### Async Mocking

```python
# For async functions
mock_async_function = AsyncMock(return_value="result")
mock_async_function.return_value = "result"

# For async context managers
mock_context = AsyncMock()
mock_context.__aenter__.return_value = mock_client
mock_context.__aexit__.return_value = None
```

#### HTTP Client Mocking

```python
@patch('httpx.AsyncClient.post')
async def test_http_request(self, mock_post):
    # Create mock response
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": "value"}
    mock_response.raise_for_status = AsyncMock()
    
    # Set up the mock
    mock_post.return_value = mock_response
    
    # Test the code
    result = await make_http_request()
    assert result == {"data": "value"}
```

#### Provider Mocking

```python
@patch('openai.AsyncOpenAI')
async def test_provider(self, mock_openai):
    # Mock the client
    mock_client = AsyncMock()
    mock_openai.return_value = mock_client
    
    # Mock the response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Response"
    
    mock_client.chat.completions.create.return_value = mock_response
    
    # Test provider
    provider = OpenAIProvider(config)
    response = await provider.chat_completion(request)
```

## Debugging Tests

### Debug Mode

Enable debug output for troubleshooting:

```bash
# Run with debug output
pytest -v -s --tb=long

# Run specific test with debug
pytest -v -s src/tests/test_cloud_models.py::test_specific_function
```

### Debug Prints

Add debug prints to understand test flow:

```python
def test_function():
    print("Debug: Starting test")
    result = function_under_test()
    print(f"Debug: Result = {result}")
    assert result == expected_value
```

### Timeout Debugging

For tests that hang, use timeouts:

```python
import pytest

@pytest.mark.timeout(10)  # 10 second timeout
def test_potentially_hanging_function():
    # Test code here
    pass
```

### Mock Debugging

Debug mock behavior:

```python
def test_with_mock_debugging(self):
    mock_function = MagicMock()
    mock_function.return_value = "test"
    
    # Debug mock calls
    print(f"Mock called: {mock_function.called}")
    print(f"Mock call count: {mock_function.call_count}")
    print(f"Mock call args: {mock_function.call_args_list}")
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Error: ModuleNotFoundError: No module named 'backend'
   # Solution: Set PYTHONPATH correctly
   export PYTHONPATH="$PYTHONPATH:$(pwd)/src"
   ```

2. **Async Test Failures**
   ```python
   # Error: 'coroutine' object is not subscriptable
   # Solution: Use AsyncMock for async methods
   mock_response.json = AsyncMock(return_value={"data": "value"})
   ```

3. **Test Hangs**
   ```python
   # Solution: Add timeouts and debug prints
   @pytest.mark.timeout(10)
   def test_function():
       # Add debug prints
       print("Debug: Starting test")
       # Test code
   ```

4. **Mock Not Working**
   ```python
   # Solution: Patch at the correct import location
   @patch('backend.services.providers.openai.AsyncOpenAI')
   def test_function(self, mock_openai):
       # Test code
   ```

### Performance Issues

1. **Slow Tests**
   ```bash
   # Run tests in parallel
   pytest -n auto
   
   # Run only fast tests
   pytest -m "not slow"
   ```

2. **Memory Issues**
   ```bash
   # Run tests with memory profiling
   pytest --memray
   ```

### Cross-Platform Issues

1. **Windows Path Issues**
   ```powershell
   # Use PowerShell for better path handling
   $env:PYTHONPATH="$env:PYTHONPATH;$(Get-Location)\src"
   ```

2. **Line Ending Issues**
   ```bash
   # Configure git for consistent line endings
   git config --global core.autocrlf input
   ```

## Continuous Integration

### GitHub Actions

The project includes GitHub Actions for automated testing:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          export PYTHONPATH="$PYTHONPATH:$(pwd)/src"
          pytest -v
```

### Local CI

Run tests locally before committing:

```bash
#!/bin/bash
# pre-commit.sh
export PYTHONPATH="$PYTHONPATH:$(pwd)/src"
pytest -v --maxfail=5
```

## Test Coverage

### Coverage Reporting

```bash
# Install coverage
pip install pytest-cov

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Coverage Configuration

Add to `pytest.ini`:

```ini
[tool:pytest]
addopts = --cov=src --cov-report=term-missing
```

## Best Practices Summary

1. **Always set PYTHONPATH** for cross-platform compatibility
2. **Use absolute imports** in tests for reliability
3. **Mock external dependencies** thoroughly
4. **Test async code** with proper async/await patterns
5. **Include edge cases** and error conditions
6. **Use descriptive test names** and docstrings
7. **Add timeouts** for potentially hanging tests
8. **Debug with prints** and detailed output
9. **Run tests regularly** in CI/CD pipeline
10. **Maintain test coverage** for critical functionality

The test suite provides a robust foundation for ensuring code quality and reliability across all platforms and use cases. 