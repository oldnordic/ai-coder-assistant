# AI Coder Assistant v2.6.0

AI Coder Assistant is a comprehensive, enterprise-grade code analysis and development tool that helps you analyze, improve, and train code with the help of AI. It supports advanced code scanning, security intelligence, code standards enforcement, PR automation, and model training, all from a modern desktop interface.

## 🚀 Main Features

### 🤖 AI & Code Analysis
- **Unified LLM Provider System**: Support for OpenAI, Anthropic, Google AI, and local Ollama models
- **Automatic Failover**: Seamless switching between providers for reliability
- **Cost Optimization**: Built-in cost tracking and provider management
- **Intelligent Code Analysis**: Multi-language support (20+ languages)
- **Advanced Refactoring**: AST-based code transformation and improvement
- **Continuous Learning**: Real-time model improvement with user feedback

### 🔒 Security & Standards
- **Security Intelligence**: Track security vulnerabilities, breaches, and patches
- **Code Standards Enforcement**: Enforce company-specific coding standards and quality rules
- **Real-time Security Monitoring**: RSS feed integration for CVE monitoring
- **Automated Patch Management**: Track and apply security patches
- **Training Data Generation**: AI security awareness training data

### 🚀 Automation & Integration
- **PR Automation**: Automated PR creation with JIRA and ServiceNow integration
- **REST API**: Full API for external integrations and CI/CD pipelines
- **Git Integration**: Automated branch creation, commits, and pushing
- **Service Integration**: Multi-instance JIRA and ServiceNow support
- **Template System**: Customizable PR templates with variable substitution

### 🏠 Local & Remote Management
- **Remote Ollama Support**: Connect to multiple local and remote Ollama instances
- **Authentication & Security**: Bearer tokens, custom headers, and SSL configuration
- **Health Monitoring**: Automated instance health checks and model listing
- **Instance Management**: Add, remove, and configure multiple Ollama instances

### 📊 Performance & Analytics
- **Performance Optimization**: Real-time system metrics and code performance analysis
- **Advanced Analytics**: Developer metrics, trends analysis, and custom reports
- **Benchmarking**: Function benchmarking and optimization recommendations
- **System Monitoring**: CPU, Memory, Disk I/O, and Network monitoring

### 🤝 Collaboration & Web
- **Collaboration Features**: Team chat, code sharing, and project management
- **Web Server Mode**: FastAPI-based web interface for remote access
- **Multi-user Support**: WebSocket-based real-time collaboration
- **Cross-platform Access**: Browser-based interface for any device

### 📚 Data & Training
- **Document Processing**: PDF, HTML, and text document processing
- **Custom Model Training**: Local training and continuous learning from feedback
- **Web Scraping**: Automated data acquisition from web sources
- **Data Management**: Comprehensive data preprocessing and corpus building

### 🖥️ Modern UI
- **Professional Interface**: PyQt6-based desktop application
- **Dark Theme**: Consistent dark theme across all components
- **Comprehensive Tabs**: 15+ specialized tabs for different functionalities
- **Real-time Updates**: Live data updates and progress monitoring

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/oldnordic/ai-coder-assistant.git
cd ai-coder-assistant
```

### 2. Set up a virtual environment and install dependencies
#### Linux & macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
#### Windows
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure LLM Providers (Optional)
Set up your API keys for cloud providers:

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Google AI
export GOOGLE_API_KEY="your-google-api-key"

# Ollama (for local models)
export OLLAMA_BASE_URL="http://localhost:11434"
```

### 4. Run the application
```bash
python main.py
```

### 5. Start PR Automation API Server (Optional)
```bash
# Start the API server for external integrations
python run_api_server.py

# Access API documentation at http://localhost:8000/docs
```

## 🧪 Running Tests

The project includes a professional test suite with cross-platform compatibility:

