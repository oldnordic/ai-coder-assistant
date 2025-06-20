# AI Coder Assistant: Binary Build Instructions

This guide provides comprehensive instructions for building optimized binaries of the AI Coder Assistant using a modern modular approach that minimizes size and memory consumption.

## 🎯 **Build Strategy Overview**

The AI Coder Assistant uses a **modular binary architecture** that separates the application into focused components:

- **Core Application** (5-8MB): Main GUI and window management
- **AI Analyzer** (3-5MB): Intelligent code analysis engine
- **Code Scanner** (2-3MB): Code scanning and linting
- **Web Scraper** (2-3MB): Web scraping and document acquisition
- **Model Trainer** (4-6MB): Model training and fine-tuning
- **Continuous Learning** (3-4MB): Continuous learning and feedback management
- **Launcher** (1-2MB): Component orchestration

**Total Size**: ~25-35MB (vs 150-200MB for traditional single binary)
**Memory Usage**: 100-200MB (vs 500-800MB for traditional approach)
**Startup Time**: 2-5 seconds (vs 10-15 seconds for traditional approach)

## 🚀 **Quick Start**

### **Windows Users**
```batch
# Download and run the Windows build script
build_windows.bat
```

### **Linux Users**
```bash
# Make script executable and run
chmod +x build_linux.sh
./build_linux.sh
```

### **macOS Users**
```bash
# Make script executable and run
chmod +x build_macos.sh
./build_macos.sh
```

### **Docker Users**
```bash
# Build using Docker
docker build -t ai-coder-builder .
docker run -v $(pwd)/dist:/app/dist ai-coder-builder

# Or use Docker Compose
docker-compose --profile build up
```

## 📋 **Prerequisites**

### **System Requirements**
- **Python 3.8+**: Required for building
- **Git**: For cloning the repository
- **4GB+ RAM**: For building process
- **2GB+ Disk Space**: For build artifacts
- **GPU Support** (Optional): CUDA/ROCm for accelerated training

### **Python Dependencies**
The build process will automatically install:
- **PyInstaller**: For creating standalone binaries
- **UPX**: For binary compression (30-50% size reduction)
- **PyTorch**: For AI model training and continuous learning
- **Transformers**: For HuggingFace model integration
- **All project dependencies**: From requirements.txt

### **Platform-Specific Requirements**

#### **Windows**
- Python 3.8+ installed and in PATH
- PowerShell (for UPX download)
- Visual Studio Build Tools (optional, for better optimization)
- CUDA Toolkit (optional, for GPU acceleration)

#### **Linux**
- Python 3.8+ and pip
- Build essentials: `sudo apt-get install build-essential`
- UPX: `sudo apt-get install upx` (or auto-installed by script)
- ROCm (optional, for AMD GPU acceleration)

#### **macOS**
- Python 3.8+ and pip
- Homebrew (recommended): `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
- Xcode Command Line Tools: `xcode-select --install`
- Metal Performance Shaders (optional, for GPU acceleration)

## 🛠 **Manual Build Process**

### **Step 1: Clone Repository**
```bash
git clone <repository-url>
cd ai-coder-assistant
```

### **Step 2: Set Up Build Environment**
```bash
# Create virtual environment
python -m venv build-env

# Activate environment
# Windows:
build-env\Scripts\activate
# Linux/macOS:
source build-env/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Install GPU support (optional)
# For CUDA (NVIDIA):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For ROCm (AMD):
python install_rocm_pytorch.py

# For CPU only:
pip install torch torchvision torchaudio
```

### **Step 3: Install UPX (Optional but Recommended)**
```bash
# Windows (PowerShell):
Invoke-WebRequest -Uri "https://github.com/upx/upx/releases/download/v4.0.2/upx-4.0.2-win64.zip" -OutFile "upx.zip"
Expand-Archive -Path "upx.zip" -DestinationPath "." -Force
copy "upx-4.0.2-win64\upx.exe" "build-env\Scripts\"

# Linux:
sudo apt-get install upx

# macOS:
brew install upx
```

### **Step 4: Build All Components**
```bash
# Build all components
python build_all.py

