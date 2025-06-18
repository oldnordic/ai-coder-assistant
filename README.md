# AI Coder Assistant

A comprehensive PyQt6-based AI-powered code analysis and development assistant with intelligent code scanning, multi-language support, model training, continuous learning, and seamless integration with Ollama and MCP servers.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)](https://pypi.org/project/PyQt6/)

## 🚀 **New: Continuous Learning & Advanced AI Features**

The application now features **sophisticated continuous learning capabilities** and **advanced AI-powered code analysis** that goes far beyond traditional linters:

### **🧠 Continuous Learning System**

#### **1. Real-Time Model Improvement**
- **Incremental Training**: Continuous model updates with user feedback
- **Performance Monitoring**: Automatic evaluation of model improvements
- **Rollback Protection**: Automatic rollback on performance degradation
- **Quality Validation**: Intelligent filtering of training data
- **Replay Buffer**: Prevents catastrophic forgetting with experience replay

#### **2. Feedback Collection & Management**
- **Multi-Type Feedback**: Corrections, improvements, rejections, approvals
- **Quality Scoring**: Automatic assessment of feedback quality
- **User Ratings**: 1-5 scale rating system for model outputs
- **Context Preservation**: Maintains full context for training
- **Batch Processing**: Efficient handling of large feedback volumes

#### **3. Advanced Model Management**
- **Real Training Integration**: Actual model finetuning with HuggingFace Trainer
- **Backup & Recovery**: Automatic model backup before updates
- **Performance Tracking**: Detailed metrics on model improvements
- **Update History**: Complete audit trail of all model changes
- **Force Update Mode**: Emergency updates with minimal training data

#### **4. Intelligent UI Dashboard**
- **Real-Time Statistics**: Live feedback and update metrics
- **Model Update Controls**: Batch size, force update, and scheduling
- **Feedback Collection**: Intuitive forms for user feedback
- **Admin Panel**: Data export, cleanup, and system management
- **Progress Tracking**: Real-time progress for all operations

### **🧠 Advanced Analysis Capabilities**

#### **1. Semantic Code Analysis**
- **Function Call Analysis**: Detects dangerous functions (eval, exec, input)
- **Comparison Logic**: Identifies incorrect comparisons (== vs is)
- **Boolean Logic**: Finds redundant boolean expressions
- **Language-Specific Semantics**: JavaScript loose equality, Python identity checks

#### **2. Data Flow Analysis**
- **Variable Tracking**: Detects unused and undefined variables
- **Data Dependencies**: Analyzes variable usage patterns
- **Scope Analysis**: Identifies variable scope issues
- **Cross-File Analysis**: Tracks variables across multiple files

#### **3. Pattern Detection**
- **Design Patterns**: Recognizes Singleton, Factory, and other patterns
- **Anti-Patterns**: Detects God Objects, Spaghetti Code, Callback Hell
- **Code Smells**: Identifies complex nested structures and poor practices
- **Architectural Patterns**: Analyzes project structure and organization

#### **4. Dependency Analysis**
- **Circular Dependencies**: Detects dependency cycles in codebase
- **Dependency Complexity**: Analyzes import/export relationships
- **Unused Dependencies**: Identifies unused imports and modules
- **Architectural Assessment**: Evaluates project structure quality

#### **5. Enhanced Security Detection**
- **Hardcoded Credentials**: Detects passwords, API keys, tokens
- **SQL Injection**: Identifies unsafe SQL query construction
- **Code Injection**: Finds eval, exec, and other dangerous functions
- **XSS Vulnerabilities**: Detects innerHTML and document.write usage

#### **6. Memory and Performance Analysis**
- **Memory Leaks**: Detects infinite loops and large data structures
- **Performance Issues**: Identifies nested loops and inefficient patterns
- **Resource Usage**: Analyzes memory allocation patterns
- **Optimization Opportunities**: Suggests performance improvements

### **🎯 Multi-Language Intelligence**

The AI analyzer provides **advanced analysis across 20+ languages**:

- **Python**: AST-based analysis, complexity calculation, semantic patterns
- **JavaScript/TypeScript**: Loose equality, callback patterns, global variables
- **Java**: Raw types, exception handling, logging practices
- **C/C++**: Memory management, pointer safety, casting practices
- **Go**: Error handling, panic usage, unused imports
- **Rust**: Unwrap usage, cloning patterns, memory safety
- **PHP**: Deprecated functions, error suppression, global usage
- **Ruby**: Eval usage, instance variables, logging practices
- **Shell**: Unquoted variables, command injection, security issues
- **SQL**: Query optimization, index usage, security patterns
- **HTML**: Accessibility, inline styles, best practices

### **📊 Analysis Categories**

The AI categorizes issues into **comprehensive categories**:

- **🔴 Critical**: Security vulnerabilities, undefined variables, syntax errors
- **🟠 High**: Performance issues, architectural problems, code smells
- **🟡 Medium**: Maintainability issues, best practice violations
- **🟢 Low**: Style issues, documentation problems, minor optimizations

### **🚀 Performance Gains**
- **Code Scanning**: Up to **7.7x faster** with parallel file processing
- **Document Preprocessing**: Up to **5.5x faster** with parallel file handling  
- **Web Scraping**: Up to **5x faster** with parallel URL processing
- **GitHub Acquisition**: Up to **8x faster** with parallel file downloading
- **Model Training**: Real-time incremental updates with performance monitoring

### **Smart Thread Management**
- **Automatic Optimization**: Thread count adapts to CPU cores and workload
- **I/O Operations**: Capped at 6-8 threads for web scraping and file I/O
- **CPU-Intensive Tasks**: Uses up to 8 threads for code analysis
- **Thread-Safe Progress**: Real-time progress tracking across all workers

### **Multi-Threaded Features**
✅ **Parallel Code Scanning** - Multiple files analyzed simultaneously  
✅ **Parallel Document Processing** - PDF, HTML, and text files processed concurrently  
✅ **Parallel Web Scraping** - Multiple URLs scraped simultaneously  
✅ **Parallel Linter Execution** - Multiple linters run concurrently  
✅ **Parallel Intelligent Analysis** - AI analysis runs on multiple files at once  
✅ **Parallel GitHub Acquisition** - Multiple files downloaded simultaneously  
✅ **Continuous Learning** - Real-time model updates with feedback processing  

## ✨ Key Features

### 🧠 **Continuous Learning & AI Intelligence**
- **Real-Time Model Improvement**: Continuous updates based on user feedback
- **Performance Monitoring**: Automatic evaluation and rollback protection
- **Quality Validation**: Intelligent filtering of training data
- **Advanced Code Analysis**: Beyond linter errors with semantic understanding
- **Multi-Language Intelligence**: Comprehensive analysis across 20+ programming languages
- **Security Vulnerability Detection**: Identifies potential security issues and code smells
- **Performance Optimization**: Detects inefficient patterns and suggests improvements
- **Maintainability Assessment**: Evaluates code quality and maintainability factors
- **Detailed Issue Classification**: Categorizes issues by type, severity, and context

### 🔍 **Advanced Code Scanning**
- **Multi-Language Support**: Analyzes 20+ programming languages with intelligent detection
- **Linter Integration**: Seamless integration with language-specific linters
- **Intelligent Pattern Recognition**: Identifies code smells, anti-patterns, and best practice violations
- **Context-Aware Suggestions**: Provides contextual improvements based on surrounding code
- **Comprehensive Reporting**: Detailed summaries with actionable recommendations

### 🤖 **AI-Powered Features**
- **Ollama Integration**: Local AI model support with custom model training
- **OpenAI & Gemini APIs**: Cloud-based AI analysis for enhanced capabilities
- **Intelligent Code Enhancement**: AI-generated suggestions for code improvements
- **Learning from Feedback**: Improves suggestions based on user corrections
- **Context-Aware Explanations**: Detailed explanations of detected issues
- **Continuous Model Updates**: Real-time model improvement through feedback

### 📚 **Document Processing**
- **Multi-Format Support**: PDF, HTML, and text document processing
- **Intelligent Text Extraction**: Advanced content extraction with formatting preservation
- **Training Data Generation**: Automatic creation of training datasets from documents
- **Parallel Processing**: Multi-threaded document handling for improved performance

### 🌐 **Web Integration**
- **Enhanced Web Scraping**: Intelligent crawling with configurable depth and page limits
- **GitHub Code Acquisition**: Direct integration with GitHub API for code collection
- **MCP Server Management**: Download and manage MCP servers for extended functionality
- **API Key Management**: Secure storage and management of API credentials

### 🎯 **Model Training & Export**
- **Custom Model Training**: Train models on your specific codebase and documentation
- **Ollama Export**: Export trained models to Ollama for local deployment
- **GGUF Format Support**: Industry-standard model format compatibility
- **Incremental Learning**: Continuous improvement through user feedback
- **Real Training Integration**: Actual model finetuning with performance monitoring

### 🖥️ **Advanced UI & User Experience**
- **Continuous Learning Dashboard**: Real-time feedback and model management
- **Intuitive Feedback Collection**: Easy-to-use forms for user feedback
- **Model Update Controls**: Batch processing and force update capabilities
- **Admin Panel**: Data export, cleanup, and system management
- **Progress Tracking**: Real-time progress for all operations
- **Multi-Tab Interface**: Organized workflow with dedicated tabs for each feature

## 🚀 AI-Powered PR Creation

Create intelligent Pull Requests with AI-generated fixes and industry-standard templates.

### CLI Usage

```bash
# Create PR from scan results
python -m src.cli.main create-pr scan_result1.json scan_result2.json \
  --pr-type security_fix \
  --priority-strategy easy_win_first \
  --auto-commit \
  --create-pr

# Create PR with custom options
python -m src.cli.main create-pr scan_results/*.json \
  --repo-path /path/to/repo \
  --base-branch main \
  --pr-type code_quality \
  --priority-strategy severity_first \
  --labels "ai-generated" "code-quality" \
  --assignees "developer1" "developer2" \
  --reviewers "senior-dev" \
  --output pr_summary.json
```

### PR Types

- **🔒 Security Fix**: Fix security vulnerabilities with comprehensive testing
- **🔧 Code Quality**: Improve code maintainability and readability
- **⚡ Performance**: Optimize performance bottlenecks
- **📋 Compliance**: Address regulatory compliance requirements
- **🔄 Refactoring**: Improve code architecture and structure
- **🐛 Bug Fix**: Fix bugs and issues

### Priority Strategies

- **🔴 Severity First**: Prioritize by issue severity (critical → high → medium → low)
- **🎯 Easy Win First**: Prioritize easy fixes for quick wins
- **⚖️ Balanced**: Balance severity and complexity
- **💼 Impact First**: Prioritize by business impact

### Features

#### 🤖 AI-Powered Analysis
- **Intelligent Fix Generation**: AI suggests code fixes for each issue
- **Complexity Assessment**: Automatically determines fix complexity
- **Confidence Scoring**: Provides confidence levels for each fix
- **Time Estimation**: Estimates time required for each fix

#### 📊 Multi-Scan Integration
- **Deduplication**: Removes duplicate issues across multiple scans
- **Conflict Resolution**: Resolves conflicts between similar issues
- **Priority Optimization**: Optimizes issue order based on strategy
- **Comprehensive Summary**: Provides detailed integration statistics

#### 🎨 Industry-Standard Templates
- **Conventional Commits**: Follows conventional commit standards
- **GitHub Standard**: Uses GitHub PR templates
- **Enterprise**: Enterprise-grade templates with compliance sections
- **Open Source**: Community-friendly templates

#### 🔄 Git Integration
- **Automatic Branching**: Creates descriptive branch names
- **Smart Committing**: Generates meaningful commit messages
- **GitHub PR Creation**: Automatically creates GitHub PRs (requires gh CLI)
- **Conflict Resolution**: Handles merge conflicts gracefully

### REST API

```bash
# Create PR from scan results
curl -X POST "http://localhost:8000/create-pr" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_result_files": ["scan1.json", "scan2.json"],
    "pr_type": "security_fix",
    "priority_strategy": "severity_first",
    "auto_commit": true,
    "create_pr": true
  }'

# Create PR from issues
curl -X POST "http://localhost:8000/create-pr-from-issues" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_path": "/path/to/repo",
    "pr_type": "code_quality",
    "issues": [...]
  }'

# Get available templates
curl -X GET "http://localhost:8000/pr-templates" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get priority strategies
curl -X GET "http://localhost:8000/priority-strategies" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### VS Code Extension

The VS Code extension provides seamless PR creation:

1. **Create PR from Scan Results**: Select scan result files and create PR
2. **Create PR from Current Scan**: Run scan and create PR in one step
3. **Show PR Templates**: View and customize PR templates
4. **Context Menu Integration**: Right-click on scan result files to create PR

### Configuration Options

```bash
# PR Creation Options
--repo-path PATH          Repository path (default: current directory)
--base-branch BRANCH      Base branch for PR (default: main)
--pr-type TYPE            PR type (security_fix, code_quality, etc.)
--priority-strategy STRAT Priority strategy (severity_first, easy_win_first, etc.)
--template-standard STD   Template standard (conventional_commits, github_standard, etc.)
--no-deduplicate          Skip deduplication of issues
--auto-commit             Automatically commit changes
--auto-push               Automatically push branch
--create-pr               Create GitHub PR (requires gh CLI)
--dry-run                 Show what would be done without making changes
--labels LABELS           Additional labels for PR
--assignees ASSIGNEES     PR assignees
--reviewers REVIEWERS     PR reviewers
--output FILE             Output file for PR summary
```

### Example Workflow

1. **Run Multiple Scans**:
   ```bash
   python -m src.cli.main scan src/ --output security_scan.json
   python -m src.cli.main scan tests/ --output quality_scan.json
   python -m src.cli.main security-scan . --output compliance_scan.json
   ```

2. **Create Comprehensive PR**:
   ```bash
   python -m src.cli.main create-pr \
     security_scan.json quality_scan.json compliance_scan.json \
     --pr-type security_fix \
     --priority-strategy easy_win_first \
     --auto-commit \
     --create-pr \
     --labels "security" "ai-generated" \
     --assignees "security-team" \
     --reviewers "senior-dev"
   ```

3. **Review and Merge**:
   - AI-generated fixes are applied
   - Comprehensive PR description with issue summary
   - Review checklist for security fixes
   - Estimated time and complexity information

### Benefits

- **🚀 Faster Development**: Automatically create PRs with AI-generated fixes
- **🎯 Smart Prioritization**: Focus on high-impact, easy-win issues first
- **🔒 Security Focus**: Comprehensive security fix templates and testing
- **📊 Data-Driven**: Detailed analytics and integration statistics
- **🔄 Standardized Process**: Industry-standard templates and workflows
- **🤖 AI Enhancement**: Intelligent fix suggestions and complexity assessment

## 🛠 Installation

### Prerequisites
- Python 3.8 or higher
- Git
- AMD GPU with ROCm support (for GPU acceleration)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/ai-coder-assistant.git
   cd ai-coder-assistant
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install PyTorch with ROCm support (Recommended for AMD GPUs)**
   ```bash
   # For AMD GPUs with ROCm 6.3
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.3
   
   # Alternative: For CPU-only or NVIDIA GPUs
   # pip install torch torchvision torchaudio
   ```

4. **Install remaining dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

### GPU Support

#### AMD GPU (ROCm)
For optimal performance on AMD GPUs, install PyTorch with ROCm support:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.3
```

#### NVIDIA GPU (CUDA)
For NVIDIA GPUs, use the standard PyTorch installation:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### CPU Only
For CPU-only systems:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### LLM Studio Setup

After installation, you can set up LLM Studio to connect to multiple AI providers:

1. **Add API Keys**
   ```bash
   # OpenAI
   python -m src.cli.main llm-studio add-provider --provider openai --api-key "your-openai-key"
   
   # Google Gemini
   python -m src.cli.main llm-studio add-provider --provider google_gemini --api-key "your-gemini-key"
   
   # Claude (Anthropic)
   python -m src.cli.main llm-studio add-provider --provider claude --api-key "your-claude-key"
   ```

2. **Test Connections**
   ```bash
   python -m src.cli.main llm-studio test-provider --provider openai
   ```

3. **Start Chatting**
   ```bash
   python -m src.cli.main llm-studio chat --interactive
   ```

### Detailed Installation Guide

For comprehensive installation instructions, platform-specific setup, and troubleshooting, see the [Installation Guide](docs/installation_guide.md).

## 📦 **Building Optimized Binaries**

The AI Coder Assistant supports building **optimized, modular binaries** that are significantly smaller and faster than traditional single-binary approaches.

### **🎯 Build Benefits**
- **85-90% Size Reduction**: 20-30MB vs 150-200MB for traditional builds
- **75-80% Memory Reduction**: 100-200MB vs 500-800MB memory usage
- **70-80% Faster Startup**: 2-5 seconds vs 10-15 seconds startup time
- **Modular Architecture**: Separate binaries for different components

### **🚀 Quick Build**

#### **Windows**
```batch
# Run the Windows build script
build_windows.bat
```

#### **Linux**
```bash
# Make script executable and run
chmod +x build_linux.sh
./build_linux.sh
```

#### **macOS**
```bash
# Make script executable and run
chmod +x build_macos.sh
./build_macos.sh
```

#### **Docker**
```bash
# Build using Docker
docker-compose --profile build up
```

### **📋 Manual Build Process**
```bash
# Set up build environment
python -m venv build-env
source build-env/bin/activate  # Linux/macOS
# or build-env\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt pyinstaller

# Build all components
python build_all.py

# Or build specific component
python build_all.py --component core
```

### **📦 Build Output**
After successful build, you'll find optimized binaries in the `dist/` directory:
- `ai-coder-core` - Main GUI application
- `ai-coder-analyzer` - AI analysis engine
- `ai-coder-scanner` - Code scanner
- `ai-coder-web` - Web scraper
- `ai-coder-trainer` - Model trainer
- `ai-coder-launcher` - Component launcher

### **🚀 Running from Binary**
```bash
# Run main application
./dist/ai-coder-core

# Or use launcher
./dist/ai-coder-launcher core

# Run specific components
./dist/ai-coder-launcher analyzer --file main.py --language python
./dist/ai-coder-launcher scanner --path /path/to/code
```

### **📚 Detailed Build Documentation**
For comprehensive build instructions, troubleshooting, and advanced options, see:
- **[BUILD_README.md](BUILD_README.md)** - Complete build guide
- **[BUILD_PLAN.md](BUILD_PLAN.md)** - Technical architecture and optimization details

## 📖 Documentation

- **[User Manual](docs/user_manual.md)** - Complete guide to using the application
- **[Multi-Language Support](docs/multi_language_support.md)** - Language-specific setup and configuration
- **[Training Workflow](docs/training_workflow.md)** - Model training and optimization guide
- **[Build Instructions](BUILD_README.md)** - Binary build and distribution guide

## 🎯 Use Cases

### **Code Review & Quality Assurance**
- Automated code quality assessment across large codebases
- Intelligent detection of security vulnerabilities and code smells
- Multi-language project analysis with unified reporting

### **Development Workflow Enhancement**
- Real-time code analysis during development
- AI-powered code suggestions and improvements
- Learning from team feedback and corrections

### **Documentation & Training**
- Automated documentation processing and analysis
- Training data generation from existing codebases
- Custom model training for domain-specific code

### **Research & Analysis**
- Large-scale code analysis and pattern recognition
- Multi-repository code quality assessment
- Automated code review for research projects

## 🔧 Configuration

### **API Keys**
Configure your API keys in the application settings:
- OpenAI API Key for GPT-based analysis
- Gemini API Key for Google's AI analysis
- GitHub Personal Access Token for code acquisition

### **Model Settings**
- Choose between Ollama (local) and cloud-based AI models
- Configure model parameters and training settings
- Set up custom model export to Ollama

### **Performance Tuning**
- Adjust thread counts for different operations
- Configure memory usage and processing limits
- Optimize for your specific hardware configuration

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines and code of conduct.

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- PyQt6 for the GUI framework
- Ollama for local AI model support
- Hugging Face for model training infrastructure
- The open-source community for linter tools and libraries

## 🖥️ Command-Line Interface (CLI)

The AI Coder Assistant now includes a powerful CLI for code scanning, security analysis, and CI/CD integration.

### Usage Examples

```bash
# Scan entire codebase
python -m src.cli.main scan /path/to/code

# Scan only changed files (git diff)
python -m src.cli.main scan --changes-only /path/to/code

# Scan only files changed in a branch
python -m src.cli.main scan --branch main /path/to/code

# Analyze a single file
python -m src.cli.main analyze --file main.py --language python

# Security-focused scan (all security issues)
python -m src.cli.main security-scan /path/to/code

# Security scan with compliance filtering (OWASP, CWE, PCI, NIST, SOC2, ISO 27001, HIPAA, GDPR, SOX, FedRAMP, CIS, MITRE)
python -m src.cli.main security-scan /path/to/code --compliance owasp
python -m src.cli.main security-scan /path/to/code --compliance cwe
python -m src.cli.main security-scan /path/to/code --compliance pci
python -m src.cli.main security-scan /path/to/code --compliance nist
python -m src.cli.main security-scan /path/to/code --compliance soc2
python -m src.cli.main security-scan /path/to/code --compliance iso27001
python -m src.cli.main security-scan /path/to/code --compliance hipaa
python -m src.cli.main security-scan /path/to/code --compliance gdpr
python -m src.cli.main security-scan /path/to/code --compliance sox
python -m src.cli.main security-scan /path/to/code --compliance fedramp
python -m src.cli.main security-scan /path/to/code --compliance cis
python -m src.cli.main security-scan /path/to/code --compliance mitre

# Output results to JSON, CSV, HTML, Markdown, SARIF, or JUnit XML
python -m src.cli.main scan /path/to/code --output results.json --format json
python -m src.cli.main scan /path/to/code --output results.md --format markdown
python -m src.cli.main scan /path/to/code --output results.sarif --format sarif
python -m src.cli.main scan /path/to/code --output results.xml --format junit
```

### List Available AI Models
```bash
python -m src.cli.main models
```

### Configuration
```bash
python -m src.cli.main config --show
python -m src.cli.main config --set API_KEY your-key
```

## 🔄 CI/CD Integration

A sample GitHub Actions workflow is provided in `.github/workflows/security-scan.yml`:

```yaml
name: Security Scan
on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]
jobs:
  security-scan:
    runs-on: ubuntu-latest
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
      - name: Run AI Coder Security Scan
        run: |
          python -m src.cli.main security-scan . --output security_report.json --fail-on-critical
      - name: Upload Security Report
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: security_report.json
```

- The workflow will fail if critical security issues are found.
- Security reports are uploaded as artifacts for review.

## 🖥️ VS Code Extension

A VS Code extension is available in `ide/vscode/` for real-time code analysis:

### Installation
```bash
cd ide/vscode
npm install
npm run compile
```

### Features
- **Scan Current File**: Analyze the currently open file
- **Scan Workspace**: Scan entire workspace for issues  
- **Security Scan**: Run security-focused analysis

### Configuration
Set in VS Code settings:
```json
{
  "ai-coder-assistant.pythonPath": "python",
  "ai-coder-assistant.projectPath": "/path/to/ai-coder-assistant"
}
```

## 📢 Team Notifications

Send scan results to your team via Slack, Discord, or Microsoft Teams:

### Setup
```bash
# Set webhook URLs
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
export TEAMS_WEBHOOK_URL="https://your-org.webhook.office.com/..."
```

### Usage
```bash
# Send to Slack
python scripts/notify_team.py slack "Security scan completed - 5 critical issues found"

# Send to Discord
python scripts/notify_team.py discord scan_results.json

# Send to Microsoft Teams
python scripts/notify_team.py teams scan_results.json
```

## 🖥️ IDE Integration

### VS Code Extension
A VS Code extension is available in `ide/vscode/` for real-time code analysis:

#### Installation
```bash
cd ide/vscode
npm install
npm run compile
```

#### Features
- **Scan Current File**: Analyze the currently open file
- **Scan Workspace**: Scan entire workspace for issues  
- **Security Scan**: Run security-focused analysis

#### Configuration
Set in VS Code settings:
```json
{
  "ai-coder-assistant.pythonPath": "python",
  "ai-coder-assistant.projectPath": "/path/to/ai-coder-assistant"
}
```

### Vim/Neovim Integration
Vim and Neovim plugins are available in `ide/vim/` and `ide/neovim/`:

#### Vim Setup
```vim
" Add to your .vimrc
source ~/path/to/ai-coder-assistant/ide/vim/ai_coder.vim

" Set your project path
let g:ai_coder_project_path = '/path/to/ai-coder-assistant'
```

#### Neovim Setup
```lua
-- Add to your init.lua
require('ai_coder').setup({
    python_path = 'python',
    project_path = '/path/to/ai-coder-assistant'
})
```

#### Commands
- `:AICoderScanFile` - Scan current file
- `:AICoderScanWorkspace` - Scan entire workspace
- `:AICoderSecurityScan` - Security scan

#### Key Mappings
- `<leader>as` - Scan current file
- `<leader>aw` - Scan workspace
- `<leader>ass` - Security scan

### Emacs Integration
Emacs plugin is available in `ide/emacs/`:

#### Setup
```elisp
;; Add to your init.el
(load-file "~/path/to/ai-coder-assistant/ide/emacs/ai-coder.el")

;; Set configuration
(setq ai-coder-project-path "/path/to/ai-coder-assistant")
```

#### Commands
- `M-x ai-coder-scan-file` - Scan current file
- `M-x ai-coder-scan-workspace` - Scan workspace
- `M-x ai-coder-security-scan` - Security scan

#### Key Bindings
- `C-c a s` - Scan current file
- `C-c a w` - Scan workspace
- `C-c a S` - Security scan

### IntelliJ IDEA Plugin
IntelliJ IDEA plugin configuration is available in `ide/intellij/`:

#### Installation
1. Build the plugin from `ide/intellij/`
2. Install via IntelliJ IDEA plugin manager
3. Configure project path in settings

#### Features
- **Scan Current File**: Analyze the currently open file
- **Scan Project**: Analyze entire project
- **Security Scan**: Perform security-focused analysis
- **Compliance Check**: Check against compliance standards

#### Keyboard Shortcuts
- `Ctrl+Alt+S` - Scan current file
- `Ctrl+Alt+Shift+S` - Scan project
- `Ctrl+Alt+Shift+V` - Security scan
- `Ctrl+Alt+Shift+C` - Compliance check

## 🌐 REST API

A comprehensive REST API is available for programmatic access to all features:

### Installation
```bash
cd api
pip install -r requirements.txt
```

### Running the API
```bash
python api/main.py
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

### Authentication
All endpoints require Bearer token authentication:
```bash
curl -H "Authorization: Bearer your-token" http://localhost:8000/health
```

### Key Endpoints

#### Health Check
```bash
GET /health
```

#### Scan Code
```bash
POST /scan
{
  "path": "/path/to/code",
  "language": "python",
  "severity_filter": ["critical", "high"],
  "compliance": ["owasp", "cwe"],
  "output_format": "json"
}
```

#### Security Scan
```bash
POST /security-scan
{
  "path": "/path/to/code",
  "compliance": ["owasp", "pci", "nist"],
  "output_format": "sarif"
}
```

#### Analyze Single File
```bash
POST /analyze
{
  "file_path": "/path/to/file.py",
  "language": "python",
  "include_suggestions": true
}
```

#### Upload and Analyze
```bash
POST /upload-analyze
# Multipart form with file upload
```

#### Get Supported Languages
```bash
GET /languages
```

#### Get Compliance Standards
```bash
GET /compliance-standards
```

### API Response Format
```json
{
  "success": true,
  "message": "Scan completed successfully. Found 5 issues.",
  "results": [
    {
      "file_path": "src/main.py",
      "line_number": 15,
      "severity": "critical",
      "issue_type": "security_vulnerability",
      "description": "Hardcoded credentials detected",
      "suggestion": "Use environment variables",
      "compliance_standards": ["owasp", "cwe"]
    }
  ],
  "summary": {
    "total_issues": 5,
    "by_severity": {"critical": 2, "high": 3},
    "by_type": {"security_vulnerability": 5}
  },
  "timestamp": "2024-01-15T10:30:00",
  "scan_duration": 2.5
}
```

### Example Usage with curl
```bash
# Scan a directory
curl -X POST "http://localhost:8000/scan" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/project",
    "compliance": ["owasp", "cwe"],
    "output_format": "json"
  }'

