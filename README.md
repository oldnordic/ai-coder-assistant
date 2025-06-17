# AI Coder Assistant

## Overview

The AI Coder Assistant is a comprehensive desktop application built with **PyQt6** designed to be a powerful and flexible tool for software developers. It leverages both local and remote AI models to provide intelligent code analysis, suggestions, and corrections across **20 programming languages**. The assistant learns from a curated corpus of documentation and source code, allowing it to provide context‑aware help tailored to your projects.

## 🚀 Key Features

### **Multi-Language Code Analysis**
- **20 Programming Languages Supported**: Python, JavaScript, TypeScript, Java, C/C++, C#, Go, Rust, PHP, Ruby, Swift, Kotlin, Scala, Dart, R, MATLAB, Shell, SQL, HTML, and more
- **Language-Specific Linters**: Each language uses appropriate linters (flake8, eslint, cppcheck, etc.)
- **Intelligent Code Suggestions**: AI-powered fixes with language-aware context

### **Enhanced Data Acquisition**
- **Local Files**: Import documentation from your own folders
- **Advanced Web Scraping**: 
  - **Enhanced Mode**: Follows hyperlinks, navigation elements, and pagination
  - **Simple Mode**: Single-page scraping for basic content
  - **Configurable Parameters**: Control page limits, depth, and domain restrictions
  - **Documentation Crawling**: Intelligently navigates through API docs, tutorials, and guides
- **YouTube Transcription**: Uses `yt-dlp` and Whisper to transcribe videos for learning

### **AI-Powered Code Review**
- **Static Analysis**: Uses language-specific linters to find syntax errors, style issues, and potential bugs
- **Intelligent Suggestions**: Generates fixes using either Ollama models or your own trained model
- **Interactive Review**: Side‑by‑side diff interface to accept or reject changes
- **Feedback Loop**: Learns from your corrections to improve future suggestions
- **Report Generation**: Creates comprehensive Markdown reports and training data

### **Ollama Integration**
- **Model Management**: Browse, select, and manage Ollama models
- **Export Local Models**: Convert your trained models to Ollama format
- **Knowledge Feedback**: Feed learning data back to Ollama for continuous improvement
- **Private Inference**: Keep all processing on-device for privacy

### **Integrated Development Tools**
- **Web Browser**: Embedded browser for quick access to online resources
- **Multi-Language Support**: Scan projects in any of the 20 supported languages
- **Smart Ignore Patterns**: Comprehensive `.ai_coder_ignore` file for all languages
- **Progress Tracking**: Real-time progress indicators for all operations

## 🛠️ Setup and Installation

### 1. Clone the repository
```bash
git clone https://github.com/oldnordic/ai-coder-assistant.git
cd ai-coder-assistant
```

### 2. Clone `llama.cpp` (Required for Model Export)
For the "Export Local Model to Ollama" feature to work, you *must* clone the `llama.cpp` repository directly into your `ai_coder_assistant` project folder.

```bash
# Navigate to your ai_coder_assistant project directory
cd /path/to/your/ai_coder_assistant

git clone https://github.com/ggerganov/llama.cpp.git
```
After this step, you should have a `llama.cpp` directory at the same level as your `main.py` file, e.g., `/home/feanor/ai_coder_assistant/llama.cpp`.

