# AI Coder Assistant - Installation Guide

## Overview

This guide covers the complete installation and setup process for the AI Coder Assistant, including the new Cloud Model Integration feature for multi-provider LLM support. The application now uses an organized file structure with separate `config/` and `data/` directories for better maintainability.

## Project Structure

The AI Coder Assistant uses an organized file structure:

```
ai_coder_assistant/
├── config/                     # Configuration files
│   ├── code_standards_config.json
│   ├── llm_studio_config.json
│   ├── pr_automation_config.json
│   └── security_intelligence_config.json
├── data/                       # Data storage files
│   ├── security_breaches.json
│   ├── security_patches.json
│   ├── security_training_data.json
│   └── security_vulnerabilities.json
├── src/                        # Source code
├── docs/                       # Documentation
├── api/                        # API server
├── scripts/                    # Utility scripts
├── logs/                       # Application logs
├── tmp/                        # Temporary files
├── requirements.txt            # Python dependencies
├── main.py                     # Main application entry point
└── README.md                   # Project overview
```

## System Requirements

### Minimum Requirements
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: 3.8 or higher
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 10GB free space
- **GPU**: Optional but recommended for local models

### Recommended Requirements
- **OS**: Latest stable version
- **Python**: 3.11 or higher
- **RAM**: 16GB or more
- **Storage**: 50GB free space
- **GPU**: NVIDIA GPU with 8GB+ VRAM or AMD GPU with ROCm support

## Installation Methods

### Method 1: Quick Install (Recommended)

#### Prerequisites
1. **Python 3.8+**: Ensure Python is installed and in your PATH
2. **Git**: For cloning the repository
3. **pip**: Python package manager

#### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/ai-coder-assistant.git
cd ai-coder-assistant

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install additional dependencies for Cloud Models
pip install fastapi uvicorn requests openai anthropic google-generativeai

# 6. Run the application
python main.py
```

### Method 2: Docker Installation

#### Prerequisites
- **Docker**: Docker Desktop or Docker Engine
- **Docker Compose**: For multi-container setup

#### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/ai-coder-assistant.git
cd ai-coder-assistant

# 2. Build and run with Docker Compose
docker-compose up --build

# 3. Access the application
# Open http://localhost:8000 in your browser
```

### Method 3: Development Installation

#### Prerequisites
- **Python 3.8+**: Latest version recommended
- **Git**: For version control
- **Development tools**: Compiler and build tools

#### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/ai-coder-assistant.git
cd ai-coder-assistant

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# 4. Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 5. Install pre-commit hooks
pre-commit install

# 6. Run tests
python -m pytest

# 7. Start development server
python main.py
```

## Configuration Setup

### Initial Configuration

After installation, you may need to configure the application:

```bash
# 1. Edit LLM configuration
vim config/llm_studio_config.json

# 2. Edit code standards configuration
vim config/code_standards_config.json

# 3. Edit security intelligence configuration
vim config/security_intelligence_config.json

# 4. Edit PR automation configuration
vim config/pr_automation_config.json
```

### Configuration File Locations

All configuration files are now organized in the `config/` directory:

- **`config/llm_studio_config.json`**: LLM provider settings and API keys
- **`config/code_standards_config.json`**: Code standards and rules
- **`config/security_intelligence_config.json`**: Security feed configurations
- **`config/pr_automation_config.json`**: Pull request automation settings

### Data File Locations

All data files are organized in the `data/` directory:

- **`data/security_vulnerabilities.json`**: Security vulnerability data
- **`data/security_breaches.json`**: Security breach information
- **`data/security_patches.json`**: Security patch data
- **`data/security_training_data.json`**: Security training datasets

## Cloud Model Integration Setup

### Overview

The Cloud Model Integration feature allows you to use multiple AI providers (OpenAI, Anthropic, Google AI) with automatic failover, cost tracking, and health monitoring.

### Provider Configuration

#### 1. OpenAI Setup

**Get API Key**:
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)

**Configure Environment**:
```bash
# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"
export OPENAI_BASE_URL="https://api.openai.com"  # Optional
export OPENAI_ORGANIZATION="your-org-id"  # Optional
```

**Using the UI**:
1. Open AI Coder Assistant
2. Go to "Cloud Models" tab
3. Click "Add Provider"
4. Select "OpenAI"
5. Enter your API key
6. Set priority (1 = highest)
7. Click "Save"

#### 2. Anthropic Setup

**Get API Key**:
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)

**Configure Environment**:
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

**Using the UI**:
1. Go to "Cloud Models" tab
2. Click "Add Provider"
3. Select "Anthropic"
4. Enter your API key
5. Set priority
6. Click "Save"

#### 3. Google AI Setup

**Get API Key**:
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Create a new API key
4. Copy the key

**Configure Environment**:
```bash
export GOOGLE_API_KEY="your-google-api-key"
```

**Using the UI**:
1. Go to "Cloud Models" tab
2. Click "Add Provider"
3. Select "Google AI"
4. Enter your API key
5. Set priority
6. Click "Save"

#### 4. Ollama Setup

**Install Ollama**:
```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