### Setup for Testing
**Linux/macOS:**
```bash
export PYTHONPATH="$PYTHONPATH:$(pwd)/src"
pytest -v
```

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH="$env:PYTHONPATH;$(Get-Location)\src"
pytest -v
```

**Windows (CMD):**
```cmd
set PYTHONPATH=%PYTHONPATH%;%CD%\src
pytest -v
```

### Test Features
- **Cross-platform compatibility**: Works on Linux, macOS, and Windows
- **Async/await support**: Professional testing of async operations
- **Comprehensive mocking**: Robust mocking of external dependencies
- **Timeout mechanisms**: Prevents test hangs and infinite loops
- **Debug capabilities**: Built-in debugging and logging

For detailed testing information, see [Test Suite Guide](docs/test_suite_guide.md).

## 📚 Complete Documentation

### Core Documentation
- [User Manual](docs/user_manual.md) - Complete feature guide
- [Installation Guide](docs/installation_guide.md) - Detailed setup instructions
- [Provider System Guide](docs/provider_system_guide.md) - LLM provider configuration and usage
- [Test Suite Guide](docs/test_suite_guide.md) - Testing setup and best practices
- [Remote Ollama Guide](docs/ollama_remote_guide.md) - Remote Ollama instance configuration
- [PR Automation Guide](docs/pr_automation_guide.md) - PR automation and external integrations
- [Security Intelligence Guide](docs/security_intelligence_guide.md) - Security vulnerability tracking and management
- [Code Standards Guide](docs/code_standards_guide.md) - Company-specific coding standards enforcement

### Advanced Features
- [Training Workflow](docs/training_workflow.md) - Custom model training
- [Multi-Language Support](docs/multi_language_support.md) - Language-specific features
- [Advanced Refactoring Guide](docs/advanced_refactoring_guide.md) - Code refactoring capabilities
- [Cloud Model Integration Guide](docs/cloud_models_section.md) - Cloud provider setup

### Architecture & Development
- [Architecture Documentation](docs/ARCHITECTURE.md) - System design and components
- [Build Instructions](docs/BUILD_README.md) - Building from source
- [Cloud Model Integration](docs/cloud_model_integration_guide.md) - Advanced provider setup

## 🚀 PR Automation System

The PR Automation System provides comprehensive automation for creating Pull Requests with integrated JIRA and ServiceNow ticket management:

### Key Features
- **🔧 Service Integration**: JIRA and ServiceNow with multi-instance support
- **📝 PR Templates**: Customizable templates with variable substitution
- **🚀 Automated PR Creation**: Git integration with GitHub CLI
- **🌐 REST API**: Full API for external integrations and CI/CD
- **🖥️ GUI Management**: User-friendly interface for configuration

### Quick PR Automation Setup

1. **Start the API Server**:
   ```bash
   python run_api_server.py
   ```

2. **Configure Services** (via API or GUI):
   ```bash
   # Add JIRA service
   curl -X POST "http://localhost:8000/api/services" \
     -H "Content-Type: application/json" \
     -d '{
       "service_type": "jira",
       "name": "JIRA-Prod",
       "base_url": "https://company.atlassian.net",
       "username": "your-email@company.com",
       "api_token": "your-api-token",
       "project_key": "PROJ"
     }'
   ```

3. **Create PR Templates**:
   ```bash
   curl -X POST "http://localhost:8000/api/templates" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Feature Template",
       "title_template": "feat: {title}",
       "body_template": "## Description\n{description}\n\n## JIRA Ticket\n{jira_ticket}",
       "branch_prefix": "feature/",
       "is_default": true
     }'
   ```

4. **Create PRs**:
   ```bash
   curl -X POST "http://localhost:8000/api/pr/create" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Add authentication feature",
       "description": "Implement OAuth2 authentication",
       "repo_path": "/path/to/repo",
       "auto_create_tickets": true
     }'
   ```

For complete PR automation documentation, see [PR Automation Guide](docs/pr_automation_guide.md).

## 🔒 Security Intelligence System

The Security Intelligence System provides comprehensive security monitoring and vulnerability tracking:

### Key Features
- **🔍 Vulnerability Tracking**: Real-time CVE monitoring and analysis
- **🚨 Breach Detection**: Security breach monitoring and analysis
- **🛠️ Patch Management**: Automated patch tracking and application
- **📡 RSS Feed Integration**: Multi-source security intelligence aggregation
- **🤖 AI Training Data**: Security awareness training data generation
- **📊 Export Capabilities**: Training data export for AI model enhancement

### Quick Security Setup

1. **Access Security Intelligence Tab**: Open the Security Intelligence tab in the main application
2. **Configure Security Feeds**: Add RSS feeds for CVE monitoring and security news
3. **Monitor Vulnerabilities**: View real-time vulnerability data and severity levels
4. **Track Patches**: Monitor security patches and mark them as applied
5. **Export Training Data**: Generate training data for AI security awareness

For complete security intelligence documentation, see [Security Intelligence Guide](docs/security_intelligence_guide.md).

## 📋 Code Standards Enforcement

The Code Standards Enforcement system provides company-specific coding standards and quality control:

### Key Features
- **🏢 Company Standards**: Define and manage company-specific coding standards
- **🔍 Multi-language Analysis**: Support for Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, PHP, Ruby
- **⚡ Real-time Analysis**: Live code analysis with violation detection
- **🔧 Auto-fix Capabilities**: Automatic fixing of common code violations
- **📊 Severity Management**: Error, Warning, and Info level violations
- **📁 Import/Export**: Standards import and export functionality

### Quick Code Standards Setup

1. **Access Code Standards Tab**: Open the Code Standards tab in the main application
2. **Create Standards**: Define company-specific coding standards and rules
3. **Analyze Code**: Analyze files or directories for violations
4. **Auto-fix Violations**: Automatically fix common code violations
5. **Export Standards**: Share standards across teams and projects

For complete code standards documentation, see [Code Standards Guide](docs/code_standards_guide.md).

## 🏗️ Architecture

### Unified Provider System
The AI Coder Assistant uses a unified provider system that eliminates vendor lock-in:

- **Single Interface**: Consistent API across all providers
- **Automatic Failover**: Seamless switching between providers
- **Cost Tracking**: Real-time usage monitoring and optimization
- **Health Monitoring**: Automated provider health checks
- **Local Support**: Ollama integration for offline usage

### Backend Services
- **Cloud Models Service**: Multi-provider LLM integration with failover
- **Refactoring Service**: Advanced code refactoring engine
- **Scanner Service**: Code analysis and scanning
- **Training Service**: Model training and fine-tuning
- **Acquisition Service**: Web scraping and data collection
- **Continuous Learning Service**: Adaptive learning system
- **Security Intelligence Service**: Vulnerability tracking and breach monitoring
- **Code Standards Service**: Company-specific coding standards enforcement
- **PR Automation Service**: Automated pull request creation and management
- **Performance Optimization Service**: System metrics and code performance analysis
- **Web Server Service**: FastAPI-based web interface and REST API
- **Collaboration Service**: Team collaboration and project management

### Frontend Components
- **PyQt6 UI**: Modern desktop interface with 15+ specialized tabs
- **Cloud Models Tab**: Provider management and monitoring
- **Refactoring Tab**: Advanced refactoring interface
- **Data Tab**: Training and data management
- **AI Tab**: Code analysis and suggestions
- **Browser Tab**: Web integration
- **CLI Module**: Command-line interface
- **PR Management Tab**: PR automation and service integration
- **Security Intelligence Tab**: Security monitoring and vulnerability tracking
- **Code Standards Tab**: Code standards enforcement and analysis
- **Ollama Manager Tab**: Remote Ollama instance management
- **Performance Optimization Tab**: System and code performance analysis
- **Web Server Tab**: Web server configuration and management
- **Advanced Analytics Tab**: Developer metrics and insights
- **Collaboration Tab**: Team collaboration and project management

## 🎯 Key Advantages

1. **Multi-Provider Support**: Not locked into a single AI provider
2. **Cost Control**: Built-in cost tracking and optimization
3. **Local Training**: Can train custom models locally
4. **Advanced Features**: More comprehensive than competitors
5. **Security Intelligence**: Real-time security monitoring and vulnerability tracking
6. **Code Standards**: Company-specific coding standards enforcement
7. **PR Automation**: Automated pull request creation with external service integration
8. **Performance Optimization**: Comprehensive performance analysis and optimization
9. **Web Server Mode**: Web-based interface for remote access
10. **Collaboration**: Team collaboration and project management tools
11. **Open Source**: Full transparency and customization
12. **Self-Hosted**: Complete privacy and control

## 📊 Implementation Status

### ✅ Completed Features (19/21) - 90.5% Complete
- All core AI and code analysis features
- Security intelligence and monitoring
- Code standards enforcement
- PR automation with external service integration
- Performance optimization and analytics
- Web server mode and collaboration features
- Ollama remote management
- Comprehensive documentation and guides

### 🔄 Planned Features (2/21)
- IDE Plugin Support (VS Code, JetBrains)
- Security Scanning Microservice (Bandit, Semgrep)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- PyQt6 for the modern desktop interface
- OpenAI, Anthropic, and Google for AI capabilities
- Ollama for local model support
- The open-source community for inspiration and tools
# Trigger CI pipeline