### 3. Set up Python 3.11
- **Linux/Windows:** Install Python 3.11 from [python.org](https://www.python.org/downloads/) or use `pyenv` (Linux/macOS).

### 4. Create and activate a virtual environment
#### **Linux (bash/zsh):**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```
#### **Linux (fish):**
```fish
python3.11 -m venv .venv
source .venv/bin/activate.fish
```
#### **Windows (cmd):**
```bat
python -m venv .venv
.venv\Scripts\activate
```
#### **Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 5. Install dependencies
```bash
pip install -r requirements.txt
```

### 6. Install Language-Specific Linters (Optional)
For full multi-language support, install the linters for languages you work with:

```bash
# Python (already included)
pip install flake8

# JavaScript/TypeScript
npm install -g eslint

# C/C++
# Install cppcheck via your package manager
# Ubuntu/Debian: sudo apt install cppcheck
# Arch: sudo pacman -S cppcheck

# Go
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Rust
cargo install clippy

# Shell
# Install shellcheck via your package manager
# Ubuntu/Debian: sudo apt install shellcheck
# Arch: sudo pacman -S shellcheck

# And more... see documentation for complete list
```

### 7. Run the application
```bash
python main.py
```

## 📚 Documentation

- **[Complete User Manual](docs/user_manual.md)**: Comprehensive guide to all features
- **[Training Workflow](docs/training_workflow.md)**: Detailed steps for model training
- **[Multi-Language Support](docs/multi_language_support.md)**: Language-specific configuration

## 🔧 Configuration

### Web Scraping Options
- **Enhanced Mode**: Follows links, navigation, and pagination (default: 15 pages, 4 levels deep)
- **Simple Mode**: Single-page scraping for basic content
- **Domain Restriction**: Option to stay within the same domain
- **Content Limits**: Automatic truncation to prevent memory issues

### Supported Languages and Linters

| Language | Extensions | Linter | Notes |
|----------|------------|--------|-------|
| Python | `.py`, `.pyw`, `.pyx`, `.pyi` | `flake8` | Default support |
| JavaScript | `.js`, `.jsx`, `.mjs` | `eslint` | Requires ESLint installation |
| TypeScript | `.ts`, `.tsx` | `eslint` | Requires ESLint installation |
| Java | `.java` | `checkstyle` | Requires Checkstyle |
| C/C++ | `.c`, `.cpp`, `.h`, `.hpp` | `cppcheck` | Requires cppcheck |
| C# | `.cs` | `dotnet` | Requires .NET SDK |
| Go | `.go` | `golangci-lint` | Requires golangci-lint |
| Rust | `.rs` | `cargo` | Requires Cargo |
| PHP | `.php` | `phpcs` | Requires PHP_CodeSniffer |
| Ruby | `.rb` | `rubocop` | Requires RuboCop |
| Swift | `.swift` | `swiftlint` | Requires SwiftLint |
| Kotlin | `.kt`, `.kts` | `ktlint` | Requires ktlint |
| Scala | `.scala` | `scalafmt` | Requires scalafmt |
| Dart | `.dart` | `dart` | Requires Dart SDK |
| R | `.r`, `.R` | `lintr` | Requires lintr |
| MATLAB | `.m` | `mlint` | Requires MATLAB |
| Shell | `.sh`, `.bash`, `.zsh` | `shellcheck` | Requires shellcheck |
| SQL | `.sql` | `sqlfluff` | Requires SQLFluff |
| HTML | `.html`, `.htm` | `htmlhint` | Requires htmlhint |

## 🎯 Quick Start

1. **Launch the application**: `python main.py`
2. **Add documentation**: Use the "Data Acquisition" tab to add local files or scrape web content
3. **Preprocess data**: Click "Pre-process All Docs & Feedback" to build the knowledge base
4. **Scan your code**: Use the "AI Agent" tab to scan your project for issues
5. **Review suggestions**: Accept or reject AI-generated fixes
6. **Export to Ollama**: Use the "Export to Ollama" tab to integrate your learning

## 🔒 Privacy and Security

- **Local Processing**: All code analysis happens on your machine
- **Ollama Integration**: Keep AI processing private with local Ollama models
- **No Data Upload**: Your code and documentation never leave your system
- **Configurable Ignore**: Use `.ai_coder_ignore` to exclude sensitive files

## 🤝 Contributing

Contributions are welcome! Please see our contributing guidelines for details.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

> **Note**: To make use of the machine learning capabilities, install a PyTorch build that matches your GPU (CUDA for NVIDIA or ROCm for AMD). Otherwise the application will fall back to CPU execution, which can be noticeably slower.

> **Ollama**: To use the built-in Ollama integration you must have Ollama installed and the service running before launching the app.

> **For detailed training steps, refer to: [docs/training_workflow.md](docs/training_workflow.md)**