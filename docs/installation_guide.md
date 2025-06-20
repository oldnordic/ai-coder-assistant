# AI Coder Assistant - Installation Guide

## Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Installation Methods](#installation-methods)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

## Overview

This guide provides comprehensive instructions for installing AI Coder Assistant on various platforms. The application supports multiple installation methods to accommodate different user preferences and system configurations.

## System Requirements

### Minimum Requirements

- **Operating System**: 
  - Windows 10 (64-bit) or later
  - macOS 10.15 (Catalina) or later
  - Ubuntu 18.04 LTS or later
- **Python**: 3.11 or 3.12
- **Memory**: 8GB RAM
- **Storage**: 2GB free disk space
- **Network**: Internet connection for AI model downloads

### Recommended Requirements

- **Memory**: 16GB RAM or more
- **Storage**: 5GB free disk space
- **GPU**: NVIDIA GPU with CUDA support (optional)
- **CPU**: Multi-core processor (4+ cores)

### GPU Support

For enhanced AI processing, the following GPU configurations are supported:

- **NVIDIA**: CUDA 11.8+ with compatible drivers
- **AMD**: ROCm 5.0+ (Linux only)
- **Apple**: Metal Performance Shaders (macOS)

## Installation Methods

### Method 1: Poetry Installation (Recommended)

Poetry is the recommended installation method as it provides the best dependency management and development experience.

#### Prerequisites

1. **Install Python 3.11+**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3.11-pip

   # macOS (using Homebrew)
   brew install python@3.11

   # Windows
   # Download from https://www.python.org/downloads/
   ```

2. **Install Poetry**
   ```bash
   # Install Poetry
   curl -sSL https://install.python-poetry.org | python3 -

   # Add Poetry to PATH (if not already added)
   export PATH="$HOME/.local/bin:$PATH"

   # Verify installation
   poetry --version
   ```

#### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/aicoder/ai-coder-assistant.git
   cd ai-coder-assistant
   ```

2. **Install Dependencies**
   ```bash
   # Install all dependencies including development tools
   poetry install --with dev

   # For production installation (without dev dependencies)
   poetry install --only main
   ```

3. **Activate Virtual Environment**
   ```bash
   # Activate the virtual environment
   poetry shell

   # Or run commands directly
   poetry run python -m src.main
   ```

4. **Verify Installation**
   ```bash
   # Check Python version
   poetry run python --version

   # Check installed packages
   poetry show

   # Run basic tests
   poetry run pytest --tb=short -v -m "not slow"
   ```

### Method 2: Docker Installation

Docker provides a consistent environment across different platforms and is ideal for production deployments.

#### Prerequisites

1. **Install Docker**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install docker.io docker-compose
   sudo systemctl enable --now docker
   sudo usermod -aG docker $USER

   # macOS
   # Download Docker Desktop from https://www.docker.com/products/docker-desktop

   # Windows
   # Download Docker Desktop from https://www.docker.com/products/docker-desktop
   ```

2. **Verify Docker Installation**
   ```bash
   docker --version
   docker-compose --version
   ```

#### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/aicoder/ai-coder-assistant.git
   cd ai-coder-assistant
   ```

2. **Build and Run**
   ```bash
   # Build and start the application
   docker-compose up -d ai-coder-assistant

   # For development environment
   docker-compose --profile dev up -d ai-coder-dev

   # With monitoring stack
   docker-compose --profile monitoring up -d
   ```

3. **Access the Application**
   - **GUI**: The application will be available on your local machine
   - **API**: http://localhost:8000
   - **Monitoring**: http://localhost:3000 (Grafana)

### Method 3: Binary Distribution

Pre-built binaries are available for users who prefer not to install Python or Docker.

#### Download and Installation

