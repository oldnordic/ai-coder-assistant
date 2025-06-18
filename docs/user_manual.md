# AI Coder Assistant - Complete User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Data Acquisition Tab](#data-acquisition-tab)
4. [AI Agent Tab](#ai-agent-tab)
5. [Advanced Refactoring Tab](#advanced-refactoring-tab)
6. [Cloud Models Tab](#cloud-models-tab)
7. [Browser & Transcription Tab](#browser--transcription-tab)
8. [Export to Ollama Tab](#export-to-ollama-tab)
9. [Multi-Language Support](#multi-language-support)
10. [Advanced Features](#advanced-features)
11. [Building Optimized Binaries](#building-optimized-binaries)
12. [Troubleshooting](#troubleshooting)
13. [Best Practices](#best-practices)
14. [Application Structure](#application-structure)
15. [How the UI Connects to Backend Logic](#how-the-ui-connects-to-backend-logic)
16. [Testing Frontend-Backend Integration](#testing-frontend-backend-integration)
17. [Progress Bars and Responsiveness](#progress-bars-and-responsiveness)
18. [Further Reading](#further-reading)

## Introduction

The AI Coder Assistant is a comprehensive desktop application that provides **intelligent code analysis**, AI-powered suggestions, and automated code improvement across 20 programming languages. It goes far beyond simple linter errors to analyze code logic, patterns, security vulnerabilities, and maintainability issues.

### Key Concepts

- **Intelligent Analysis**: Analyzes code logic, patterns, and context beyond syntax errors
- **Security Scanning**: Detects hardcoded credentials, SQL injection risks, and vulnerabilities
- **Performance Analysis**: Identifies inefficient patterns and performance bottlenecks
- **Code Smell Detection**: Finds anti-patterns, magic numbers, and maintainability issues
- **AI Suggestions**: Generates intelligent fixes using Ollama or custom models
- **Feedback Loop**: Learns from your corrections to improve future suggestions
- **Multi-Language**: Supports 20 programming languages with intelligent analysis

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
4. **Install Linters**: Install language-specific linters for enhanced analysis (optional)

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

### Debug Logging for Web Scraping

When using Enhanced Web Scraping, the application now provides detailed debug logs to help you understand and troubleshoot the crawling process:

- **Extracted Links**: Logs all links found on each page.
- **Followed Links**: Logs which links are being followed for further scraping.
- **Skipped Links**: Logs reasons for skipping links (already visited, different domain, max depth reached, etc.).

**How to use:**
- Check the log console or output for lines like:
  - `Extracted X links from ...`
  - `FOLLOW: ...`
  - `SKIP: ...`
- Use these logs to verify that the scraper is finding and following the expected links, or to diagnose why certain links are not being followed.

### Preprocessing

**Purpose**: Prepare your data for AI training and knowledge base queries.

**Processing Modes**:
- **Reset and Re-process All**: Clears existing data and rebuilds from scratch
- **Accumulate New Data**: Adds new data to existing knowledge base

**What happens during preprocessing**:
1. **Text Extraction**: Converts documents to plain text
2. **Cleaning**: Removes formatting artifacts and noise
3. **Chunking**: Splits large documents into manageable pieces
4. **Metadata Creation**: Tracks document sources and relationships

## AI Agent Tab

The AI Agent tab is the core of the application, providing **intelligent code analysis** and AI-powered suggestions.

### Model Selection

**Ollama Models**:
- **Refresh Models**: Updates the list of available Ollama models
- **Model Selection**: Choose the model for code analysis
- **Auto-detection**: Automatically detects running Ollama instances

**Own Trained Models**:
- **Load Model**: Load your custom trained model
- **Model Status**: Shows if a model is loaded and ready
- **Training Required**: Train models before using them

### Intelligent Code Analysis

**Purpose**: Perform comprehensive analysis of your code beyond simple linter errors.

**What the intelligent analysis detects**:

#### 🔒 Security Vulnerabilities
- **Hardcoded Credentials**: Passwords, API keys, tokens in code
- **SQL Injection Risks**: Unsafe database queries with user input
- **Security Anti-patterns**: Dangerous practices and vulnerabilities

#### ⚡ Performance Issues
- **Inefficient Algorithms**: Nested loops, O(n²) complexity
- **Memory Leaks**: Resource management problems
- **Performance Anti-patterns**: Slow code patterns and bottlenecks

#### 🧹 Code Smells
- **Magic Numbers**: Unnamed constants in code
- **Bare Except Clauses**: Generic exception handling
- **Anti-patterns**: Poor coding practices and smells

#### 🏗️ Maintainability Issues
- **Complex Functions**: High cyclomatic complexity
- **Long Functions**: Functions with too many lines
- **Poor Documentation**: Missing or inadequate comments
- **TODO/FIXME Comments**: Unresolved action items

#### 📚 Best Practice Violations
- **Language-specific Issues**: Violations of language best practices
- **Style Violations**: Inconsistent coding style
- **Architecture Problems**: Poor code organization

#### 🔧 Linter Errors
- **Syntax Errors**: Language-specific syntax issues
- **Style Issues**: Code formatting and style violations
- **Potential Bugs**: Issues detected by language linters

**How to scan**:
1. **Select Directory**: Choose your project folder
2. **Configure Model**: Select Ollama or own model
3. **Start Intelligent Scan**: Click "Start Scan"
4. **Monitor Progress**: Watch real-time analysis progress
5. **Review Results**: Examine comprehensive issue analysis

**Analysis Process**:
1. **File Discovery**: Identifies all supported code files
2. **Language Detection**: Determines language for each file
3. **Linter Integration**: Runs language-specific linters (if available)
4. **Intelligent Analysis**: Performs deep code analysis
5. **Issue Classification**: Categorizes issues by type and severity
6. **AI Enhancement**: Generates intelligent suggestions for each issue

### Issue Classification

**Issue Types**:
- **Logic Errors**: Problems with code logic and flow
- **Performance Issues**: Inefficient code patterns
- **Security Vulnerabilities**: Security-related problems
- **Code Smells**: Anti-patterns and poor practices
- **Maintainability Issues**: Code organization problems
- **Documentation Issues**: Missing or poor documentation
- **Best Practice Violations**: Language-specific violations
- **Linter Errors**: Traditional linter-detected issues

**Severity Levels**:
- **Critical**: Must-fix issues (security vulnerabilities, critical bugs)
- **High**: Important issues (performance problems, major code smells)
- **Medium**: Moderate issues (maintainability, style violations)
- **Low**: Minor issues (documentation, minor style issues)

### Scan Results and Summary

**Comprehensive Summary**:
- **Total Issues**: Complete count of all detected issues
- **Languages Analyzed**: Number of programming languages scanned
- **Issues by Type**: Breakdown of issues by category
- **Issues by Severity**: Prioritized list by importance
- **Critical Issues**: Highlighted critical problems requiring immediate attention

**Example Summary**:
```
=== INTELLIGENT CODE ANALYSIS COMPLETE ===

Total Issues Found: 23
Languages Analyzed: 3

Issues by Type:
  • Code Smell: 8
  • Security Vulnerability: 3
  • Performance Issue: 2
  • Maintainability Issue: 7
  • Linter Error: 3

Issues by Severity:
  • Critical: 2
  • High: 5
  • Medium: 12
  • Low: 4

🚨 CRITICAL ISSUES (2):
  1. src/auth.py:15 - Hardcoded API key detected
  2. src/database.py:42 - SQL injection vulnerability

📋 RECOMMENDATIONS:
  • Address security vulnerabilities immediately
  • Optimize performance-critical code sections
  • Improve code maintainability and documentation
```

### Interactive Review

**Purpose**: Review and apply AI suggestions with full control and context.

**Enhanced Review Interface**:
- **Issue Information**: Type, severity, file location, and language
- **Context Display**: Additional context and background information
- **Code Snippet**: Original problematic code
- **AI Suggestion**: Intelligent improvement proposal
- **AI Explanation**: Detailed analysis and justification
- **User Feedback**: Field to modify or provide alternative solutions

**Review Process**:
1. **Issue Overview**: Review issue type, severity, and context
2. **Code Analysis**: Examine the problematic code snippet
3. **AI Suggestion**: Review the proposed improvement
4. **AI Explanation**: Understand the reasoning behind the suggestion
5. **User Input**: Modify the suggestion if needed
6. **Decision**: Accept, reject, or modify the suggestion
7. **Learning**: Your feedback improves future suggestions

**Learning Integration**:
- **Feedback Storage**: Saves your corrections to learning data
- **Model Improvement**: Uses feedback to improve future suggestions
- **Pattern Recognition**: Learns your coding preferences and style

### Report Generation

**Purpose**: Create comprehensive reports of intelligent analysis results.

**Report Types**:
- **Markdown Report**: Human-readable format with detailed explanations
- **JSONL Training Data**: Machine-readable format for model training
- **Statistics**: Summary of issues, fixes, and trends

**Report Contents**:
- **Executive Summary**: High-level overview of findings
- **Issue Breakdown**: Detailed analysis by file and type
- **Code Snippets**: Original and corrected code examples
- **AI Explanations**: Justifications for each suggestion
- **Recommendations**: Prioritized action items
- **Statistics**: Summary metrics and improvement trends

## Advanced Refactoring Tab

The Advanced Refactoring tab provides **comprehensive automated refactoring capabilities** with multi-language support, safety features, and intelligent suggestion management.

### Overview

**Purpose**: Automatically identify and apply code refactoring opportunities to improve code quality, maintainability, and readability.

**Key Features**:
- **Multi-language Support**: Python, JavaScript, TypeScript, Java, C++
- **AST-based Analysis**: Accurate Python code parsing and transformation
- **Pattern-based Refactoring**: Efficient JavaScript/TypeScript analysis
- **Safety-first Approach**: Backup creation, validation, and rollback mechanisms
- **Preview System**: View changes before applying them
- **Progress Tracking**: Real-time progress updates for long operations

### Getting Started

**Initial Setup**:
1. **Select Project**: Choose the project directory to analyze
2. **Configure Languages**: Select languages to analyze (default: all supported)
3. **Start Analysis**: Click "Analyze Project" to begin refactoring opportunity detection
4. **Review Suggestions**: Examine the list of refactoring opportunities
5. **Apply Refactoring**: Preview and apply selected refactoring operations

### Project Analysis

**Analysis Process**:
1. **File Discovery**: Automatically finds all source files in the project
2. **Language Detection**: Identifies programming language for each file
3. **Pattern Analysis**: Applies language-specific refactoring patterns
4. **Opportunity Detection**: Identifies refactoring opportunities
5. **Suggestion Grouping**: Groups related refactoring operations
6. **Priority Ranking**: Sorts suggestions by impact and priority

**Supported File Types**:
- **Python**: `.py`, `.pyw`, `.pyx`, `.pyi`
- **JavaScript**: `.js`, `.jsx`, `.mjs`
- **TypeScript**: `.ts`, `.tsx`
- **Java**: `.java`
- **C/C++**: `.c`, `.cpp`, `.cc`, `.cxx`, `.h`, `.hpp`

### Refactoring Suggestions

**Suggestion Types**:

#### **Extract Method**
- **Purpose**: Break down long functions into smaller, focused methods
- **Detection**: Functions with 30+ lines or high cyclomatic complexity
- **Benefits**: Improved readability, testability, and maintainability
- **Example**: Split a 50-line function into 3 smaller, focused methods

#### **Extract Class**
- **Purpose**: Split large classes into smaller, more focused classes
- **Detection**: Classes with 100+ lines or 15+ methods
- **Benefits**: Better separation of concerns, reduced coupling
- **Example**: Extract utility methods into a separate helper class

#### **Extract Constant**
- **Purpose**: Replace magic numbers with named constants
- **Detection**: Numbers >= 1000 or frequently used values
- **Benefits**: Improved readability and maintainability
- **Example**: Replace `86400` with `SECONDS_PER_DAY`

#### **Remove Unused Imports**
- **Purpose**: Clean up unused import statements
- **Detection**: Imported modules not used in the file
- **Benefits**: Cleaner code, faster imports, reduced dependencies
- **Example**: Remove unused `os` import from a file

#### **Inline Variable**
- **Purpose**: Simplify single-use variables
- **Detection**: Variables used only once in return statements
- **Benefits**: Reduced code complexity and line count
- **Example**: Inline `result = calculate()` in `return result`

### Suggestion Management

**Filtering Options**:
- **Priority**: High, Medium, Low
- **Category**: Performance, Maintainability, Readability, Architecture
- **Language**: Filter by specific programming languages
- **Impact Score**: Filter by estimated impact (0.0 to 1.0)

**Suggestion Information**:
- **Title**: Clear description of the refactoring opportunity
- **Description**: Detailed explanation of the issue and solution
- **Priority**: Importance level (High, Medium, Low)
- **Category**: Type of improvement (Performance, Maintainability, etc.)
- **Impact Score**: Estimated improvement impact (0.0 to 1.0)
- **Estimated Time**: Time required to apply the refactoring
- **Operations**: List of individual refactoring operations

**Example Suggestion**:
```
Title: Extract method from 'process_data' function
Description: Function 'process_data' is 45 lines long and can be broken down into smaller methods
Priority: Medium
Category: Maintainability
Impact Score: 0.7
Estimated Time: 10-15 minutes
Operations: 1 refactoring operation
```

### Preview System

**Purpose**: View detailed changes before applying refactoring operations.

**Preview Features**:
- **File Changes**: List of files that will be modified
- **Operations**: Individual refactoring operations within each file
- **Diff View**: Side-by-side comparison of original and refactored code
- **Summary**: Overview of changes (lines added, removed, files modified)

**How to Preview**:
1. **Select Suggestion**: Choose a refactoring suggestion from the list
2. **Click Preview**: Click "Preview Changes" button
3. **Review Changes**: Examine the diff view and file changes
4. **Understand Impact**: Review the summary of modifications
5. **Make Decision**: Decide whether to apply or skip the refactoring

**Preview Dialog Features**:
- **Summary Panel**: High-level overview of changes
- **File Tree**: Hierarchical view of modified files
- **Diff Viewer**: Detailed code comparison with syntax highlighting
- **Operation Details**: Information about each refactoring operation

### Applying Refactoring

**Safety Features**:
- **Automatic Backup**: Creates backup files before applying changes
- **Validation**: Pre-application validation of all changes
- **Confirmation**: User confirmation for destructive operations
- **Rollback**: Ability to revert changes if needed

**Application Process**:
1. **Select Suggestion**: Choose the refactoring suggestion to apply
2. **Preview Changes**: Review the proposed modifications
3. **Confirm Application**: Click "Apply Refactoring" with backup option
4. **Monitor Progress**: Watch real-time progress updates
5. **Review Results**: Check the application results and any warnings

**Backup Options**:
- **Create Backup**: Automatically create `.backup` files
- **Backup Location**: Same directory as original files
- **Backup Naming**: `filename.py.backup`
- **Backup Verification**: Confirm backup files were created successfully

**Application Results**:
- **Success Count**: Number of operations applied successfully
- **Modified Files**: List of files that were changed
- **Backup Files**: List of backup files created
- **Warnings**: Any issues or warnings during application
- **Errors**: Any errors that prevented application

### Supported Languages

#### **Python**
- **AST-based Analysis**: Uses Python's Abstract Syntax Tree for accurate parsing
- **Function Analysis**: Detects long functions and high complexity
- **Class Analysis**: Identifies large classes and method counts
- **Import Analysis**: Finds unused imports and circular dependencies
- **Magic Numbers**: Detects hardcoded numbers that should be constants

**Python-specific Features**:
- **Cyclomatic Complexity**: Calculates function complexity scores
- **AST Parsing**: Accurate code structure analysis
- **Import Tracking**: Monitors import usage across files
- **Type Hints**: Respects type annotations and hints

#### **JavaScript/TypeScript**
- **Pattern-based Analysis**: Uses regex patterns for code detection
- **Function Detection**: Identifies long functions and complex logic
- **Class Analysis**: Finds large classes and method counts
- **Variable Analysis**: Detects unused variables and magic numbers

**JavaScript/TypeScript Features**:
- **ES6+ Support**: Modern JavaScript features and syntax
- **TypeScript Integration**: TypeScript-specific analysis
- **Module Analysis**: ES6 module import/export tracking
- **Async/Await**: Async function complexity analysis

#### **Java & C++**
- **Framework Ready**: Extensible architecture for additional languages
- **Pattern Matching**: Language-specific pattern detection
- **File Analysis**: Basic file structure and size analysis
- **Future Enhancement**: Planned for full language support

### Best Practices

#### **Before Refactoring**
1. **Version Control**: Ensure your code is committed to version control
2. **Backup Creation**: Always enable backup creation for safety
3. **Test Coverage**: Have good test coverage before refactoring
4. **Review Changes**: Always preview changes before applying
5. **Start Small**: Begin with low-risk refactoring operations

#### **During Refactoring**
1. **Monitor Progress**: Watch progress indicators during application
2. **Check Results**: Review application results and any warnings
3. **Verify Changes**: Test your code after refactoring
4. **Run Tests**: Execute your test suite to ensure functionality
5. **Review Code**: Manually review the refactored code

#### **After Refactoring**
1. **Test Thoroughly**: Run comprehensive tests on refactored code
2. **Review Performance**: Check if refactoring improved performance
3. **Update Documentation**: Update any affected documentation
4. **Commit Changes**: Commit refactored code to version control
5. **Monitor Issues**: Watch for any issues introduced by refactoring

### Troubleshooting

#### **Common Issues**

**Analysis Fails**:
- **Check File Permissions**: Ensure read access to project files
- **Verify Language Support**: Confirm language is supported
- **Check File Size**: Large files may exceed processing limits
- **Review Logs**: Check log console for error messages

**Preview Not Working**:
- **File Access**: Ensure write access for temporary files
- **Memory Issues**: Large projects may require more memory
- **Syntax Errors**: Files with syntax errors may not preview correctly
- **Encoding Issues**: Check file encoding (UTF-8 recommended)

**Application Fails**:
- **Backup Issues**: Ensure backup creation is enabled
- **File Locks**: Close files in other applications
- **Permission Errors**: Check write permissions for project directory
- **Disk Space**: Ensure sufficient disk space for backups

#### **Performance Optimization**

**Large Projects**:
- **Filter Languages**: Analyze only relevant languages
- **Use Filters**: Apply priority and category filters
- **Batch Operations**: Apply refactoring in smaller batches
- **Memory Management**: Close other applications during analysis

**Slow Analysis**:
- **Exclude Directories**: Use `.ai_coder_ignore` to exclude files
- **Limit File Types**: Focus on specific file extensions
- **Background Processing**: Let analysis run in background
- **Progress Monitoring**: Use progress indicators to track status

### Advanced Features

#### **Custom Refactoring Rules**
- **Pattern Configuration**: Customize detection patterns
- **Threshold Adjustment**: Modify detection thresholds
- **Language-specific Rules**: Add language-specific refactoring rules
- **Custom Operations**: Define custom refactoring operations

#### **Batch Operations**
- **Multiple Suggestions**: Apply multiple refactoring suggestions at once
- **Dependency Handling**: Automatic handling of dependent changes
- **Conflict Resolution**: Intelligent conflict detection and resolution
- **Rollback Support**: Batch rollback for failed operations

#### **Integration Features**
- **IDE Integration**: Future integration with popular IDEs
- **CI/CD Pipeline**: Integration with continuous integration systems
- **Team Collaboration**: Shared refactoring suggestions
- **Version Control**: Direct integration with Git workflows

### Examples

#### **Python Refactoring Example**

**Original Code**:
```python
def process_user_data(user_data):
    """Process user data and return results."""
    result = 0
    for i in range(1000):  # Magic number
        if i % 2 == 0:
            result += i
        else:
            result -= i
    
    # More complex logic
    for j in range(500):  # Another magic number
        if j % 3 == 0:
            result *= 2
        elif j % 5 == 0:
            result /= 2
        else:
            result += 1
    
    return result
```

**Refactored Code**:
```python
# Extracted constants
MAX_ITERATIONS = 1000
SECOND_ITERATIONS = 500

def process_user_data(user_data):
    """Process user data and return results."""
    result = calculate_initial_result()
    result = apply_complex_logic(result)
    return result

def calculate_initial_result():
    """Calculate initial result based on even/odd numbers."""
    result = 0
    for i in range(MAX_ITERATIONS):
        if i % 2 == 0:
            result += i
        else:
            result -= i
    return result

def apply_complex_logic(result):
    """Apply complex mathematical logic to result."""
    for j in range(SECOND_ITERATIONS):
        if j % 3 == 0:
            result *= 2
        elif j % 5 == 0:
            result /= 2
        else:
            result += 1
    return result
```

#### **JavaScript Refactoring Example**

**Original Code**:
```javascript
function processData(data) {
    let result = 0;
    
    // First loop
    for (let i = 0; i < 1000; i++) {  // Magic number
        if (i % 2 === 0) {
            result += i;
        } else {
            result -= i;
        }
    }
    
    // Second loop
    for (let j = 0; j < 500; j++) {  // Another magic number
        if (j % 3 === 0) {
            result *= 2;
        } else if (j % 5 === 0) {
            result /= 2;
        } else {
            result += 1;
        }
    }
    
    return result;
}
```

**Refactored Code**:
```javascript
// Extracted constants
const MAX_ITERATIONS = 1000;
const SECOND_ITERATIONS = 500;

function processData(data) {
    let result = calculateInitialResult();
    result = applyComplexLogic(result);
    return result;
}

function calculateInitialResult() {
    let result = 0;
    for (let i = 0; i < MAX_ITERATIONS; i++) {
        if (i % 2 === 0) {
            result += i;
        } else {
            result -= i;
        }
    }
    return result;
}

function applyComplexLogic(result) {
    for (let j = 0; j < SECOND_ITERATIONS; j++) {
        if (j % 3 === 0) {
            result *= 2;
        } else if (j % 5 === 0) {
            result /= 2;
        } else {
            result += 1;
        }
    }
    return result;
}
```

## Cloud Models Tab

The Cloud Models tab provides **comprehensive multi-provider LLM management** with automatic failover, cost tracking, and health monitoring capabilities.

### Overview

**Purpose**: Manage multiple AI providers (OpenAI, Anthropic, Google AI) with unified interface, automatic failover, and cost optimization.

**Key Features**:
- **Multi-Provider Support**: OpenAI, Anthropic, Google AI, and more
- **Automatic Failover**: Seamless switching between providers
- **Cost Tracking**: Real-time usage monitoring and cost analysis
- **Health Monitoring**: Automated provider health checks
- **Unified Interface**: Single API for all LLM operations
- **Provider Management**: Add, configure, and test providers
- **Usage Analytics**: Detailed usage statistics and cost breakdown

### Provider Configuration

**Purpose**: Configure and manage AI providers for your application.

#### **Adding Providers**

**OpenAI Configuration**:
1. **API Key**: Enter your OpenAI API key
2. **Base URL**: Optional custom endpoint (default: https://api.openai.com)
3. **Organization**: Optional organization ID
4. **Priority**: Set provider priority (1 = highest, used first)
5. **Timeout**: Request timeout in seconds

**Anthropic Configuration**:
1. **API Key**: Enter your Anthropic API key
2. **Priority**: Set provider priority
3. **Timeout**: Request timeout in seconds

**Google AI Configuration**:
1. **API Key**: Enter your Google AI API key
2. **Priority**: Set provider priority
3. **Timeout**: Request timeout in seconds

**Ollama Configuration**:
1. **Endpoint**: Ollama server URL (default: http://localhost:11434)
2. **Priority**: Set provider priority
3. **Timeout**: Request timeout in seconds

#### **Provider Management**

**Provider List**:
- **Status**: Active/Inactive provider status
- **Priority**: Provider priority order
- **Last Used**: Timestamp of last successful request
- **Success Rate**: Percentage of successful requests
- **Average Cost**: Average cost per request

**Provider Actions**:
- **Test Connection**: Verify provider connectivity
- **Edit Configuration**: Modify provider settings
- **Remove Provider**: Delete provider configuration
- **Enable/Disable**: Toggle provider availability

### Model Selection

**Purpose**: Configure and manage AI models across different providers.

#### **Available Models**

**OpenAI Models**:
- **GPT-4**: Most capable model (8192 tokens, $0.03/1K tokens)
- **GPT-4 Turbo**: Fast and efficient (4096 tokens, $0.01/1K tokens)
- **GPT-3.5 Turbo**: Cost-effective (4096 tokens, $0.002/1K tokens)

**Anthropic Models**:
- **Claude-3 Opus**: Most capable (4096 tokens, $0.015/1K tokens)
- **Claude-3 Sonnet**: Balanced (4096 tokens, $0.003/1K tokens)
- **Claude-3 Haiku**: Fast and cheap (4096 tokens, $0.00025/1K tokens)

**Google AI Models**:
- **Gemini Pro**: General purpose (8192 tokens, $0.0005/1K tokens)
- **Gemini Pro Vision**: Vision capable (8192 tokens, $0.0005/1K tokens)

**Ollama Models**:
- **Local Models**: Any model available in your Ollama instance
- **Custom Models**: Your trained models exported to Ollama

#### **Model Configuration**

**Model Settings**:
- **Default Model**: Set default model for each provider
- **Fallback Models**: Configure backup models for each provider
- **Model Parameters**: Set default temperature, max tokens, etc.
- **Cost Limits**: Set maximum cost per request

**Model Testing**:
- **Test Completion**: Test model with sample prompts
- **Response Quality**: Evaluate model response quality
- **Performance Metrics**: Measure response time and reliability

### Usage Monitoring

**Purpose**: Track and analyze LLM usage patterns and costs.

#### **Real-time Metrics**

**Current Session**:
- **Total Requests**: Number of requests in current session
- **Total Cost**: Total cost for current session
- **Total Tokens**: Total tokens used in current session
- **Active Providers**: Currently active providers

**Provider Breakdown**:
- **Requests per Provider**: Number of requests per provider
- **Cost per Provider**: Cost breakdown by provider
- **Success Rate**: Success rate per provider
- **Average Response Time**: Response time per provider

#### **Historical Analytics**

**Usage Trends**:
- **Daily Usage**: Requests and costs per day
- **Weekly Trends**: Weekly usage patterns
- **Monthly Reports**: Monthly usage summaries
- **Cost Analysis**: Cost trends and optimization opportunities

**Model Usage**:
- **Popular Models**: Most frequently used models
- **Model Performance**: Performance metrics per model
- **Cost per Model**: Cost analysis per model
- **Model Comparison**: Compare models across providers

#### **Cost Optimization**

**Cost Alerts**:
- **Daily Limits**: Set daily cost limits
- **Threshold Alerts**: Alerts when approaching limits
- **Provider Switching**: Automatic switching to cheaper providers
- **Usage Recommendations**: Suggestions for cost optimization

**Optimization Strategies**:
- **Provider Priority**: Put cheaper providers first
- **Model Selection**: Use cost-effective models for simple tasks
- **Token Management**: Optimize prompt length and token usage
- **Batch Processing**: Group requests to reduce overhead

### Health Check

**Purpose**: Monitor provider health and availability.

#### **Provider Health Status**

**Health Indicators**:
- **Connection Status**: Provider connectivity status
- **Response Time**: Average response time
- **Error Rate**: Percentage of failed requests
- **Last Check**: Timestamp of last health check

**Health Check Process**:
1. **Connection Test**: Verify network connectivity
2. **API Test**: Test provider API endpoints
3. **Model Test**: Test model availability
4. **Performance Test**: Measure response times

#### **Automatic Failover**

**Failover Logic**:
1. **Primary Provider**: Try highest priority provider first
2. **Health Check**: Verify provider is healthy
3. **Fallback**: If primary fails, try next provider
4. **Error Handling**: Graceful degradation with detailed reporting

**Failover Configuration**:
- **Failover Threshold**: Number of failures before switching
- **Retry Logic**: Number of retries per provider
- **Backoff Strategy**: Exponential backoff for retries
- **Recovery**: Automatic recovery when provider becomes healthy

### Test Completion

**Purpose**: Test LLM providers and models with sample prompts.

#### **Test Interface**

**Test Options**:
- **Provider Selection**: Choose provider to test
- **Model Selection**: Select model for testing
- **Prompt Input**: Enter test prompt
- **Parameters**: Set temperature, max tokens, etc.

**Test Results**:
- **Response Content**: Model response text
- **Response Time**: Time taken for response
- **Token Usage**: Number of tokens used
- **Cost**: Cost of the test request
- **Provider Used**: Which provider handled the request

#### **Test Scenarios**

**Basic Testing**:
- **Simple Prompts**: Test basic text completion
- **Code Generation**: Test code generation capabilities
- **Analysis Tasks**: Test code analysis capabilities
- **Multi-turn Conversations**: Test chat completion

**Advanced Testing**:
- **Error Handling**: Test error scenarios
- **Rate Limiting**: Test rate limit handling
- **Timeout Scenarios**: Test timeout handling
- **Large Prompts**: Test with large input prompts

### Best Practices

#### **Provider Configuration**
1. **API Key Security**: Store API keys securely using environment variables
2. **Provider Priority**: Set priorities based on cost and performance
3. **Timeout Settings**: Configure appropriate timeouts for each provider
4. **Rate Limits**: Be aware of provider rate limits

#### **Cost Management**
1. **Monitor Usage**: Regularly check usage and cost metrics
2. **Set Limits**: Configure daily and per-request cost limits
3. **Optimize Prompts**: Keep prompts concise to reduce token usage
4. **Use Appropriate Models**: Choose cost-effective models for simple tasks

#### **Health Monitoring**
1. **Regular Checks**: Schedule regular health checks
2. **Alert Configuration**: Set up alerts for provider issues
3. **Failover Testing**: Test failover scenarios regularly
4. **Performance Monitoring**: Track response times and success rates

#### **Security Considerations**
1. **API Key Rotation**: Regularly rotate API keys
2. **Access Control**: Implement proper access controls
3. **Data Privacy**: Be aware of data sent to providers
4. **Audit Logging**: Log all provider interactions for security

### Troubleshooting

#### **Common Issues**

**Provider Not Available**:
- Check API key validity
- Verify network connectivity
- Check provider service status
- Review rate limits and quotas

**High Costs**:
- Review model selection
- Optimize prompt length
- Check for unnecessary requests
- Consider using cheaper providers

**Slow Response Times**:
- Check network connectivity
- Verify provider performance
- Consider using different models
- Implement caching where appropriate

**Failover Issues**:
- Verify provider configurations
- Check health check settings
- Review failover thresholds
- Test failover scenarios manually

#### **Debug Information**

**Logs and Metrics**:
- **Request Logs**: Detailed request/response logs
- **Error Logs**: Error messages and stack traces
- **Performance Metrics**: Response times and success rates
- **Cost Tracking**: Detailed cost breakdown

**Diagnostic Tools**:
- **Provider Test**: Test individual providers
- **Model Test**: Test specific models
- **Network Test**: Test network connectivity
- **Configuration Validation**: Validate provider configurations

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

## 🧠 Advanced AI-Powered Code Analysis

The AI Coder Assistant features **sophisticated intelligent analysis** that goes far beyond traditional linters and provides deep insights into your code.

### **Semantic Code Analysis**

The AI understands the **meaning and context** of your code:

#### **Function Call Analysis**
- **Dangerous Functions**: Detects `eval()`, `exec()`, `input()` usage
- **Performance Issues**: Identifies blocking calls like `sleep()`
- **Security Risks**: Flags potentially unsafe function calls
- **Best Practices**: Suggests safer alternatives

#### **Comparison Logic**
- **Python**: Detects `== None` vs `is None` usage
- **JavaScript**: Identifies loose equality (`==` vs `===`)
- **Type Safety**: Ensures proper comparison operators
- **Semantic Correctness**: Validates logical expressions

#### **Boolean Logic**
- **Redundant Expressions**: Finds unnecessary `True` in AND conditions
- **Logic Simplification**: Suggests cleaner boolean expressions
- **Conditional Analysis**: Analyzes complex conditional logic
- **Optimization Opportunities**: Identifies logical improvements

### **Data Flow Analysis**

Tracks how data moves through your code:

#### **Variable Tracking**
- **Unused Variables**: Detects variables that are defined but never used
- **Undefined Variables**: Identifies variables used without definition
- **Scope Issues**: Analyzes variable scope and accessibility
- **Cross-File Dependencies**: Tracks variables across multiple files

#### **Data Dependencies**
- **Import Analysis**: Tracks module dependencies
- **Function Dependencies**: Analyzes function call relationships
- **Data Relationships**: Maps data flow between components
- **Dependency Cycles**: Detects circular dependencies

### **Pattern Detection**

Recognizes design patterns and anti-patterns:

#### **Design Patterns**
- **Singleton Pattern**: Detects singleton implementations
- **Factory Pattern**: Identifies factory method usage
- **Observer Pattern**: Recognizes observer implementations
- **Strategy Pattern**: Detects strategy pattern usage

#### **Anti-Patterns**
- **God Object**: Identifies classes with too many responsibilities
- **Spaghetti Code**: Detects complex nested control flow
- **Callback Hell**: Finds deeply nested callbacks (JavaScript)
- **Global Variables**: Identifies excessive global variable usage

#### **Code Smells**
- **Complex Methods**: Detects overly complex functions
- **Long Parameter Lists**: Identifies methods with too many parameters
- **Data Clumps**: Finds groups of related data that should be objects
- **Primitive Obsession**: Detects overuse of primitive types

### **Dependency Analysis**

Analyzes project architecture and dependencies:

#### **Circular Dependencies**
- **Import Cycles**: Detects circular import dependencies
- **Module Dependencies**: Maps module dependency relationships
- **Architecture Issues**: Identifies architectural problems
- **Refactoring Suggestions**: Provides solutions for dependency issues

#### **Dependency Complexity**
- **High Coupling**: Detects tightly coupled modules
- **Low Cohesion**: Identifies modules with mixed responsibilities
- **Dependency Metrics**: Calculates dependency complexity scores
- **Architectural Assessment**: Evaluates overall project structure

### **Enhanced Security Detection**

Comprehensive security vulnerability scanning:

#### **Hardcoded Credentials**
- **Passwords**: Detects hardcoded passwords in code
- **API Keys**: Identifies exposed API keys and tokens
- **Secrets**: Finds hardcoded secrets and private keys
- **Configuration**: Detects sensitive configuration data

#### **SQL Injection**
- **String Concatenation**: Identifies unsafe SQL query construction
- **Parameterized Queries**: Suggests safer query methods
- **Input Validation**: Detects missing input validation
- **Database Security**: Analyzes database access patterns

#### **Code Injection**
- **Eval Usage**: Detects dangerous `eval()` function calls
- **Exec Usage**: Identifies `exec()` function usage
- **Dynamic Code**: Finds dynamic code execution patterns
- **Input Sanitization**: Detects missing input sanitization

#### **XSS Vulnerabilities**
- **innerHTML**: Detects unsafe innerHTML assignments
- **document.write**: Identifies dangerous document.write usage
- **User Input**: Analyzes user input handling
- **Output Encoding**: Detects missing output encoding

### **Memory and Performance Analysis**

Identifies performance and memory issues:

#### **Memory Leaks**
- **Infinite Loops**: Detects potential infinite loops
- **Large Data Structures**: Identifies memory-intensive operations
- **Resource Cleanup**: Detects missing resource cleanup
- **Memory Allocation**: Analyzes memory allocation patterns

#### **Performance Issues**
- **Nested Loops**: Detects inefficient nested loop structures
- **String Concatenation**: Identifies inefficient string operations
- **List Operations**: Analyzes list manipulation efficiency
- **Algorithm Complexity**: Detects high-complexity algorithms

#### **Resource Usage**
- **CPU Intensive**: Identifies CPU-intensive operations
- **I/O Operations**: Analyzes I/O operation patterns
- **Network Calls**: Detects inefficient network usage
- **Database Queries**: Analyzes database query efficiency

### **Multi-Language Intelligence**

Advanced analysis across multiple programming languages:

#### **Python Analysis**
- **AST Parsing**: Uses Abstract Syntax Tree for deep analysis
- **Complexity Calculation**: Calculates cyclomatic complexity
- **Type Hints**: Analyzes type annotation usage
- **Import Analysis**: Tracks import dependencies

#### **JavaScript/TypeScript Analysis**
- **Loose Equality**: Detects `==` vs `===` usage
- **Callback Patterns**: Analyzes callback and promise usage
- **Global Variables**: Identifies global variable usage
- **Type Safety**: Analyzes TypeScript type usage

#### **Java Analysis**
- **Raw Types**: Detects generic type usage
- **Exception Handling**: Analyzes exception handling patterns
- **Logging**: Identifies logging framework usage
- **Memory Management**: Analyzes object lifecycle

#### **C/C++ Analysis**
- **Memory Management**: Detects memory allocation/deallocation
- **Pointer Safety**: Analyzes pointer usage patterns
- **Type Casting**: Identifies unsafe type casting
- **Resource Management**: Detects resource cleanup issues

### **Using Advanced Analysis**

#### **Running Analysis**
1. **Select Files**: Choose files or directories to analyze
2. **Choose Language**: Select the programming language
3. **Run Analysis**: Click "Scan Code" to start analysis
4. **Review Results**: Examine detailed analysis results

#### **Understanding Results**
- **Issue Types**: Each issue is categorized by type and severity
- **Code Snippets**: See the exact code causing issues
- **Suggestions**: Get specific recommendations for fixes
- **Context**: Understand the broader context of issues

#### **Taking Action**
- **Review Critical Issues**: Address security and logic errors first
- **Fix Performance Issues**: Optimize code for better performance
- **Refactor Code**: Improve code structure and maintainability
- **Update Documentation**: Address documentation issues

### **Analysis Configuration**

#### **Customizing Analysis**
- **Severity Levels**: Configure which severity levels to report
- **Issue Types**: Enable/disable specific issue types
- **File Patterns**: Include/exclude specific file patterns
- **Language Settings**: Configure language-specific analysis

#### **Performance Settings**
- **Thread Count**: Adjust the number of analysis threads
- **Memory Limits**: Set memory usage limits for analysis
- **Timeout Settings**: Configure analysis timeout values
- **Caching**: Enable/disable analysis result caching

### **Integration with Development Workflow**

#### **IDE Integration**
- **Real-time Analysis**: Get analysis results as you code
- **Quick Fixes**: Apply suggested fixes directly
- **Error Highlighting**: See issues highlighted in your editor
- **Auto-fix**: Automatically fix simple issues

#### **CI/CD Integration**
- **Automated Scanning**: Run analysis in CI/CD pipelines
- **Quality Gates**: Set quality thresholds for deployments
- **Report Generation**: Generate analysis reports for stakeholders
- **Trend Analysis**: Track code quality over time

#### **Team Collaboration**
- **Shared Reports**: Share analysis results with team members
- **Code Reviews**: Use analysis results in code reviews
- **Best Practices**: Establish team coding standards
- **Training**: Use analysis results for team training

## Building Optimized Binaries

The AI Coder Assistant supports building **optimized, modular binaries** that provide significant performance and size benefits over traditional single-binary approaches.

### **🎯 Why Build Binaries?**

#### **Performance Benefits**
- **85-90% Size Reduction**: 20-30MB vs 150-200MB for traditional builds
- **75-80% Memory Reduction**: 100-200MB vs 500-800MB memory usage
- **70-80% Faster Startup**: 2-5 seconds vs 10-15 seconds startup time
- **Modular Architecture**: Load only the components you need

#### **Distribution Benefits**
- **No Python Installation Required**: End users don't need Python
- **Cross-Platform Compatibility**: Works on Windows, Linux, and macOS
- **Easy Deployment**: Simple file distribution
- **Professional Packaging**: Ready for commercial distribution

### **🚀 Quick Build Options**

#### **Windows Users**
```batch
# Simply run the Windows build script
build_windows.bat
```

#### **Linux Users**
```bash
# Make script executable and run
chmod +x build_linux.sh
./build_linux.sh
```

#### **macOS Users**
```bash
# Make script executable and run
chmod +x build_macos.sh
./build_macos.sh
```

#### **Docker Users**
```bash
# Build using Docker (works on any platform)
docker-compose --profile build up
```

### **📋 Manual Build Process**

#### **Step 1: Set Up Build Environment**
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
```

#### **Step 2: Install UPX (Optional but Recommended)**
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

#### **Step 3: Build Components**
```bash
# Build all components
python build_all.py

# Or build specific component
python build_all.py --component core
python build_all.py --component analyzer
python build_all.py --component scanner
python build_all.py --component web
python build_all.py --component trainer
```

### **📦 Build Output Structure**

After successful build, you'll find the following structure in the `dist/` directory:

```
dist/
├── ai-coder-core.exe          # Main GUI application (5-8MB)
├── ai-coder-analyzer.exe      # AI analysis engine (3-5MB)
├── ai-coder-scanner.exe       # Code scanner (2-3MB)
├── ai-coder-web.exe           # Web scraper (2-3MB)
├── ai-coder-trainer.exe       # Model trainer (4-6MB)
├── ai-coder-launcher.exe      # Component launcher (1-2MB)
├── run.py                     # Python launcher script
├── shared/
│   ├── models/                # AI models (optional)
│   ├── config/                # Configuration files
│   └── data/                  # Data directory
├── docs/                      # Documentation
├── README.md                  # Instructions
└── requirements.txt           # Dependencies
```

### **🚀 Running from Binary Distribution**

#### **Main Application**
```bash
# Run the main GUI application
./dist/ai-coder-core

# Or use the launcher
./dist/ai-coder-launcher core
```

#### **Individual Components**
```bash
# Run AI analyzer on specific file
./dist/ai-coder-launcher analyzer --file main.py --language python

# Run code scanner on directory
./dist/ai-coder-launcher scanner --path /path/to/code

# Run web scraper
./dist/ai-coder-launcher web --url https://example.com

# Run model trainer
./dist/ai-coder-launcher trainer --data training_data.txt
```

#### **Component-Specific Usage**

**AI Analyzer**:
```bash
# Analyze single file
./dist/ai-coder-analyzer --file main.py --language python

# Analyze with output file
./dist/ai-coder-analyzer --file main.py --language python --output results.json
```

**Code Scanner**:
```bash
# Scan directory
./dist/ai-coder-scanner --path /path/to/project

# Scan with output file
./dist/ai-coder-scanner --path /path/to/project --output scan_results.json
```

**Web Scraper**:
```bash
# Scrape single URL
./dist/ai-coder-web --url https://docs.python.org/3/

# Scrape with output directory
./dist/ai-coder-web --url https://docs.python.org/3/ --output ./scraped_docs
```

**Model Trainer**:
```bash
# Train model
./dist/ai-coder-trainer --data training_data.txt

# Train with output path
./dist/ai-coder-trainer --data training_data.txt --output ./trained_model
```

### **🔧 Advanced Build Options**

#### **Custom Build Configuration**
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
        'PyQt6.QtCore', 'PyQt6.QtWidgets'
    ],
    'target_platform': 'auto',     # auto, windows, linux, macos
    'architecture': 'auto',        # auto, x86_64, arm64
}
```

#### **Cross-Platform Building**
```bash
# Build for specific platform
docker-compose --profile build-windows up
docker-compose --profile build-linux up
docker-compose --profile build-macos up
```

#### **Performance Optimization**
```bash
# Build with maximum optimization
python build_all.py --optimization-level high

# Build without UPX compression
python build_all.py --compression none

# Build with debug symbols
python build_all.py --debug
```

### **📊 Component Breakdown**

| Component | Size | Dependencies | Function |
|-----------|------|--------------|----------|
| **Core** | 5-8MB | PyQt6, basic config | Main GUI |
| **Analyzer** | 3-5MB | transformers, torch | AI analysis |
| **Scanner** | 2-3MB | pathspec, networkx | Code scanning |
| **Web** | 2-3MB | requests, beautifulsoup4 | Web scraping |
| **Trainer** | 4-6MB | torch, datasets | Model training |
| **Launcher** | 1-2MB | minimal Python | Orchestration |

### **🔄 Continuous Integration**

#### **GitHub Actions Example**
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

### **🐛 Build Troubleshooting**

#### **Common Build Issues**

**Python Not Found**:
```bash
# Windows
python --version
# If not found, install Python from python.org

# Linux/macOS
python3 --version
# If not found: sudo apt-get install python3 (Linux) or brew install python (macOS)
```

**PyInstaller Installation Failed**:
```bash
# Upgrade pip first
pip install --upgrade pip

# Install with specific version
pip install pyinstaller==5.13.0

# Or install from source
pip install git+https://github.com/pyinstaller/pyinstaller.git
```

**UPX Not Found**:
```bash
# Manual installation
# Windows: Download from https://upx.github.io/
# Linux: sudo apt-get install upx
# macOS: brew install upx
```

**Build Fails with Import Errors**:
```bash
# Clean and rebuild
python build_all.py --clean
python build_all.py

# Check dependencies
pip list | grep -E "(torch|transformers|PyQt6)"
```

**Binary Too Large**:
```bash
# Enable UPX compression
python build_all.py --compression upx

# Exclude unnecessary modules
python build_all.py --exclude-modules matplotlib,numpy,pandas

# Use higher optimization
python build_all.py --optimization-level high
```

**Binary Won't Run**:
```bash
# Check permissions (Linux/macOS)
chmod +x dist/*

# Check dependencies
ldd dist/ai-coder-core  # Linux
otool -L dist/ai-coder-core  # macOS

# Run with debug output
./dist/ai-coder-core --debug
```

#### **Platform-Specific Issues**

**Windows**:
- **Antivirus blocking**: Add build directory to exclusions
- **PowerShell execution policy**: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- **Visual Studio Build Tools**: Install for better optimization

**Linux**:
- **Missing libraries**: `sudo apt-get install libgl1-mesa-glx libglib2.0-0`
- **Permission denied**: `chmod +x dist/*`
- **UPX not found**: `sudo apt-get install upx`

**macOS**:
- **Security warning**: Allow in System Preferences > Security & Privacy
- **Missing Xcode tools**: `xcode-select --install`
- **Homebrew not found**: Install from https://brew.sh/

### **📚 Additional Resources**

For comprehensive build instructions, troubleshooting, and advanced options, see:
- **[BUILD_README.md](../BUILD_README.md)** - Complete build guide
- **[BUILD_PLAN.md](../BUILD_PLAN.md)** - Technical architecture and optimization details

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

## Application Structure

The AI Coder Assistant is now organized with a clear separation between frontend (UI) and backend (logic):
- **Frontend**: All user interface code is in `src/frontend/` (PyQt6 windows, dialogs, tabs, etc.)
- **Backend**: All business logic, AI, and data processing is in `src/backend/`

All frontend-backend imports use explicit relative paths (e.g. `from ...backend.services import ai_tools`).

## How the UI Connects to Backend Logic
- The main window and all tabs/widgets call backend services for scanning, training, preprocessing, and PR creation.
- All progress dialogs and worker threads are managed in the frontend, but the actual work is performed by backend functions.
- Settings and constants are always imported from `src/backend/utils/`.

## Testing Frontend-Backend Integration
- Unit tests for every frontend-backend call are in `tests/frontend_backend/`.
- These tests use `unittest` and `unittest.mock` to verify that the UI calls backend services and uses backend constants/settings correctly.
- **What is covered:**
  - All main window calls to backend services (scan, report, train, etc.)
  - Worker thread execution of backend functions
  - All UI tab widgets' use of backend settings/constants
  - Markdown viewer dialog's use of backend constants
- To run all tests:

```bash
python -m unittest discover tests
```

## Progress Bars and Responsiveness
- All long-running operations (scan, preprocess, train, export, etc.) use worker threads and progress dialogs.
- The UI remains responsive and progress bars update correctly for all tasks.

## Further Reading
- See `ARCHITECTURE.md` for a full developer-oriented overview of the new structure and integration patterns.

---

This manual covers the complete functionality of the AI Coder Assistant. For specific technical details, refer to the individual documentation files in the `docs/` directory. 