# Security scan
curl -X POST "http://localhost:8000/security-scan" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/project",
    "compliance": ["pci", "nist"],
    "output_format": "sarif"
  }'
```

## 🔒 Compliance Standards

The AI Coder Assistant supports **12 major compliance standards**:

### Core Security Standards
- **OWASP Top 10**: Web application security risks
- **CWE**: Common Weakness Enumeration for software security
- **PCI DSS**: Payment Card Industry Data Security Standard
- **NIST Cybersecurity Framework**: Government cybersecurity best practices

### Enterprise Standards
- **SOC 2**: Service Organization Control 2 for cloud services
- **ISO 27001**: International information security management
- **HIPAA**: Health Insurance Portability and Accountability Act
- **GDPR**: General Data Protection Regulation (EU)
- **SOX**: Sarbanes-Oxley Act financial controls
- **FedRAMP**: Federal Risk and Authorization Management Program

### Advanced Security Frameworks
- **CIS Controls**: Center for Internet Security Controls
- **MITRE ATT&CK**: Adversarial Tactics, Techniques, and Common Knowledge

### Usage Examples
```bash
# Check against specific standards
python -m src.cli.main security-scan . --compliance owasp
python -m src.cli.main security-scan . --compliance gdpr
python -m src.cli.main security-scan . --compliance fedramp