1. **Download Binary**
   - Visit the [GitHub Releases](https://github.com/aicoder/ai-coder-assistant/releases)
   - Download the appropriate binary for your platform

2. **Extract and Run**
   ```bash
   # Extract the archive
   tar -xzf ai-coder-assistant-1.0.0-linux.tar.gz
   cd ai-coder-assistant-1.0.0

   # Make executable
   chmod +x ai-coder-assistant

   # Run the application
   ./ai-coder-assistant
   ```

### Method 4: Development Installation

For developers who want to contribute to the project.

#### Prerequisites

1. **Install Development Tools**
   ```bash
   # Ubuntu/Debian
   sudo apt install build-essential git curl

   # macOS
   xcode-select --install

   # Windows
   # Install Visual Studio Build Tools
   ```

2. **Install Poetry with Development Dependencies**
   ```bash
   poetry install --with dev,gpu,docs
   ```

3. **Setup Pre-commit Hooks**
   ```bash
   poetry run pre-commit install
   ```

4. **Run Development Server**
   ```bash
   # Start development server
   poetry run python -m src.main

   # Run tests
   poetry run pytest

   # Run linting
   poetry run black src/
   poetry run isort src/
   poetry run flake8 src/
   ```

## Configuration

### Initial Configuration

After installation, the application will guide you through initial configuration:

1. **Welcome Screen**: Choose your preferred settings
2. **Model Selection**: Select AI models for analysis
3. **API Keys**: Configure API keys for cloud models
4. **Directory Setup**: Configure project directories

### Configuration Files

The application uses several configuration files located in the `config/` directory:

#### **LLM Studio Configuration** (`config/llm_studio_config.json`)
```json
{
  "providers": {
    "openai": {
      "api_key": "your-openai-key",
      "model": "gpt-4",
      "enabled": true
    },
    "anthropic": {
      "api_key": "your-anthropic-key",
      "model": "claude-3-sonnet",
      "enabled": true
    },
    "ollama": {
      "url": "http://localhost:11434",
      "model": "llama2",
      "enabled": true
    }
  },
  "default_provider": "openai",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

#### **Code Standards Configuration** (`config/code_standards_config.json`)
```json
{
  "python": {
    "style_guide": "pep8",
    "max_line_length": 88,
    "docstring_style": "google",
    "type_hints": true
  },
  "javascript": {
    "style_guide": "eslint",
    "max_line_length": 80,
    "semicolons": true
  },
  "java": {
    "style_guide": "google",
    "max_line_length": 100,
    "indentation": 4
  }
}
```

#### **Security Configuration** (`config/security_intelligence_config.json`)
```json
{
  "scanning": {
    "sast_enabled": true,
    "dependency_scanning": true,
    "secret_scanning": true,
    "compliance_checking": true
  },
  "standards": {
    "owasp_top_10": true,
    "cwe": true,
    "nist": true,
    "iso_27001": true,
    "soc2": true,
    "hipaa": true
  },
  "reporting": {
    "severity_levels": ["critical", "high", "medium", "low"],
    "include_recommendations": true,
    "include_examples": true
  }
}
```

### Environment Variables

The application supports various environment variables for configuration:

```bash
# API Configuration
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"

# Application Configuration
export AI_CODER_LOG_LEVEL="INFO"
export AI_CODER_DATA_DIR="/path/to/data"
export AI_CODER_CACHE_DIR="/path/to/cache"
export AI_CODER_DEBUG="false"

# Docker Configuration
export AI_CODER_DOCKER_ENABLED="true"
export AI_CODER_DOCKER_IMAGE="ai-coder-assistant:latest"

# GPU Configuration
export CUDA_VISIBLE_DEVICES="0"
export ROCR_VISIBLE_DEVICES="0"
```

### User Configuration

User-specific configuration is stored in `~/.ai_coder_assistant/`:

```bash
# Create user configuration directory
mkdir -p ~/.ai_coder_assistant

# Copy default configuration
cp config/*.json ~/.ai_coder_assistant/
```

## Verification

### Basic Functionality Test

1. **Start the Application**
   ```bash
   # Using Poetry
   poetry run python -m src.main

   # Using Docker
   docker-compose up ai-coder-assistant

   # Using binary
   ./ai-coder-assistant
   ```

2. **Verify GUI Launch**
   - The main window should appear
   - All tabs should be accessible
   - No error messages in the console

3. **Test Basic Features**
   - Navigate between tabs
   - Open settings
   - Check model status

### API Functionality Test

1. **Start API Server**
   ```bash
   # Using Poetry
   poetry run python -m src.backend.services.web_server

   # Using Docker
   docker-compose up ai-coder-api
   ```

2. **Test API Endpoints**
   ```bash
   # Health check
   curl http://localhost:8000/health

   # API documentation
   curl http://localhost:8000/docs
   ```

### CLI Functionality Test

1. **Test CLI Commands**
   ```bash
   # Help
   poetry run python -m src.cli.main --help

   # Version
   poetry run python -m src.cli.main --version

   # Scan directory
   poetry run python -m src.cli.main scan --directory /path/to/code
   ```

### Performance Test

1. **Run Performance Tests**
   ```bash
   # Run performance benchmarks
   poetry run pytest --benchmark-only -m "benchmark"

   # Check system resources
   poetry run python -c "
   from src.backend.services.performance_monitor import get_performance_monitor
   monitor = get_performance_monitor()
   monitor.start_monitoring()
   import time
   time.sleep(10)
   summary = monitor.get_metrics_summary()
   print(summary)
   "
   ```

## Troubleshooting

### Common Installation Issues

#### **Poetry Installation Issues**

**Problem**: Poetry not found in PATH
```bash
# Solution: Add Poetry to PATH
export PATH="$HOME/.local/bin:$PATH"

# Add to shell profile
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Problem**: Poetry virtual environment issues
```bash
# Solution: Recreate virtual environment
poetry env remove python
poetry install
```

#### **Docker Installation Issues**

**Problem**: Docker permission denied
```bash
# Solution: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

**Problem**: Docker build fails
```bash
# Solution: Clean and rebuild
docker-compose down
docker system prune -a
docker-compose build --no-cache
```

#### **Python Version Issues**

**Problem**: Wrong Python version
```bash
# Solution: Use correct Python version
poetry env use python3.11
poetry install
```

#### **Dependency Issues**

**Problem**: Package installation fails
```bash
# Solution: Update pip and retry
poetry run pip install --upgrade pip
poetry install --sync
```

### Runtime Issues

#### **Application Won't Start**

1. **Check Python Version**
   ```bash
   python --version
   # Should be 3.11 or 3.12
   ```

2. **Check Dependencies**
   ```bash
   poetry show
   # Should show all required packages
   ```

3. **Check Logs**
   ```bash
   # Check application logs
   tail -f logs/application.log
   ```

#### **AI Models Not Working**

1. **Check API Keys**
   ```bash
   # Verify API keys are set
   echo $OPENAI_API_KEY
   echo $ANTHROPIC_API_KEY
   ```

2. **Check Internet Connection**
   ```bash
   # Test connectivity
   curl -I https://api.openai.com
   ```

3. **Check Model Status**
   ```bash
   # Test model availability
   poetry run python -c "
   from src.backend.services.llm_manager import LLMManager
   manager = LLMManager()
   print(manager.get_available_models())
   "
   ```

#### **Performance Issues**

1. **Check System Resources**
   ```bash
   # Monitor system resources
   htop
   df -h
   free -h
   ```

2. **Check Application Performance**
   ```bash
   # Monitor application performance
   poetry run python -c "
   from src.backend.services.performance_monitor import get_performance_monitor
   monitor = get_performance_monitor()
   monitor.start_monitoring()
   import time
   time.sleep(30)
   summary = monitor.get_metrics_summary()
   print(summary)
   "
   ```

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
# Set debug environment variable
export AI_CODER_DEBUG="true"

# Or modify configuration
# In ~/.ai_coder_assistant/config.json
{
  "debug": true,
  "log_level": "DEBUG"
}
```

### Getting Help

1. **Check Documentation**: Review the documentation in `docs/`
2. **Check Issues**: Search existing issues on GitHub
3. **Create Issue**: Create a new issue with detailed information
4. **Community Support**: Join discussions on GitHub

### Support Information

When requesting help, please provide:

1. **System Information**
   ```bash
   # Operating system
   uname -a

   # Python version
   python --version

   # Poetry version
   poetry --version

   # Docker version (if applicable)
   docker --version
   ```

2. **Installation Method**: Poetry, Docker, or Binary
3. **Error Messages**: Complete error messages and stack traces
4. **Log Files**: Relevant log files from `logs/` directory
5. **Configuration**: Relevant configuration files

---

**Version**: 1.0.0  
**Last Updated**: January 2025  
**License**: GNU General Public License v3.0 