**Start Ollama**:
```bash
ollama serve
```

**Pull Models**:
```bash
# Pull a model
ollama pull llama3:latest

# Or pull your custom model
ollama pull your-model:latest
```

**Configure in UI**:
1. Go to "Cloud Models" tab
2. Click "Add Provider"
3. Select "Ollama"
4. Enter endpoint: `http://localhost:11434`
5. Set priority
6. Click "Save"

### CLI Configuration

You can also configure providers using the command line:

```bash
# Check status
python -m src.cli.main llm-studio status

# Add OpenAI provider
python -m src.cli.main llm-studio add-provider --provider openai --api-key "your-key"

# Add Anthropic provider
python -m src.cli.main llm-studio add-provider --provider anthropic --api-key "your-key"

# Add Google AI provider
python -m src.cli.main llm-studio add-provider --provider google_gemini --api-key "your-key"

# Add Ollama provider
python -m src.cli.main llm-studio add-provider --provider ollama --api-key "http://localhost:11434"

# List providers
python -m src.cli.main llm-studio list-providers

# Test provider
python -m src.cli.main llm-studio test-provider --provider openai
```

## Language-Specific Setup

### Python Development

**Install Python Linters**:
```bash
pip install flake8 black isort mypy
```

**Configure Linters**:
```bash
# Create .flake8 configuration
echo "[flake8]
max-line-length = 88
extend-ignore = E203, W503
" > .flake8

# Create pyproject.toml for black
echo "[tool.black]
line-length = 88
target-version = ['py38']
" > pyproject.toml
```

### JavaScript/TypeScript Development

**Install Node.js**:
```bash
# Using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install node
nvm use node
```

**Install Linters**:
```bash
npm install -g eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
```

**Configure ESLint**:
```bash
# Initialize ESLint configuration
eslint --init
```

### Java Development

**Install Java**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install openjdk-11-jdk

# macOS
brew install openjdk@11

# Windows
# Download from https://adoptium.net/
```

**Install Checkstyle**:
```bash
# Download checkstyle
wget https://github.com/checkstyle/checkstyle/releases/download/checkstyle-10.12.5/checkstyle-10.12.5-all.jar
```

### C/C++ Development

**Install Compiler**:
```bash
# Ubuntu/Debian
sudo apt install build-essential

# macOS
xcode-select --install

# Windows
# Install Visual Studio Build Tools
```

**Install cppcheck**:
```bash
# Ubuntu/Debian
sudo apt install cppcheck

# macOS
brew install cppcheck

# Windows
# Download from https://cppcheck.sourceforge.io/
```

## Configuration Files

### Environment Variables

Create a `.env` file in the project root:

```bash
# AI Provider API Keys
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key

# Ollama Configuration
OLLAMA_ENDPOINT=http://localhost:11434

# Application Settings
LOG_LEVEL=INFO
DEBUG_MODE=false
MAX_WORKERS=4

# Database Settings (if using)
DATABASE_URL=sqlite:///ai_coder.db

# Security Settings
SECRET_KEY=your-secret-key
```

### Application Configuration

Create `config.yaml` in the project root:

```yaml
# Application Settings
app:
  name: "AI Coder Assistant"
  version: "1.0.0"
  debug: false
  log_level: "INFO"

# AI Providers
providers:
  openai:
    enabled: true
    priority: 1
    timeout: 30
    max_retries: 3
  
  anthropic:
    enabled: true
    priority: 2
    timeout: 30
    max_retries: 3
  
  google:
    enabled: true
    priority: 3
    timeout: 30
    max_retries: 3
  
  ollama:
    enabled: true
    priority: 4
    timeout: 60
    max_retries: 1

# Models
models:
  default:
    provider: "openai"
    model: "gpt-4"
    temperature: 0.7
    max_tokens: 1000
  
  fallback:
    provider: "anthropic"
    model: "claude-3-sonnet"
    temperature: 0.7
    max_tokens: 1000

# Cost Management
cost_management:
  daily_limit: 10.0
  alert_threshold: 0.8
  auto_switch: true

# Health Monitoring
health_monitoring:
  check_interval: 300  # 5 minutes
  failover_threshold: 3
  recovery_check_interval: 60  # 1 minute
```

## Verification and Testing

### 1. Basic Functionality Test

```bash
# Start the application
python main.py

# Check if the UI loads
# Navigate through different tabs
# Verify basic functionality
```

### 2. Cloud Model Integration Test

```bash
# Test provider connections
python -m src.cli.main llm-studio status