# Check against multiple standards
python -m src.cli.main security-scan . --compliance owasp,cwe,pci

# Check all standards
python -m src.cli.main security-scan . --compliance all
```

## Features

### Core Features
- **AI-Powered Code Analysis**: Intelligent scanning and analysis of codebases
- **Security Scanning**: Comprehensive security vulnerability detection
- **Multi-Language Support**: Support for Python, JavaScript, TypeScript, Java, C++, Go, Rust, and more
- **Compliance Checking**: Built-in compliance standards (OWASP, CWE, MISRA, etc.)
- **AI-Generated Fixes**: Automatic generation of code fixes and improvements
- **Pull Request Creation**: AI-powered PR creation with industry-standard templates
- **LLM Studio**: Multi-provider AI model management and chat interface

### LLM Studio Features
- **Multi-Provider Support**: OpenAI, Google Gemini, Claude, and Ollama integration
- **Provider Management**: Add, configure, and test multiple AI providers
- **Model Selection**: Choose from available models with cost and capability information
- **Chat Interface**: Interactive chat with AI models
- **Fallback Support**: Automatic fallback between providers
- **Usage Tracking**: Monitor API usage and costs
- **GUI Integration**: Full integration with the main application interface

### Advanced Features
- **Intelligent Issue Prioritization**: AI-powered issue ranking and prioritization
- **Custom Compliance Standards**: Support for custom compliance frameworks
- **Batch Processing**: Process multiple files and directories
- **Export Formats**: Multiple output formats (JSON, SARIF, JUnit XML)
- **Training & Fine-tuning**: Custom model training capabilities
- **Browser Integration**: Web scraping and transcription features

### LLM Studio Commands

```bash
# Add a new provider
python -m src.cli.main llm-studio add-provider --provider openai --api-key "your-api-key"

