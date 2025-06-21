# AI Coder Assistant - User Manual

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [User Interface](#user-interface)
5. [Core Features](#core-features)
6. [Advanced Features](#advanced-features)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [API Reference](#api-reference)
10. [Contributing](#contributing)

## Overview

AI Coder Assistant is a comprehensive AI-powered code analysis and development tool that combines static analysis, security scanning, code quality assessment, and intelligent suggestions. Built with modern Python technologies and a robust architecture, it provides both GUI and CLI interfaces for maximum flexibility.

### Key Features

- **🔍 Intelligent Code Analysis**: AI-powered code review and suggestions
- **🛡️ Security Scanning**: Comprehensive security vulnerability detection
- **📊 Code Quality Assessment**: Standards compliance and best practices
- **🤖 AI Model Integration**: Support for multiple LLM providers
- **🔄 Continuous Learning**: Adaptive model improvement
- **📈 Performance Monitoring**: Real-time system and application metrics
- **🌐 Multi-Language Support**: Python, JavaScript, Java, C++, and more
- **🔧 Refactoring Tools**: Automated code improvement suggestions
- **📋 PR Automation**: Automated pull request analysis and generation
- **🎯 Code Standards**: Configurable coding standards enforcement

### System Requirements

- **Operating System**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.11 or 3.12
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 2GB free space
- **GPU**: Optional (NVIDIA CUDA for enhanced AI processing)

## Installation

### Method 1: Poetry Installation (Recommended)

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Clone the repository
git clone https://github.com/aicoder/ai-coder-assistant.git
cd ai-coder-assistant

# Install dependencies
poetry install --with dev

# Activate virtual environment
poetry shell
```

### Method 2: Docker Installation

```bash
# Clone the repository
git clone https://github.com/aicoder/ai-coder-assistant.git
cd ai-coder-assistant

# Run with Docker Compose
docker-compose up -d ai-coder-assistant

# For development
docker-compose --profile dev up -d ai-coder-dev
```

### Method 3: Binary Distribution

Download the latest release from GitHub and extract to your preferred location.

## Quick Start

### 1. Launch the Application

```bash
# Using Poetry
poetry run python -m src.main

# Using Python directly
python -m src.main

# Using Docker
docker-compose up ai-coder-assistant
```

### 2. Initial Setup

1. **Welcome Screen**: The application will display a welcome screen with setup options
2. **Configuration**: Choose your preferred settings or use defaults
3. **Model Selection**: Select AI models for analysis (local or cloud-based)
4. **Directory Setup**: Configure your project directories

### 3. First Scan

1. **Select Directory**: Choose a code directory to analyze
2. **Configure Scan**: Select analysis options (security, quality, standards)
3. **Run Analysis**: Click "Start Scan" to begin analysis
4. **Review Results**: Examine the generated report and suggestions

## User Interface

### Main Window Layout

The main application window is organized into several key areas:

#### 1. **Menu Bar**
- **File**: Open projects, save reports, export results
- **Edit**: Copy, paste, find, replace
- **View**: Toggle panels, themes, zoom
- **Tools**: Access various analysis tools
- **Help**: Documentation, about, updates

#### 2. **Toolbar**
- **Quick Actions**: Start scan, stop, pause, save
- **View Controls**: Toggle panels, zoom, theme
- **Status Indicators**: Connection status, model status

#### 3. **Tab System**
The application uses a tabbed interface for different functionalities:

##### **AI Analysis Tab**
- **Quick Scan**: Fast local analysis
- **AI Enhancement**: Deep AI-powered analysis
- **Model Selection**: Choose AI models
- **Results Display**: Analysis results and suggestions

##### **Scanner Tab**
- **Directory Selection**: Choose code directories
- **Scan Configuration**: Configure scan parameters
- **Progress Tracking**: Real-time scan progress
- **Results Management**: View and manage scan results

##### **Security Intelligence Tab**
- **Vulnerability Scanning**: Security analysis
- **Compliance Checking**: Standards compliance
- **Threat Assessment**: Risk evaluation
- **Security Reports**: Detailed security reports

##### **Code Standards Tab**
- **Standards Configuration**: Define coding standards
- **Compliance Checking**: Verify code compliance
- **Style Analysis**: Code style assessment
- **Best Practices**: Best practice recommendations

##### **Performance Optimization Tab**
- **Performance Analysis**: Code performance assessment
- **Optimization Suggestions**: Performance improvements
- **Benchmarking**: Performance benchmarking
- **Resource Monitoring**: System resource tracking

##### **Continuous Learning Tab**
- **Learning Configuration**: Set up learning parameters
- **Model Training**: Train custom models
- **Feedback Integration**: User feedback processing
- **Model Management**: Manage trained models

##### **PR Management Tab**
- **PR Analysis**: Pull request analysis
- **Automated Reviews**: Automated code reviews
- **Review Generation**: Generate review comments
- **Integration**: Git integration

##### **Refactoring Tab**
- **Refactoring Suggestions**: Code refactoring recommendations
- **Automated Refactoring**: Automated code improvements
- **Refactoring History**: Track refactoring changes
- **Quality Metrics**: Code quality metrics

##### **Collaboration Tab**
- **Team Management**: Team collaboration features
- **Code Sharing**: Share code and results
- **Review Workflow**: Code review workflow
- **Communication**: Team communication tools

##### **Settings Tab**
- **General Settings**: Application preferences
- **Model Configuration**: AI model settings
- **Security Settings**: Security preferences
- **Advanced Options**: Advanced configuration

##### **Model Manager Tab**
- **Model Installation**: Install AI models
- **Model Configuration**: Configure model parameters
- **Model Performance**: Monitor model performance
- **Model Updates**: Update models

##### **Cloud Models Tab**
- **Cloud Provider Setup**: Configure cloud providers
- **Model Selection**: Select cloud-based models
- **API Configuration**: API key management
- **Usage Monitoring**: Monitor API usage

##### **Web Server Tab**
- **Server Configuration**: Configure web server
- **API Management**: Manage API endpoints
- **Access Control**: Control server access
- **Monitoring**: Server monitoring

##### **Advanced Analytics Tab**
- **Analytics Dashboard**: Comprehensive analytics
- **Trend Analysis**: Code quality trends
- **Performance Metrics**: Detailed performance data
- **Custom Reports**: Generate custom reports

#### 4. **Status Bar**
- **Connection Status**: AI model connection status
- **Scan Progress**: Current scan progress
- **System Status**: System resource usage
- **Notifications**: Important notifications

### Navigation

#### **Keyboard Shortcuts**
- `Ctrl+N`: New project
- `Ctrl+O`: Open project
- `Ctrl+S`: Save project
- `Ctrl+Z`: Undo
- `Ctrl+Y`: Redo
- `Ctrl+F`: Find
- `Ctrl+R`: Replace
- `F5`: Refresh
- `Ctrl+Tab`: Switch tabs
- `Ctrl+W`: Close tab
- `F1`: Help

#### **Mouse Navigation**
- **Left Click**: Select items, activate buttons
- **Right Click**: Context menus
- **Double Click**: Open files, expand items
- **Drag & Drop**: Move items, reorganize panels

## Core Features

### 1. Intelligent Code Analysis

The AI Analysis tab provides two main analysis modes:

#### **Quick Scan**
- **Purpose**: Fast local analysis without AI enhancement
- **Use Case**: Initial code review, quick quality check
- **Features**:
  - Static analysis
  - Basic code quality assessment
  - Syntax checking
  - Style analysis
  - Performance indicators

#### **AI Enhancement**
- **Purpose**: Deep AI-powered analysis with intelligent suggestions
- **Use Case**: Comprehensive code review, detailed analysis
- **Features**:
  - AI-powered code review
  - Intelligent suggestions
  - Best practice recommendations
  - Security analysis
  - Performance optimization suggestions

#### **Model Selection**
- **Local Models**: Ollama, local LLMs
- **Cloud Models**: OpenAI, Anthropic, Google
- **Custom Models**: User-trained models

### 2. Code Scanning

The Scanner tab provides comprehensive code analysis:

#### **Directory Selection**
- **Browse**: Select directories manually
- **Recent**: Quick access to recent directories
- **Favorites**: Save frequently used directories
- **Drag & Drop**: Drag directories directly

#### **Scan Configuration**
- **File Types**: Select file types to scan
- **Exclusions**: Exclude specific files/directories
- **Depth**: Configure scan depth
- **Parallel Processing**: Enable/disable parallel scanning

#### **Scan Types**
- **Full Scan**: Complete codebase analysis
- **Incremental Scan**: Scan only changed files
- **Targeted Scan**: Scan specific files/directories
- **Quick Scan**: Fast surface-level analysis

### 3. Security Intelligence

The Security Intelligence tab provides comprehensive security analysis:

#### **Vulnerability Scanning**
- **SAST Analysis**: Static Application Security Testing
- **Dependency Scanning**: Third-party dependency analysis
- **Configuration Analysis**: Security configuration review
- **Compliance Checking**: Security compliance verification

#### **Security Standards**
- **OWASP Top 10**: OWASP security standards
- **CWE**: Common Weakness Enumeration
- **NIST**: National Institute of Standards
- **ISO 27001**: Information security management
- **SOC2**: Service Organization Control 2
- **HIPAA**: Health Insurance Portability and Accountability Act

### 4. Code Standards

The Code Standards tab enforces coding standards:

#### **Standards Configuration**
- **Language-Specific**: Different standards for different languages
- **Custom Rules**: User-defined coding rules
- **Industry Standards**: Industry-specific standards
- **Team Standards**: Team-specific standards

#### **Compliance Checking**
- **Style Compliance**: Code style verification
- **Best Practices**: Best practice compliance
- **Documentation**: Documentation standards
- **Testing**: Testing standards

### 5. Performance Optimization

The Performance Optimization tab analyzes and optimizes code performance:

#### **Performance Analysis**
- **Code Complexity**: Cyclomatic complexity analysis
- **Memory Usage**: Memory usage analysis
- **Execution Time**: Performance profiling
- **Resource Usage**: Resource consumption analysis

#### **Optimization Suggestions**
- **Algorithm Optimization**: Algorithm improvement suggestions
- **Memory Optimization**: Memory usage optimization
- **I/O Optimization**: Input/output optimization
- **Parallelization**: Parallel processing opportunities

## Advanced Features

### 1. Continuous Learning

The Continuous Learning tab enables adaptive model improvement:

#### **Learning Configuration**
- **Learning Rate**: Configure learning parameters
- **Feedback Integration**: User feedback processing
- **Model Updates**: Automatic model updates
- **Quality Metrics**: Learning quality assessment

#### **Model Training**
- **Custom Training**: Train custom models
- **Fine-tuning**: Fine-tune existing models
- **Transfer Learning**: Transfer learning capabilities
- **Model Evaluation**: Model performance evaluation

### 2. PR Management

The PR Management tab provides automated pull request analysis:

#### **PR Analysis**
- **Automated Reviews**: Automated code reviews
- **Review Generation**: Generate review comments
- **Quality Assessment**: PR quality assessment
- **Integration**: Git integration

#### **Review Workflow**
- **Review Templates**: Customizable review templates
- **Review Assignment**: Automated review assignment
- **Review Tracking**: Track review progress
- **Review History**: Review history management

### 3. Refactoring Tools

The Refactoring tab provides automated refactoring capabilities:

#### **Refactoring Suggestions**
- **Code Smells**: Detect code smells
- **Refactoring Opportunities**: Identify refactoring opportunities
- **Best Practices**: Suggest best practices
- **Code Quality**: Improve code quality

#### **Automated Refactoring**
- **Safe Refactoring**: Safe automated refactoring
- **Refactoring Preview**: Preview refactoring changes
- **Refactoring History**: Track refactoring changes
- **Rollback**: Rollback refactoring changes

#### **Autonomous Refactoring System**
- **🏗️ Analyze Architecture**: Comprehensive AST-based architectural analysis
- **AI-Powered Suggestions**: AI-generated refactoring recommendations
- **Iterative Self-Correction**: Automatic learning and improvement from failures
- **Containerized Testing**: Safe, isolated testing environment for all changes
- **Continuous Learning**: Every automation attempt improves future performance

### 4. Autonomous Refactoring and Learning

The AI Coder Assistant now features an advanced autonomous refactoring and learning system that can automatically analyze, fix, and improve code with minimal human intervention.

#### **Dual-Trigger Automation**

##### **Reactive Fix (Issue-Specific)**
- **Security Intelligence Tab**: "🚀 Automate Fix" buttons on each vulnerability
- **Scan Results Table**: "🚀 Automate Fix" buttons on each issue
- **Targeted Remediation**: Creates specific goals for each issue
- **AI Code Generation**: Uses fine-tuned codeollama models for intelligent fixes
- **Containerized Testing**: Validates all changes in isolated environment
- **Learning Integration**: Captures results for continuous improvement

##### **Proactive Refactor (Architectural)**
- **Refactoring Tab**: "🏗️ Analyze Architecture" button
- **Comprehensive Analysis**: AST-based code architecture analysis
- **Architectural Issues**: Detects high coupling, low cohesion, circular dependencies
- **SOLID Violations**: Identifies design principle violations
- **AI-Enhanced Suggestions**: Generates high-level refactoring recommendations
- **User Approval Workflow**: Review and approve suggestions before implementation

#### **Iterative Self-Correction Loop**

The system uses a sophisticated iterative loop that continuously improves:

1. **Analysis Phase**: Analyzes codebase, understands goals, retrieves relevant knowledge
2. **Code Generation Phase**: Creates context-aware AI prompts and generates fixes
3. **Application Phase**: Safely applies changes with workspace locking and backups
4. **Testing Phase**: Runs comprehensive tests in containerized environment
5. **Learning Phase**: Creates learning examples and improves future performance

#### **Learning System**

##### **Knowledge Sources**
- **Code Scanners**: SAST results, linter output, static analysis
- **User Interactions**: Manual fixes, approved/rejected suggestions, feedback
- **Web/YouTube Content**: Tutorials, best practices, code examples
- **Project Rules**: Coding standards, configuration files, documentation

##### **Continuous Improvement**
- **Unified Knowledge Base**: Specialized data adapters for each source
- **Model Fine-tuning**: Continuous model improvement with new knowledge
- **Performance Tracking**: Success/failure statistics and learning metrics
- **Quality Assessment**: Example quality evaluation and filtering

#### **Configuration**

##### **System Settings**
```json
{
  "max_iterations": 5,
  "test_timeout": 300,
  "build_timeout": 600,
  "create_backup": true,
  "run_tests": true,
  "enable_learning": true
}
```

##### **Learning Configuration**
```json
{
  "learning_rate": 0.001,
  "batch_size": 32,
  "max_examples": 10000,
  "confidence_threshold": 0.7,
  "auto_finetune": true,
  "finetune_interval": 100
}
```

#### **Usage Workflow**

##### **Getting Started**
1. Open Settings Tab → "Autonomous Features"
2. Enable "Autonomous Refactoring"
3. Configure learning preferences
4. Set up Docker for containerized testing

##### **Using Reactive Fix**
1. Open Security Intelligence Tab or scan results
2. Click "🚀 Automate Fix" on specific issues
3. Review confirmation dialog
4. Monitor automation progress
5. Review results and apply if satisfied

##### **Using Proactive Refactor**
1. Open Refactoring Tab
2. Select project directory
3. Click "🏗️ Analyze Architecture"
4. Review architectural suggestions
5. Select suggestions to implement
6. Monitor automation progress

#### **Safety Features**
- **Workspace Locking**: Prevents conflicts during automation
- **Automatic Backups**: Creates backups before applying changes
- **Containerized Testing**: Isolated testing environment
- **Progress Tracking**: Real-time monitoring of automation progress
- **Rollback Capability**: Ability to revert changes if needed

### 5. Collaboration Features

The Collaboration tab enables team collaboration:

#### **Team Management**
- **User Management**: Manage team members
- **Role Assignment**: Assign user roles
- **Permission Management**: Manage user permissions
- **Team Analytics**: Team performance analytics

#### **Code Sharing**
- **Code Snippets**: Share code snippets
- **Analysis Results**: Share analysis results
- **Best Practices**: Share best practices
- **Knowledge Base**: Team knowledge base

### 6. Model Management

The Model Manager tab manages AI models:

#### **Model Installation**
- **Local Models**: Install local models
- **Cloud Models**: Configure cloud models
- **Custom Models**: Install custom models
- **Model Updates**: Update models

#### **Model Configuration**
- **Model Parameters**: Configure model parameters
- **Performance Tuning**: Tune model performance
- **Resource Allocation**: Allocate resources
- **Model Testing**: Test model performance

## Configuration

### Application Settings

Access settings through the Settings tab:

#### **General Settings**
- **Theme**: Light/Dark theme selection
- **Language**: Application language
- **Auto-save**: Auto-save configuration
- **Notifications**: Notification preferences

#### **Model Configuration**
- **Default Models**: Set default AI models
- **API Keys**: Manage API keys
- **Model Parameters**: Configure model parameters
- **Resource Limits**: Set resource limits

#### **Security Settings**
- **Authentication**: Authentication configuration
- **Encryption**: Data encryption settings
- **Access Control**: Access control settings
- **Audit Logging**: Audit logging configuration

### Configuration Files

The application uses several configuration files:

#### **Main Configuration**
- **Location**: `config/` directory
- **Format**: JSON
- **Files**:
  - `llm_studio_config.json`: LLM configuration
  - `code_standards_config.json`: Code standards
  - `security_intelligence_config.json`: Security settings
  - `pr_automation_config.json`: PR automation
  - `local_code_reviewer_config.json`: Local code reviewer

#### **User Configuration**
- **Location**: `~/.ai_coder_assistant/`
- **Format**: JSON
- **Files**:
  - `config.json`: User preferences
  - `models.json`: Model configurations
  - `projects.json`: Project history

### Environment Variables

The application supports environment variables:

```bash
# API Configuration
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"

# Application Configuration
export AI_CODER_LOG_LEVEL="INFO"
export AI_CODER_DATA_DIR="/path/to/data"
export AI_CODER_CACHE_DIR="/path/to/cache"

# Docker Configuration
export AI_CODER_DOCKER_ENABLED="true"
export AI_CODER_DOCKER_IMAGE="ai-coder-assistant:latest"
```

## Troubleshooting

### Common Issues

#### **Application Won't Start**
1. **Check Python Version**: Ensure Python 3.11+ is installed
2. **Check Dependencies**: Run `poetry install`
3. **Check Permissions**: Ensure write permissions to data directories
4. **Check Logs**: Review log files in `logs/` directory

#### **AI Models Not Working**
1. **Check API Keys**: Verify API keys are configured
2. **Check Internet**: Ensure internet connection
3. **Check Model Status**: Verify model availability
4. **Check Resources**: Ensure sufficient system resources

#### **Scan Results Empty**
1. **Check Directory**: Verify directory contains code files
2. **Check File Types**: Ensure supported file types
3. **Check Permissions**: Verify read permissions
4. **Check Configuration**: Review scan configuration

#### **Performance Issues**
1. **Check Resources**: Monitor CPU, memory, disk usage
2. **Check Configuration**: Review performance settings
3. **Check Logs**: Review performance logs
4. **Restart Application**: Restart the application

### Log Files

Log files are located in the `logs/` directory:

- **application.log**: Main application log
- **error.log**: Error log
- **performance.log**: Performance log
- **security.log**: Security log
- **ai.log**: AI model log

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set debug environment variable
export AI_CODER_DEBUG="true"

# Or modify configuration
# In config/config.json
{
  "debug": true,
  "log_level": "DEBUG"
}
```

### Support

For additional support:

1. **Documentation**: Check the documentation in `docs/`
2. **Issues**: Report issues on GitHub
3. **Discussions**: Join discussions on GitHub
4. **Email**: Contact support team

## API Reference

### REST API

The application provides a REST API for integration:

#### **Base URL**
```
http://localhost:8000/api/v1
```

#### **Authentication**
```bash
# API Key authentication
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8000/api/v1/health
```

#### **Endpoints**

##### **Health Check**
```bash
GET /health
```

##### **Scan Code**
```bash
POST /scan
Content-Type: application/json

{
  "directory": "/path/to/code",
  "options": {
    "security": true,
    "quality": true,
    "standards": true
  }
}
```

##### **Get Scan Results**
```bash
GET /scan/{scan_id}/results
```

##### **Analyze File**
```bash
POST /analyze
Content-Type: application/json

{
  "file": "/path/to/file.py",
  "language": "python",
  "options": {
    "ai_enhancement": true
  }
}
```

### Python API

The application provides a Python API:

```python
from src.backend.services.scanner import ScannerService
from src.backend.services.intelligent_analyzer import IntelligentCodeAnalyzer

# Initialize services
scanner = ScannerService()
analyzer = IntelligentCodeAnalyzer()

# Scan directory
results = scanner.scan_directory("/path/to/code")

# Analyze file
analysis = analyzer.analyze_file("/path/to/file.py")
```

### CLI Interface

The application provides a command-line interface:

```bash
# Scan directory
python -m src.cli.main scan --directory /path/to/code

# Analyze file
python -m src.cli.main analyze --file /path/to/file.py

# Security scan
python -m src.cli.main security --directory /path/to/code

# Generate report
python -m src.cli.main report --scan-id 123 --format html
```

## Contributing

### Development Setup

1. **Fork Repository**: Fork the repository on GitHub
2. **Clone Repository**: Clone your fork locally
3. **Install Dependencies**: Run `poetry install --with dev`
4. **Create Branch**: Create a feature branch
5. **Make Changes**: Make your changes
6. **Run Tests**: Run `poetry run pytest`
7. **Submit PR**: Submit a pull request

### Code Style

The project follows PEP 8 style guidelines:

```bash
# Format code
poetry run black src/
poetry run isort src/

# Lint code
poetry run flake8 src/
poetry run mypy src/
```

### Testing

Run the test suite:

```bash
# Run all tests
poetry run pytest

# Run specific tests
poetry run pytest tests/test_scanner.py

# Run with coverage
poetry run pytest --cov=src --cov-report=html
```

### Documentation

Update documentation when making changes:

1. **User Manual**: Update `docs/user_manual.md`
2. **API Documentation**: Update API documentation
3. **Code Comments**: Add/update code comments
4. **README**: Update README if needed

---

**Last Updated**: June 2025  
**Version**: 1.0  
**Compatibility**: AI Coder Assistant v2.0+ 