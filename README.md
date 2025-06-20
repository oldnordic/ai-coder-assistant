# AI Coder Assistant v3.0.0

AI Coder Assistant is a comprehensive, enterprise-grade code analysis and development tool that helps you analyze, improve, and train code with the help of AI. It supports advanced code scanning, security intelligence, code standards enforcement, PR automation, and model training, all from a modern desktop interface.

## 📁 Project Structure

The AI Coder Assistant uses an organized file structure for better maintainability:

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

## 🔄 Major Architectural Improvements (v3.0.0)

### 🏗️ Modern Architecture
- **Event-Driven Design**: Inter-module communication via event bus with type safety
- **Modular Components**: Clear separation of concerns with independent services
- **Database Persistence**: SQLite-based persistence with connection pooling and retry logic
- **Performance Monitoring**: Integrated performance tracking across all services
- **Robust Error Handling**: Centralized error management with severity levels
- **Organized File Structure**: Clean separation of configuration and data files

### 🔧 Enhanced Infrastructure
- **Absolute Imports**: Standardized import paths using `src/` root for consistent module resolution
- **Core Services**: Config management, logging, error handling, threading, and event systems
- **Backend Services**: Scanner, model management, task management, and persistence services
- **Frontend Components**: PyQt6-based UI components with lifecycle management
- **Comprehensive Testing**: 92% test success rate with unit, integration, and performance tests

### 📊 Performance & Reliability
- **Database Optimization**: Connection pooling and query optimization
- **Memory Management**: Enhanced resource cleanup and garbage collection
- **Response Time Tracking**: Real-time performance metrics and alerts
- **Error Recovery**: Robust error handling and recovery mechanisms

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

## 🔒 Security Features

### 🔐 Secure API Key Management
AI Coder Assistant now includes enterprise-grade security features for managing sensitive configuration:

#### Environment-Based Secrets Management
- **Secure Storage**: API keys and sensitive data are stored in environment variables, not in configuration files
- **Dotenv Support**: Use `.env` files for local development (automatically loaded from project root)
- **System Integration**: Support for system environment variables for production deployments
- **Template System**: `env.template` file provides a starting point for configuration

#### Supported Environment Variables
```bash
# AI Provider API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
AZURE_API_KEY=your_azure_api_key_here
COHERE_API_KEY=your_cohere_api_key_here

# AWS Configuration
AWS_ACCESS_KEY=your_aws_access_key_here
AWS_SECRET_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1

# External Services
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@domain.com
JIRA_API_TOKEN=your_jira_api_token_here
JIRA_PROJECT_KEY=PROJ

SERVICENOW_BASE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your_username
SERVICENOW_API_TOKEN=your_servicenow_api_token_here
```

#### Settings Management GUI
- **Dedicated Settings Tab**: Complete GUI for managing API keys and configuration
- **Real-time Validation**: Instant feedback on configuration status
- **Secure Input**: Password fields for sensitive data entry
- **Environment Integration**: Direct integration with .env files
- **Template Creation**: Built-in .env template generation

#### Security Best Practices
1. **Never commit .env files** to version control
2. **Use system environment variables** for production deployments
3. **Regularly rotate API keys** and tokens
4. **Use minimum required permissions** for each service
5. **Enable auto-refresh** for security data updates

### 🛡️ Security Intelligence
- **CVE Monitoring**: Real-time vulnerability tracking and display
- **Security Breach Tracking**: Monitor and analyze security incidents
- **Patch Management**: Track and apply security patches
- **Code Security Analysis**: Automated security scanning of codebases
- **Dependency Vulnerability Scanning**: Identify vulnerable dependencies

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

### 3. Configure Security and API Keys
Set up your API keys and sensitive configuration securely:

#### Option A: Using .env file (Recommended for development)
```bash
# Copy the template and fill in your values
cp env.template .env
# Edit .env with your actual API keys and configuration
```

#### Option B: Using environment variables (Recommended for production)
```bash
# AI Provider API Keys
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export GOOGLE_API_KEY="your-google-api-key"

# External Services (if using PR automation)
export JIRA_BASE_URL="https://your-domain.atlassian.net"
export JIRA_USERNAME="your-email@domain.com"
export JIRA_API_TOKEN="your-jira-api-token"
export JIRA_PROJECT_KEY="PROJ"

export SERVICENOW_BASE_URL="https://your-instance.service-now.com"
export SERVICENOW_USERNAME="your-username"
export SERVICENOW_API_TOKEN="your-servicenow-api-token"
```

