# Installation Guide

## Overview
This guide provides detailed installation instructions for the AI Coder Assistant across different platforms and hardware configurations.

## System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows 10/11
- **Python**: 3.8 or higher
- **RAM**: 8GB (16GB recommended)
- **Storage**: 10GB free space
- **GPU**: Optional but recommended for AI features

### Recommended Requirements
- **OS**: Linux with ROCm support (for AMD GPUs)
- **Python**: 3.9 or higher
- **RAM**: 16GB or more
- **Storage**: 50GB free space
- **GPU**: AMD GPU with ROCm 6.3+ or NVIDIA GPU with CUDA 11.8+

## Installation Methods

### Method 1: Standard Installation

#### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/ai-coder-assistant.git
cd ai-coder-assistant
```

#### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

#### Step 3: Install PyTorch
Choose the appropriate PyTorch installation based on your hardware:

**For AMD GPUs (ROCm):**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.3
```

**For NVIDIA GPUs (CUDA):**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**For CPU-only systems:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 5: Verify Installation
```bash
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'ROCm available: {torch.backends.mps.is_available() if hasattr(torch.backends, \"mps\") else False}')"
```

### Method 2: Docker Installation

#### Prerequisites
- Docker installed on your system
- Docker Compose (optional)

#### Build and Run
```bash
# Build the Docker image
docker build -t ai-coder-assistant .

# Run the container
docker run -it --rm -p 8000:8000 ai-coder-assistant
```

### Method 3: Development Installation

#### For Contributors
```bash
# Clone with submodules
git clone --recursive https://github.com/your-username/ai-coder-assistant.git
cd ai-coder-assistant

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install PyTorch (choose appropriate version)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.3

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Install pre-commit hooks
pre-commit install
```

## Platform-Specific Instructions

### Linux (Ubuntu/Debian)

#### Install System Dependencies
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv git build-essential
```

#### For AMD GPU Support
```bash
# Install ROCm (if not already installed)
wget https://repo.radeon.com/amdgpu-install/5.7.3/ubuntu/jammy/amdgpu-install_5.7.3.50703-1_all.deb
sudo apt install ./amdgpu-install_5.7.3.50703-1_all.deb
sudo amdgpu-install --usecase=hiplibsdk,rocm
```

#### For NVIDIA GPU Support
```bash
# Install CUDA (if not already installed)
# Follow NVIDIA's official installation guide for your distribution
```

### macOS

#### Install Homebrew (if not installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Install Dependencies
```bash
brew install python3 git
```

#### For Apple Silicon (M1/M2)
```bash
# PyTorch automatically detects Apple Silicon
pip install torch torchvision torchaudio
```

### Windows

#### Install Python
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Install with "Add Python to PATH" option checked

#### Install Git
1. Download Git from [git-scm.com](https://git-scm.com/download/win)
2. Install with default settings

#### For NVIDIA GPU Support
1. Install NVIDIA drivers from [nvidia.com](https://www.nvidia.com/Download/index.aspx)
2. Install CUDA Toolkit from [developer.nvidia.com](https://developer.nvidia.com/cuda-downloads)

## LLM Studio Setup

### Initial Configuration

After installation, set up LLM Studio for multi-provider AI support:

#### 1. Add API Keys
```bash
# OpenAI
python -m src.cli.main llm-studio add-provider --provider openai --api-key "your-openai-key"

# Google Gemini
python -m src.cli.main llm-studio add-provider --provider google_gemini --api-key "your-gemini-key"

# Claude (Anthropic)
python -m src.cli.main llm-studio add-provider --provider claude --api-key "your-claude-key"

# Ollama (local)
python -m src.cli.main llm-studio add-provider --provider ollama --api-key "http://localhost:11434"
```

#### 2. Test Connections
```bash
# Test each provider
python -m src.cli.main llm-studio test-provider --provider openai
python -m src.cli.main llm-studio test-provider --provider google_gemini
python -m src.cli.main llm-studio test-provider --provider claude
```

#### 3. List Available Models
```bash
python -m src.cli.main llm-studio list-models
```

#### 4. Start Interactive Chat
```bash
python -m src.cli.main llm-studio chat --interactive
```

### Environment Variables

Create a `.env` file in the project root for API keys:

```bash
# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_ORGANIZATION=your-organization-id

# Google Gemini
GOOGLE_API_KEY=your-gemini-api-key

# Claude (Anthropic)
ANTHROPIC_API_KEY=your-claude-api-key

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
```

## Troubleshooting

### Common Issues

#### PyTorch Installation Issues
```bash
# Clear pip cache
pip cache purge

# Force reinstall PyTorch
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.3 --force-reinstall
```

#### GPU Not Detected
```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# For AMD GPUs
python -c "import torch; print(torch.backends.mps.is_available())"
```

#### Missing Dependencies
```bash
# Update pip
pip install --upgrade pip

# Install missing packages
pip install -r requirements.txt --upgrade
```

#### Permission Issues (Linux)
```bash
# Fix ownership
sudo chown -R $USER:$USER .venv/

# Fix permissions
chmod -R 755 .venv/
```

### Performance Optimization

#### For AMD GPUs
```bash
# Set environment variables for optimal performance
export HSA_OVERRIDE_GFX_VERSION=10.3.0
export HIP_VISIBLE_DEVICES=0
```

#### For NVIDIA GPUs
```bash
# Set CUDA device
export CUDA_VISIBLE_DEVICES=0
```

## Verification

### Test Installation
```bash
# Run the application
python main.py

# Test CLI functionality
python -m src.cli.main --help

# Test API server
python api/main.py
```

### Check GPU Support
```bash
# Verify PyTorch GPU support
python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU count: {torch.cuda.device_count()}')
    print(f'Current GPU: {torch.cuda.get_device_name()}')
"
```

## Next Steps

After successful installation:

1. **Read the User Manual**: See `docs/user_manual.md`
2. **Explore Features**: Try the GUI, CLI, and API
3. **Set up LLM Studio**: Configure your AI providers
4. **Join the Community**: Report issues and contribute

## Support

- **Documentation**: Check the `docs/` directory
- **Issues**: Report bugs on GitHub
- **Discussions**: Join community discussions
- **Wiki**: Check the project wiki for additional resources

## Note on Architecture

- The codebase is now separated into `src/frontend/` (UI) and `src/backend/` (logic).
- All integration tests for frontend-backend calls are in `tests/frontend_backend/`.

## Installation Steps

1. Clone the repository...

## Running Integration Tests

After installation, you can verify frontend-backend connections by running:

```bash
python -m unittest discover tests/frontend_backend
``` 