# Or build specific component
python build_all.py --component core
python build_all.py --component analyzer
python build_all.py --component scanner
python build_all.py --component web
python build_all.py --component trainer
python build_all.py --component continuous-learning
```

### **Step 5: Clean Build (Optional)**
```bash
# Clean previous builds
python build_all.py --clean
```

## 📦 **Build Output**

After successful build, you'll find the following structure in the `dist/` directory:

```
dist/
├── ai-coder-core.exe              # Main GUI application
├── ai-coder-analyzer.exe          # AI analysis engine
├── ai-coder-scanner.exe           # Code scanner
├── ai-coder-web.exe               # Web scraper
├── ai-coder-trainer.exe           # Model trainer
├── ai-coder-continuous-learning.exe # Continuous learning system
├── ai-coder-launcher.exe          # Component launcher
├── run.py                         # Python launcher script
├── shared/
│   ├── models/                    # AI models (optional)
│   ├── config/                    # Configuration files
│   │   ├── code_standards_config.json
│   │   ├── llm_studio_config.json
│   │   ├── pr_automation_config.json
│   │   └── security_intelligence_config.json
│   ├── data/                      # Data directory
│   │   ├── security_breaches.json
│   │   ├── security_patches.json
│   │   ├── security_training_data.json
│   │   └── security_vulnerabilities.json
│   └── continuous_learning_data/  # Continuous learning database
├── docs/                          # Documentation
├── README.md                      # Instructions
└── requirements.txt               # Dependencies
```

## 🚀 **Running the Application**

### **From Binary Distribution**
```bash
# Run main GUI application
./dist/ai-coder-core

# Or use the launcher
./dist/ai-coder-launcher core

# Run specific components
./dist/ai-coder-launcher analyzer --file main.py --language python
./dist/ai-coder-launcher scanner --path /path/to/code
./dist/ai-coder-launcher web --url https://example.com
./dist/ai-coder-launcher trainer --data training_data.txt
./dist/ai-coder-launcher continuous-learning --feedback feedback.json
```

### **From Source (Alternative)**
```bash
# If you have Python installed
python run.py
```

## 🔧 **Advanced Build Options**

### **Custom Build Configuration**
```python
# build_config.py
BUILD_CONFIG = {
    'optimization_level': 'high',  # low, medium, high
    'compression': 'upx',          # upx, lzma, none
    'strip_symbols': True,
    'exclude_modules': [
        'matplotlib', 'numpy', 'pandas', 'scipy'
    ],
    'include_modules': [
        'PyQt6.QtCore', 'PyQt6.QtWidgets',
        'torch', 'transformers', 'datasets'
    ],
    'continuous_learning': {
        'enabled': True,
        'database_path': 'continuous_learning_data/',
        'model_backup': True
    }
}
```

### **GPU Acceleration Support**
```bash
# Build with CUDA support (NVIDIA)
python build_all.py --gpu cuda

# Build with ROCm support (AMD)
python build_all.py --gpu rocm

# Build with Metal support (macOS)
python build_all.py --gpu metal

# Build for CPU only
python build_all.py --gpu cpu
```

### **Continuous Learning Configuration**
```bash
# Build with continuous learning enabled
python build_all.py --enable-continuous-learning

# Build with specific database backend
python build_all.py --database sqlite