#### Option C: Using the Settings GUI
1. Start the application
2. Go to the "Settings" tab
3. Enter your API keys and configuration
4. Click "Save Settings" to create/update your .env file

### 4. Configure Application Settings (Optional)
Edit configuration files in the `config/` directory:

```bash
# LLM provider settings
vim config/llm_studio_config.json

# Code standards configuration
vim config/code_standards_config.json

# Security intelligence settings
vim config/security_intelligence_config.json

# PR automation settings
vim config/pr_automation_config.json
```

### 5. Run the application
```bash
# Set PYTHONPATH for proper module resolution
export PYTHONPATH=src
python src/main.py
```

### 6. Start PR Automation API Server (Optional)
```bash
# Start the API server for external integrations
export PYTHONPATH=src
python src/backend/services/web_server.py

# Access API documentation at http://localhost:8000/docs
```

## 🧪 Running Tests

The project includes a comprehensive test suite with the new architecture:

### Setup for Testing
**Linux/macOS:**
```bash
export PYTHONPATH=src
pytest -v
```

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH="src"
pytest -v
```

**Windows (CMD):**
```cmd
set PYTHONPATH=src
pytest -v
```

### Test Coverage
- **Core Modules**: Config, error handling, logging, threading, events (100% pass rate)
- **Backend Services**: Scanner, model management, task management, persistence
- **Frontend Components**: UI components with event-driven architecture
- **Integration Tests**: Frontend-backend communication and data flow
- **Performance Tests**: Database operations and service performance

### Test Features
- **Cross-platform compatibility**: Works on Linux, macOS, and Windows
- **Async/await support**: Professional testing of async operations
- **Comprehensive mocking**: Robust mocking of external dependencies
- **Timeout mechanisms**: Prevents test hangs and infinite loops
- **Debug capabilities**: Built-in debugging and logging

For detailed testing information, see [Test Suite Guide](docs/test_suite_guide.md).

## 🏗️ Building from Source

### Prerequisites
- Python 3.8+
- PyInstaller
- UPX (optional, for binary optimization)

### Build Commands
```bash
# Set PYTHONPATH
export PYTHONPATH=src

# Build all components
python build_all.py

# Build specific component
python build_all.py --component assistant
python build_all.py --component cli
python build_all.py --component api
```

### Platform-Specific Builds
```bash
# Linux
./build_linux.sh

# macOS
./build_macos.sh

# Windows
build_windows.bat
```

## 📚 Documentation

The AI Coder Assistant includes comprehensive documentation that has been updated to reflect the new organized file structure:

### 📁 File Organization
- **`config/`**: All configuration files (JSON format)
  - `code_standards_config.json`: Code standards and rules
  - `llm_studio_config.json`: LLM provider settings
  - `pr_automation_config.json`: PR automation configuration
  - `security_intelligence_config.json`: Security feed settings
- **`data/`**: All data storage files (JSON format)
  - `security_breaches.json`: Security breach information
  - `security_patches.json`: Security patch data
  - `security_training_data.json`: Security training datasets
  - `security_vulnerabilities.json`: Security vulnerability data

### 📖 Updated Documentation
- **[Architecture Guide](docs/ARCHITECTURE.md)**: Complete system architecture with new file structure
- **[Installation Guide](docs/installation_guide.md)**: Setup instructions with organized file structure
- **[User Manual](docs/user_manual.md)**: Comprehensive user guide with updated paths
- **[Test Suite Guide](docs/test_suite_guide.md)**: Testing instructions with new file organization
- **[Cloud Model Integration](docs/cloud_model_integration_guide.md)**: Multi-provider LLM setup
- **[Advanced Refactoring](docs/advanced_refactoring_guide.md)**: Code refactoring with organized config
- **[Multi-Language Support](docs/multi_language_support.md)**: 20+ language support documentation
- **[Training Workflow](docs/training_workflow.md)**: Model training and Ollama integration
- **[Security Intelligence](docs/security_intelligence_guide.md)**: Security monitoring and analysis
- **[PR Automation](docs/pr_automation_guide.md)**: Automated pull request management
- **[Code Standards](docs/code_standards_guide.md)**: Code quality enforcement
- **[Provider System](docs/provider_system_guide.md)**: LLM provider management

### 🔧 Configuration Management
All configuration is now centralized and organized:
```bash
# View all configuration files
ls config/

# Edit specific configurations
vim config/llm_studio_config.json
vim config/code_standards_config.json
vim config/security_intelligence_config.json
vim config/pr_automation_config.json
```

## 🧪 Running Tests

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