# List configured providers
python -m src.cli.main llm-studio list-providers

# Test provider connection
python -m src.cli.main llm-studio test-provider --provider openai

# List available models
python -m src.cli.main llm-studio list-models

# Start interactive chat
python -m src.cli.main llm-studio chat --interactive

# Send a single message
python -m src.cli.main llm-studio chat --message "Hello, how are you?" --model "gpt-4"
```

### API Endpoints

#### Core Endpoints
```bash
# Health check
curl -X GET "http://localhost:8000/health" \
  -H "Authorization: Bearer your-token"

# Scan code
curl -X POST "http://localhost:8000/scan" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"path": "/path/to/code", "language": "python"}'

# Create PR from scan results
curl -X POST "http://localhost:8000/create-pr" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"scan_result_files": ["results1.json", "results2.json"], "pr_type": "security_fix"}'
```

#### LLM Studio API Endpoints
```bash
# Add provider
curl -X POST "http://localhost:8000/llm/providers/add" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"provider_type": "openai", "api_key": "your-api-key"}'

# List providers
curl -X GET "http://localhost:8000/llm/providers" \
  -H "Authorization: Bearer your-token"

# Test provider
curl -X POST "http://localhost:8000/llm/providers/test" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"provider_type": "openai", "api_key": "your-api-key"}'