# Test individual providers
python -m src.cli.main llm-studio test-provider --provider openai
python -m src.cli.main llm-studio test-provider --provider anthropic
python -m src.cli.main llm-studio test-provider --provider google_gemini
python -m src.cli.main llm-studio test-provider --provider ollama
```

### 3. Code Analysis Test

```bash
# Test code analysis with CLI
python -m src.cli.main analyze --file src/main.py --language python --format text

# Test workspace scanning
python -m src.cli.main scan . --output scan_results.json --format json
```

### 4. Advanced Refactoring Test

```bash
# Test refactoring analysis
# Use the UI to analyze a project
# Verify refactoring suggestions are generated
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
```bash
# Ensure you're in the project root directory
cd ai-coder-assistant

# Add project root to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run with module flag
python -m src.cli.main
```

#### 2. API Key Issues

**Problem**: Provider authentication fails

**Solution**:
```bash
# Verify API keys are set
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
echo $GOOGLE_API_KEY

# Test API keys manually
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

#### 3. Ollama Connection Issues

**Problem**: Cannot connect to Ollama

**Solution**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve

# Check Ollama logs
ollama logs
```

#### 4. Memory Issues

**Problem**: Application runs out of memory

**Solution**:
```bash
# Increase Python memory limit
export PYTHONMALLOC=malloc
export PYTHONDEVMODE=1

# Or run with memory optimization
python -X dev main.py
```

#### 5. GPU Issues

**Problem**: GPU not detected or used

**Solution**:
```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# Install GPU drivers
# NVIDIA: Install CUDA toolkit
# AMD: Install ROCm
```

### Performance Optimization

#### 1. Memory Optimization

```bash
# Set memory limits
export PYTHONMALLOC=malloc
export MALLOC_ARENA_MAX=2

# Use memory-efficient settings
python main.py --memory-efficient
```

#### 2. GPU Optimization

```bash
# Enable GPU acceleration
export CUDA_VISIBLE_DEVICES=0
export ROCR_VISIBLE_DEVICES=0

# Use mixed precision
export TORCH_AMP_ENABLED=1
```

#### 3. Network Optimization

```bash
# Set connection pooling
export REQUESTS_SESSION_POOL_SIZE=10
export REQUESTS_SESSION_POOL_MAXSIZE=20

# Enable HTTP/2
export REQUESTS_HTTP2_ENABLED=1
```

## Security Considerations

### 1. API Key Security

```bash
# Use environment variables (recommended)
export OPENAI_API_KEY="your-key"

# Or use a secrets manager
# AWS Secrets Manager, Azure Key Vault, etc.

# Never commit API keys to version control
echo "*.key" >> .gitignore
echo ".env" >> .gitignore
```

### 2. Network Security

```bash
# Use HTTPS for all API calls
export OPENAI_BASE_URL="https://api.openai.com"

# Set up firewall rules
# Allow only necessary outbound connections

# Use VPN for additional security
```

### 3. Data Privacy

```bash
# Configure data retention
export DATA_RETENTION_DAYS=30

# Enable data encryption
export ENCRYPT_DATA=true

# Set up audit logging
export AUDIT_LOG_ENABLED=true
```

## Updates and Maintenance

### 1. Updating the Application

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run migrations (if any)
python -m src.backend.migrations

# Restart the application
python main.py
```

### 2. Updating Models

```bash
# Update Ollama models
ollama pull llama3:latest

# Update local models
python -m src.backend.services.trainer --update-models
```

### 3. Backup and Recovery

```bash
# Backup configuration
cp config.yaml config.yaml.backup

# Backup database (if using)
cp ai_coder.db ai_coder.db.backup

# Backup trained models
tar -czf models_backup.tar.gz src/backend/data/processed_data/
```

## Support and Resources

### Documentation
- [User Manual](docs/user_manual.md)
- [Cloud Model Integration Guide](docs/cloud_model_integration_guide.md)
- [Advanced Refactoring Guide](docs/advanced_refactoring_guide.md)
- [API Documentation](docs/api_documentation.md)

### Community
- [GitHub Issues](https://github.com/your-username/ai-coder-assistant/issues)
- [Discussions](https://github.com/your-username/ai-coder-assistant/discussions)
- [Wiki](https://github.com/your-username/ai-coder-assistant/wiki)

### Troubleshooting
- [FAQ](docs/faq.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
- [Performance Tuning](docs/performance_tuning.md)

## Conclusion

The AI Coder Assistant is now fully installed and configured with Cloud Model Integration. You can:

1. **Use Multiple AI Providers**: Configure OpenAI, Anthropic, Google AI, and Ollama
2. **Monitor Costs**: Track usage and optimize spending
3. **Ensure Reliability**: Automatic failover between providers
4. **Analyze Code**: Use intelligent code analysis across 20+ languages
5. **Refactor Code**: Apply advanced refactoring suggestions
6. **Train Models**: Create custom models for your domain

For the best experience, ensure all providers are properly configured and test the functionality using the provided CLI commands and UI tools. 