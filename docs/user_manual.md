# AI Coder Assistant - Complete User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Data Acquisition Tab](#data-acquisition-tab)
4. [AI Agent Tab](#ai-agent-tab)
5. [Browser & Transcription Tab](#browser--transcription-tab)
6. [Export to Ollama Tab](#export-to-ollama-tab)
7. [Multi-Language Support](#multi-language-support)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

## Introduction

The AI Coder Assistant is a comprehensive desktop application that provides intelligent code analysis, suggestions, and corrections across 20 programming languages. It combines static analysis tools with AI-powered suggestions to help you write better, more maintainable code.

### Key Concepts

- **Static Analysis**: Uses language-specific linters to find code issues
- **AI Suggestions**: Generates intelligent fixes using Ollama or custom models
- **Feedback Loop**: Learns from your corrections to improve future suggestions
- **Knowledge Base**: Builds context from documentation and your feedback
- **Multi-Language**: Supports 20 programming languages with appropriate tools

## Getting Started

### First Launch

1. **Start the application**: `python main.py`
2. **Check the log console**: Monitor for any initialization messages
3. **Verify Ollama connection**: If using Ollama, ensure the service is running
4. **Select your project**: Use the AI Agent tab to choose your code directory

### Initial Setup

1. **Add Documentation**: Use the Data Acquisition tab to add relevant documentation
2. **Preprocess Data**: Build your knowledge base with "Pre-process All Docs & Feedback"
3. **Configure Ignore Patterns**: Edit `.ai_coder_ignore` to exclude unwanted files
4. **Install Linters**: Install language-specific linters for full support

## Data Acquisition Tab

The Data Acquisition tab is where you build your knowledge base by adding documentation and training data.

### Local Files

**Purpose**: Import documentation from your local file system.

**How to use**:
1. Click "Select Local Docs Folder"
2. Choose a directory containing documentation files
3. Supported formats: `.txt`, `.md`, `.html`, `.pdf`
4. Files are automatically processed and added to your corpus

**Best practices**:
- Organize documentation in logical folders
- Include API references, tutorials, and best practices
- Use descriptive folder names for better organization

### Web Scraping

**Purpose**: Automatically extract content from web documentation.

**Enhanced Mode** (Recommended for documentation):
- **Max Pages**: 1-50 (default: 15) - Maximum pages to scrape per URL
- **Max Depth**: 1-10 (default: 4) - How deep to follow links
- **Same Domain Only**: Restricts crawling to the same website
- **Smart Navigation**: Follows pagination, next/previous links, and navigation menus

**Simple Mode** (For single pages):
- Scrapes only the main page content
- No link following
- Faster processing for basic content

**How to use**:
1. Enter URLs (one per line) in the text area
2. Select scraping mode (Enhanced or Simple)
3. Configure parameters as needed
4. Click "Scrape URLs and Add to Corpus"

**Example URLs**:
```
https://docs.python.org/3/library/os.html
https://reactjs.org/docs/getting-started.html
https://developer.mozilla.org/en-US/docs/Web/JavaScript
```

**Advanced Features**:
- **Content Detection**: Automatically identifies main content areas
- **Navigation Parsing**: Finds and follows relevant links
- **Duplicate Prevention**: Avoids scraping the same content twice
- **Error Recovery**: Continues processing even if some pages fail

### Preprocessing

**Purpose**: Prepare your data for AI training and knowledge base queries.

**Processing Modes**:
- **Reset and Re-process All**: Clears existing data and rebuilds from scratch
- **Accumulate New Data**: Adds new data to existing knowledge base

**What happens during preprocessing**:
1. **Text Extraction**: Converts documents to plain text
2. **Cleaning**: Removes formatting artifacts and noise
3. **Chunking**: Splits large documents into manageable pieces
4. **Vectorization**: Creates searchable embeddings (if FAISS available)
5. **Metadata Creation**: Tracks document sources and relationships

## AI Agent Tab

The AI Agent tab is the core of the application, providing code analysis and AI-powered suggestions.

### Model Selection

**Ollama Models**:
- **Refresh Models**: Updates the list of available Ollama models
- **Model Selection**: Choose the model for code analysis
- **Auto-detection**: Automatically detects running Ollama instances

**Own Trained Models**:
- **Load Model**: Load your custom trained model
- **Model Status**: Shows if a model is loaded and ready
- **Training Required**: Train models before using them

### Code Scanning

**Purpose**: Analyze your code for issues and generate AI suggestions.

**How to scan**:
1. **Select Directory**: Choose your project folder
2. **Configure Model**: Select Ollama or own model
3. **Start Scan**: Click "Scan Code for Issues"
4. **Monitor Progress**: Watch real-time progress updates
5. **Review Results**: Examine found issues and suggestions

**Supported Languages**:
- **Python**: Uses flake8 for analysis
- **JavaScript/TypeScript**: Uses ESLint
- **C/C++**: Uses cppcheck
- **Java**: Uses Checkstyle
- **Go**: Uses golangci-lint
- **Rust**: Uses cargo clippy
- **And 14 more languages...**

**Scan Results**:
- **Issue Count**: Total number of issues found
- **File Breakdown**: Issues per file
- **Severity Levels**: Different types of issues
- **AI Suggestions**: Generated fixes for each issue

### Interactive Review

**Purpose**: Review and apply AI suggestions with full control.

**Review Process**:
1. **Issue Display**: Shows the problematic code
2. **AI Suggestion**: Presents the proposed fix
3. **User Input**: You can modify the suggestion
4. **Decision**: Accept, reject, or modify the suggestion
5. **Learning**: Your feedback improves future suggestions

**Review Interface**:
- **Original Code**: Shows the current problematic code
- **Suggested Fix**: AI-generated correction
- **Explanation**: AI justification for the change
- **User Input**: Field to modify the suggestion
- **Action Buttons**: Accept, Reject, or Cancel

**Learning Integration**:
- **Feedback Storage**: Saves your corrections to learning data
- **Model Improvement**: Uses feedback to improve future suggestions
- **Pattern Recognition**: Learns your coding preferences

### Report Generation

**Purpose**: Create comprehensive reports of code analysis results.

**Report Types**:
- **Markdown Report**: Human-readable format with explanations
- **JSONL Training Data**: Machine-readable format for model training
- **Statistics**: Summary of issues and fixes

**Report Contents**:
- **File-by-file breakdown**: Issues organized by file
- **Code snippets**: Original and corrected code
- **AI explanations**: Justifications for each suggestion
- **Statistics**: Summary metrics and trends

## Browser & Transcription Tab

### Web Browser

**Purpose**: Integrated browser for quick access to online resources.

**Features**:
- **URL Navigation**: Direct URL input and navigation
- **Bookmark Support**: Save frequently visited pages
- **Search Integration**: Quick access to documentation
- **Resource Access**: View online documentation while coding

### YouTube Transcription

**Purpose**: Extract learning content from video tutorials.

**How to use**:
1. **Paste URL**: Enter a YouTube video URL
2. **Start Transcription**: Click "Transcribe Video Audio"
3. **Wait for Processing**: Monitor progress in the log
4. **Review Results**: Check the transcribed text
5. **Add to Corpus**: Use the transcription for learning

**Processing Options**:
- **Fast API**: Uses YouTube's transcript API when available
- **Local Fallback**: Uses Whisper for videos without transcripts
- **Quality Settings**: Configurable audio quality and processing

**Supported Formats**:
- **YouTube Videos**: Direct YouTube URLs
- **Audio Extraction**: Automatically extracts audio
- **Text Output**: Clean, formatted transcription

## Export to Ollama Tab

### Model Management

**Purpose**: Manage and export models to Ollama for private inference.

**Features**:
- **Model Discovery**: Automatically finds available Ollama models
- **Status Monitoring**: Shows model availability and status
- **Refresh Capability**: Updates model list in real-time

### Export Process

**Purpose**: Convert your trained models to Ollama format.

**Prerequisites**:
- **llama.cpp**: Must be cloned in the project directory
- **Ollama Service**: Must be running locally
- **Trained Model**: Must have a trained model to export

**Export Steps**:
1. **Select Model**: Choose the model to export
2. **Configure Settings**: Set export parameters
3. **Start Export**: Begin the conversion process
4. **Monitor Progress**: Watch conversion status
5. **Verify Results**: Check that the model is available in Ollama

**Export Options**:
- **Model Format**: GGUF format for Ollama compatibility
- **Quantization**: Various precision levels for size/performance trade-offs
- **Metadata**: Include model information and training data

### Knowledge Feedback

**Purpose**: Feed your learning data back to Ollama for continuous improvement.

**Feedback Loop**:
1. **Learning Data**: Accumulated from your corrections
2. **Model Training**: Uses feedback to improve the model
3. **Export Integration**: Feeds improved model back to Ollama
4. **Continuous Learning**: Ongoing improvement cycle

**Benefits**:
- **Personalized Suggestions**: Tailored to your coding style
- **Domain Expertise**: Learns from your specific projects
- **Privacy Preserved**: All learning happens locally
- **Continuous Improvement**: Gets better over time

## Multi-Language Support

### Supported Languages

The application supports 20 programming languages with appropriate linters:

| Language | Extensions | Linter | Installation |
|----------|------------|--------|--------------|
| Python | `.py`, `.pyw`, `.pyx`, `.pyi` | flake8 | `pip install flake8` |
| JavaScript | `.js`, `.jsx`, `.mjs` | eslint | `npm install -g eslint` |
| TypeScript | `.ts`, `.tsx` | eslint | `npm install -g eslint` |
| Java | `.java` | checkstyle | Download from Apache |
| C/C++ | `.c`, `.cpp`, `.h`, `.hpp` | cppcheck | Package manager |
| C# | `.cs` | dotnet | .NET SDK |
| Go | `.go` | golangci-lint | `go install` |
| Rust | `.rs` | cargo | `cargo install clippy` |
| PHP | `.php` | phpcs | `composer global require` |
| Ruby | `.rb` | rubocop | `gem install rubocop` |
| Swift | `.swift` | swiftlint | Homebrew |
| Kotlin | `.kt`, `.kts` | ktlint | Download binary |
| Scala | `.scala` | scalafmt | Coursier |
| Dart | `.dart` | dart | Dart SDK |
| R | `.r`, `.R` | lintr | `install.packages("lintr")` |
| MATLAB | `.m` | mlint | MATLAB installation |
| Shell | `.sh`, `.bash`, `.zsh` | shellcheck | Package manager |
| SQL | `.sql` | sqlfluff | `pip install sqlfluff` |
| HTML | `.html`, `.htm` | htmlhint | `npm install -g htmlhint` |

### Language Configuration

**Linter Installation**:
- **System-wide**: Install linters globally for all projects
- **Project-specific**: Use project-local linter configurations
- **Version Management**: Ensure compatible linter versions

**Configuration Files**:
- **ESLint**: `.eslintrc.js` or `.eslintrc.json`
- **Flake8**: `setup.cfg` or `pyproject.toml`
- **RuboCop**: `.rubocop.yml`
- **And more...**

### Ignore Patterns

**Purpose**: Exclude files and directories from analysis.

**Configuration**:
- **File**: `.ai_coder_ignore` in your project root
- **Syntax**: Gitignore-compatible patterns
- **Scope**: Applies to all supported languages

**Common Patterns**:
```
# Build artifacts
build/
dist/
*.o
*.exe

# Dependencies
node_modules/
vendor/
.venv/

# IDE files
.vscode/
.idea/
*.swp

# OS files
.DS_Store
Thumbs.db
```

## Advanced Features

### Custom Model Training

**Purpose**: Train models on your specific domain and coding style.

**Training Process**:
1. **Data Collection**: Gather documentation and feedback
2. **Preprocessing**: Clean and prepare training data
3. **Base Training**: Train on general documentation
4. **Fine-tuning**: Train on your specific feedback
5. **Export**: Convert to Ollama format

**Training Parameters**:
- **Model Size**: Balance between performance and resource usage
- **Training Epochs**: Number of training iterations
- **Learning Rate**: How quickly the model learns
- **Batch Size**: Number of examples per training step

### Knowledge Base Queries

**Purpose**: Query your documentation for context-aware suggestions.

**Query Types**:
- **Issue-based**: Find relevant documentation for specific issues
- **Context-aware**: Use surrounding code for better suggestions
- **Domain-specific**: Leverage your project's documentation

**Query Process**:
1. **Issue Analysis**: Extract key information from the code issue
2. **Documentation Search**: Find relevant documentation
3. **Context Integration**: Combine code and documentation context
4. **Suggestion Generation**: Create informed suggestions

### Performance Optimization

**Resource Management**:
- **Memory Usage**: Monitor and optimize memory consumption
- **Processing Speed**: Balance between speed and accuracy
- **GPU Utilization**: Use GPU acceleration when available
- **Batch Processing**: Process multiple files efficiently

**Caching**:
- **Model Caching**: Cache loaded models for faster access
- **Result Caching**: Cache analysis results for repeated scans
- **Documentation Caching**: Cache processed documentation

## Troubleshooting

### Common Issues

**Application Won't Start**:
- **Python Version**: Ensure Python 3.11 is installed
- **Dependencies**: Run `pip install -r requirements.txt`
- **Virtual Environment**: Activate your virtual environment
- **Permissions**: Check file and directory permissions

**Ollama Connection Issues**:
- **Service Status**: Ensure Ollama is running (`ollama serve`)
- **Model Availability**: Check if models are downloaded
- **Network Issues**: Verify local network connectivity
- **Port Conflicts**: Check for port conflicts on 11434

**Linter Not Found**:
- **Installation**: Install the required linter
- **PATH Issues**: Ensure linter is in your system PATH
- **Version Compatibility**: Check linter version compatibility
- **Configuration**: Verify linter configuration files

**Web Scraping Issues**:
- **Network Connectivity**: Check internet connection
- **Rate Limiting**: Some sites may block rapid requests
- **JavaScript Content**: Some content requires JavaScript execution
- **Robot.txt**: Respect site crawling policies

**Model Training Issues**:
- **Memory**: Ensure sufficient RAM for training
- **GPU**: Check GPU availability and drivers
- **Data Quality**: Verify training data quality
- **Configuration**: Check training parameters

### Performance Issues

**Slow Scanning**:
- **File Count**: Reduce the number of files scanned
- **Ignore Patterns**: Exclude unnecessary files
- **Linter Optimization**: Use faster linter configurations
- **Parallel Processing**: Enable parallel file processing

**Memory Problems**:
- **Model Size**: Use smaller models
- **Batch Processing**: Process files in smaller batches
- **Cache Management**: Clear unnecessary caches
- **Resource Monitoring**: Monitor system resources

**GPU Issues**:
- **Driver Updates**: Update GPU drivers
- **CUDA Installation**: Ensure proper CUDA installation
- **Memory Allocation**: Adjust GPU memory allocation
- **Fallback Options**: Use CPU fallback when needed

## Best Practices

### Data Management

**Documentation Organization**:
- **Logical Structure**: Organize documentation by topic
- **Version Control**: Keep documentation up to date
- **Quality Control**: Ensure documentation quality
- **Regular Updates**: Update documentation regularly

**Training Data**:
- **Diverse Sources**: Include various types of documentation
- **Quality Over Quantity**: Focus on high-quality content
- **Domain Relevance**: Include domain-specific documentation
- **Regular Feedback**: Continuously provide feedback

### Code Analysis

**Effective Scanning**:
- **Regular Scans**: Scan code regularly for issues
- **Incremental Analysis**: Focus on changed files
- **Context Awareness**: Consider project context
- **Team Standards**: Align with team coding standards

**Review Process**:
- **Thorough Review**: Carefully review all suggestions
- **Context Consideration**: Consider broader code context
- **Learning Integration**: Provide feedback for learning
- **Documentation**: Document accepted changes

### Model Management

**Model Selection**:
- **Task Appropriateness**: Choose models appropriate for your task
- **Performance Balance**: Balance accuracy and speed
- **Resource Constraints**: Consider available resources
- **Privacy Requirements**: Use local models for sensitive code

**Training Strategy**:
- **Incremental Training**: Train models incrementally
- **Feedback Integration**: Regularly integrate feedback
- **Validation**: Validate model performance
- **Backup Strategy**: Keep backups of trained models

### Security and Privacy

**Code Protection**:
- **Local Processing**: Keep code processing local
- **Ignore Sensitive Files**: Exclude sensitive files from analysis
- **Access Control**: Control access to the application
- **Audit Trails**: Maintain logs of analysis activities

**Data Privacy**:
- **No External Upload**: Ensure no code leaves your system
- **Local Storage**: Store all data locally
- **Encryption**: Encrypt sensitive training data
- **Access Logging**: Log access to sensitive data

---

This manual covers the complete functionality of the AI Coder Assistant. For specific technical details, refer to the individual documentation files in the `docs/` directory. 