# Build with model backup enabled
python build_all.py --enable-model-backup
```

## 🆕 **New Features in v2.0.0**

### **Continuous Learning System**
- **Real-time Model Updates**: Incremental training with user feedback
- **Performance Monitoring**: Automatic evaluation and rollback
- **Quality Validation**: Intelligent filtering of training data
- **UI Dashboard**: Complete continuous learning management interface

### **Enhanced Platform Support**
- **AMD GPU Support**: ROCm integration for AMD graphics cards
- **Apple Silicon**: Native support for M1/M2 Macs
- **Windows CUDA**: Full CUDA support for NVIDIA GPUs
- **Cross-Platform**: Consistent experience across all platforms

### **Improved Build Process**
- **Modular Architecture**: Smaller, focused binaries
- **GPU Acceleration**: Optional GPU support for training
- **Dependency Optimization**: Reduced binary sizes
- **Cross-Platform**: Single build script for all platforms

## 📊 **Build Metrics**

### **Size Comparison**
| Component | Traditional | Modular | Reduction |
|-----------|-------------|---------|-----------|
| **Single Binary** | 150-200MB | N/A | N/A |
| **Modular Binaries** | N/A | 20-30MB | 85-90% |
| **Memory Usage** | 500-800MB | 100-200MB | 75-80% |
| **Startup Time** | 10-15s | 2-5s | 70-80% |

### **Component Breakdown**
| Component | Size | Dependencies | Function |
|-----------|------|--------------|----------|
| **Core** | 5-8MB | PyQt6, basic config | Main GUI |
| **Analyzer** | 3-5MB | transformers, torch | AI analysis |
| **Scanner** | 2-3MB | pathspec, networkx | Code scanning |
| **Web** | 2-3MB | requests, beautifulsoup4 | Web scraping |
| **Trainer** | 4-6MB | torch, datasets | Model training |
| **Continuous Learning** | 3-4MB | torch, transformers, datasets | Continuous learning |
| **Launcher** | 1-2MB | minimal Python | Orchestration |

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Python Not Found**
```bash
# Windows
python --version
# If not found, install Python from python.org

# Linux/macOS
python3 --version
# If not found: sudo apt-get install python3 (Linux) or brew install python (macOS)
```

#### **PyInstaller Installation Failed**
```bash
# Upgrade pip first
pip install --upgrade pip

# Install with specific version
pip install pyinstaller==5.13.0

# Or install from source
pip install git+https://github.com/pyinstaller/pyinstaller.git
```

#### **UPX Not Found**
```bash
# Manual installation
# Windows: Download from https://upx.github.io/
# Linux: sudo apt-get install upx
# macOS: brew install upx
```

#### **Build Fails with Import Errors**
```bash
# Clean and rebuild
python build_all.py --clean
python build_all.py

# Check dependencies
pip list | grep -E "(torch|transformers|PyQt6)"
```

#### **Binary Too Large**
```bash
# Enable UPX compression
python build_all.py --compression upx

# Exclude unnecessary modules
python build_all.py --exclude-modules matplotlib,numpy,pandas

# Use higher optimization
python build_all.py --optimization-level high
```

#### **Binary Won't Run**
```bash
# Check permissions (Linux/macOS)
chmod +x dist/*

# Check dependencies
ldd dist/ai-coder-core  # Linux
otool -L dist/ai-coder-core  # macOS

# Run with debug output
./dist/ai-coder-core --debug
```

### **Platform-Specific Issues**

#### **Windows**
- **Antivirus blocking**: Add build directory to exclusions
- **PowerShell execution policy**: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- **Visual Studio Build Tools**: Install for better optimization

#### **Linux**
- **Missing libraries**: `sudo apt-get install libgl1-mesa-glx libglib2.0-0`
- **Permission denied**: `chmod +x dist/*`
- **UPX not found**: `sudo apt-get install upx`

#### **macOS**
- **Security warning**: Allow in System Preferences > Security & Privacy
- **Missing Xcode tools**: `xcode-select --install`
- **Homebrew not found**: Install from https://brew.sh/

## 🔄 **Continuous Integration**

### **GitHub Actions Example**
```yaml
name: Build Binaries

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Build binaries
      run: python build_all.py
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: ai-coder-assistant-${{ matrix.os }}
        path: dist/
```

## 📚 **Additional Resources**

- **PyInstaller Documentation**: https://pyinstaller.org/
- **UPX Documentation**: https://upx.github.io/
- **Docker Documentation**: https://docs.docker.com/
- **Project Documentation**: See `docs/` directory

## 🤝 **Support**

If you encounter issues with the build process:

1. **Check the troubleshooting section** above
2. **Review the build logs** in the `logs/` directory
3. **Search existing issues** in the project repository
4. **Create a new issue** with detailed information:
   - Operating system and version
   - Python version
   - Full error message
   - Build command used
   - Build logs

## 📄 **License**

This build system is part of the AI Coder Assistant project and follows the same license terms. See the main LICENSE file for details. 