# List models
curl -X GET "http://localhost:8000/llm/models" \
  -H "Authorization: Bearer your-token"

# Chat completion
curl -X POST "http://localhost:8000/llm/chat" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "model": "gpt-4"
  }'

# Get LLM config
curl -X GET "http://localhost:8000/llm/config" \
  -H "Authorization: Bearer your-token"
```

## GUI Usage

### Main Application
The AI Coder Assistant includes a comprehensive GUI built with PyQt6:

```bash
# Start the GUI
python main.py
```

The GUI includes several tabs:
- **AI Agent**: Code scanning and analysis
- **Data & Training**: Model training and data preprocessing
- **Browser & Transcription**: Web scraping and transcription
- **Export to Ollama**: Export models to Ollama format
- **LLM Studio**: Multi-provider AI model management and chat

### LLM Studio GUI
The LLM Studio is fully integrated into the main application:

1. **Access via Tab**: Click on the "LLM Studio" tab in the main window
2. **Access via Menu**: Use "LLM Studio" → "Open LLM Studio" from the menu bar
3. **Standalone Window**: LLM Studio can also be opened in a separate window

#### LLM Studio Features in GUI:
- **Provider Management**: Add, configure, and test AI providers
- **Model Selection**: Browse and select from available models
- **Chat Interface**: Interactive chat with AI models
- **Configuration**: Manage API keys and settings
- **Usage Monitoring**: Track API usage and costs

### GUI Features
- **Real-time Logging**: Live console output for all operations
- **Progress Tracking**: Visual progress indicators for long-running tasks
- **File Browser**: Integrated file selection dialogs
- **Settings Management**: Configure application settings
- **Report Generation**: Generate and view analysis reports

## Architecture

The codebase is now separated into:
- `src/frontend/`: All PyQt6 UI, dialogs, and user interaction logic
- `src/backend/`: All business logic, AI, data processing, and utility code

All frontend-backend imports use explicit relative paths (e.g. `from ...backend.services import ai_tools`).

See `ARCHITECTURE.md` for a detailed diagram and explanation.

## Testing

- Unit tests for every frontend-backend call are in `tests/frontend_backend/`.
- These tests use `unittest` and `unittest.mock` to verify that frontend code calls backend services, settings, and constants correctly.
- To run all tests:

```bash
python -m unittest discover tests
```

## Progress Dialogs and Threading

- All long-running operations use worker threads and progress dialogs.
- Progress bars are now fully responsive and update correctly for all tasks.

## Manuals and Documentation

- See `docs/user_manual.md` for user instructions.
- See `ARCHITECTURE.md` for developer architecture and integration details.

## 🕸️ Enhanced Web Scraping & Debug Logging

- **Configurable Depth & Link Limits**: Scrape web pages with user-defined depth, per-page link limits, and domain restrictions.
- **Detailed Logging**: Now logs all extracted links, which links are followed, and reasons for skipping (already visited, different domain, max depth, etc.).
- **Debugging**: To debug scraping, check the logs for lines like:
  - `Extracted X links from ...`
  - `FOLLOW: ...`
  - `SKIP: ...`
- **Usage**: Set scraping mode to "Enhanced (Follow Links)" and adjust `links_per_page`, `max_depth`, and `max_pages` as needed in the UI.

## 🛡️ Security, Maintainability, and Testing

- **Constants Usage**: All magic numbers replaced with named constants for maintainability and clarity.
- **Security Improvements**: SSL verification enabled by default, checks for hardcoded credentials, and secure API key management.
- **Performance Optimizations**: Reasonable file size and timeout limits, efficient thread management.
- **Industry-Standard Tests**: Comprehensive test suite covers imports, constants, web scraping, scanner, AI tools, security, performance, and code quality. Run with:
  ```bash
  python -m pytest tests/test_comprehensive.py -v
  ```
- **All features and tests pass, ensuring robust, secure, and maintainable code.**

---

**Experience the power of intelligent code analysis with multi-threading performance and optimized binaries!** 🚀