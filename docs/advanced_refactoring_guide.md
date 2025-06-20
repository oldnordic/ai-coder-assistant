# Advanced Refactoring Guide

## Overview

The Advanced Refactoring system in AI Coder Assistant provides **comprehensive automated refactoring capabilities** with multi-language support, safety features, and intelligent suggestion management. This guide covers all aspects of using the refactoring system effectively. The system now uses an organized file structure with configuration files stored in the `config/` directory.

## Project Structure

The refactoring system uses the organized file structure:

```
ai_coder_assistant/
├── config/                     # Configuration files
│   ├── code_standards_config.json  # Code standards for refactoring
│   └── ...                     # Other configuration files
├── data/                       # Data storage files
├── src/                        # Source code
│   ├── backend/services/
│   │   ├── refactoring.py      # Refactoring engine
│   │   ├── code_standards.py   # Code standards enforcement
│   │   └── ...                 # Other services
│   └── ...
└── ...
```

## Table of Contents

1. [Getting Started](#getting-started)
2. [Core Concepts](#core-concepts)
3. [Supported Languages](#supported-languages)
4. [Refactoring Operations](#refactoring-operations)
5. [User Interface Guide](#user-interface-guide)
6. [Safety Features](#safety-features)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Usage](#advanced-usage)
10. [Examples](#examples)

## Getting Started

### Prerequisites

- **Project Setup**: Have a code project ready for analysis
- **Version Control**: Ensure your code is committed to version control
- **Backup Strategy**: Understand the backup and safety features
- **Test Coverage**: Have good test coverage before refactoring
- **Configuration**: Ensure `config/code_standards_config.json` is properly configured

### Configuration Setup

The refactoring system uses configuration files in the `config/` directory:

```bash
# View code standards configuration
cat config/code_standards_config.json

# Edit code standards for refactoring
vim config/code_standards_config.json
```

### Quick Start

1. **Open Advanced Refactoring Tab**: Navigate to the "Advanced Refactoring" tab in the main application
2. **Select Project**: Choose your project directory for analysis
3. **Start Analysis**: Click "Analyze Project" to begin refactoring opportunity detection
4. **Review Suggestions**: Examine the list of refactoring opportunities
5. **Preview Changes**: Use the preview system to understand proposed changes
6. **Apply Refactoring**: Apply selected refactoring operations with safety features

## Core Concepts

### What is Refactoring?

**Refactoring** is the process of restructuring existing code without changing its external behavior. The goal is to improve code quality, maintainability, and readability.

### Key Principles

- **Behavior Preservation**: Refactoring should not change what the code does
- **Small Steps**: Make small, incremental changes
- **Safety First**: Always have backup and rollback capabilities
- **Testing**: Verify functionality after each refactoring step

### Refactoring vs. Rewriting

- **Refactoring**: Improves existing code structure while preserving behavior
- **Rewriting**: Creates new code from scratch (not covered by this system)

## Supported Languages

### Python

**Analysis Method**: AST-based (Abstract Syntax Tree)
**File Extensions**: `.py`, `.pyw`, `.pyx`, `.pyi`

**Features**:
- **Function Analysis**: Detects long functions and high cyclomatic complexity
- **Class Analysis**: Identifies large classes and method counts
- **Import Analysis**: Finds unused imports and circular dependencies
- **Magic Numbers**: Detects hardcoded numbers that should be constants
- **Type Hints**: Respects type annotations and hints

**Python-specific Refactoring**:
- Extract method from long functions
- Extract class from large classes
- Extract constants from magic numbers
- Remove unused imports
- Simplify complex expressions

### JavaScript/TypeScript

**Analysis Method**: Pattern-based with regex matching
**File Extensions**: `.js`, `.jsx`, `.mjs`, `.ts`, `.tsx`

**Features**:
- **Function Detection**: Identifies long functions and complex logic
- **Class Analysis**: Finds large classes and method counts
- **Variable Analysis**: Detects unused variables and magic numbers
- **Module Analysis**: ES6 module import/export tracking
- **Async/Await**: Async function complexity analysis

**JavaScript/TypeScript Refactoring**:
- Extract function from long functions
- Extract class from large classes
- Extract constants from magic numbers
- Remove unused variables
- Simplify complex logic

### Java & C++

**Analysis Method**: Pattern-based (framework ready)
**File Extensions**: `.java`, `.c`, `.cpp`, `.cc`, `.cxx`, `.h`, `.hpp`

**Features**:
- **Basic Analysis**: File structure and size analysis
- **Pattern Matching**: Language-specific pattern detection
- **Future Enhancement**: Planned for full language support

## Refactoring Operations

### Extract Method

**Purpose**: Break down long functions into smaller, focused methods.

**When to Use**:
- Functions with 30+ lines of code
- Functions with high cyclomatic complexity (>10)
- Functions with multiple responsibilities
- Functions that are difficult to test

**Benefits**:
- Improved readability and understanding
- Better testability (smaller units to test)
- Enhanced maintainability
- Reduced code duplication

**Example**:
```python
# Before
def process_data(data):
    result = 0
    for item in data:
        if item > 0:
            result += item * 2
        else:
            result -= abs(item)
    
    # More processing...
    for item in data:
        if item % 2 == 0:
            result *= 1.5
        else:
            result /= 1.5
    
    return result

# After
def process_data(data):
    result = calculate_initial_result(data)
    result = apply_final_processing(data, result)
    return result

def calculate_initial_result(data):
    result = 0
    for item in data:
        if item > 0:
            result += item * 2
        else:
            result -= abs(item)
    return result

def apply_final_processing(data, result):
    for item in data:
        if item % 2 == 0:
            result *= 1.5
        else:
            result /= 1.5
    return result
```

### Extract Class

**Purpose**: Split large classes into smaller, more focused classes.

**When to Use**:
- Classes with 100+ lines of code
- Classes with 15+ methods
- Classes with multiple responsibilities
- Classes that violate the Single Responsibility Principle

**Benefits**:
- Better separation of concerns
- Reduced coupling between components
- Improved testability
- Enhanced maintainability

**Example**:
```python
# Before
class DataProcessor:
    def __init__(self):
        self.data = []
        self.config = {}
        self.logger = None
    
    def load_data(self, file_path):
        # 20 lines of data loading logic
        pass
    
    def validate_data(self, data):
        # 15 lines of validation logic
        pass
    
    def transform_data(self, data):
        # 25 lines of transformation logic
        pass
    
    def save_data(self, data, file_path):
        # 18 lines of saving logic
        pass
    
    def generate_report(self, data):
        # 30 lines of report generation logic
        pass

# After
class DataProcessor:
    def __init__(self):
        self.data = []
        self.config = {}
        self.logger = None
        self.loader = DataLoader()
        self.validator = DataValidator()
        self.transformer = DataTransformer()
        self.saver = DataSaver()
        self.reporter = ReportGenerator()
    
    def process_data(self, input_path, output_path):
        data = self.loader.load_data(input_path)
        data = self.validator.validate_data(data)
        data = self.transformer.transform_data(data)
        self.saver.save_data(data, output_path)
        return self.reporter.generate_report(data)

class DataLoader:
    def load_data(self, file_path):
        # 20 lines of data loading logic
        pass

class DataValidator:
    def validate_data(self, data):
        # 15 lines of validation logic
        pass

# ... other extracted classes
```

### Extract Constant

**Purpose**: Replace magic numbers with named constants.

**When to Use**:
- Numbers >= 1000 in code
- Frequently used values
- Configuration values
- Mathematical constants

**Benefits**:
- Improved readability
- Centralized configuration
- Easier maintenance
- Reduced errors

**Example**:
```python
# Before
def calculate_daily_rate(hours_worked):
    return hours_worked * 25.50  # Magic number

def process_timeout():
    time.sleep(300)  # Magic number

# After
HOURLY_RATE = 25.50
TIMEOUT_SECONDS = 300

def calculate_daily_rate(hours_worked):
    return hours_worked * HOURLY_RATE

def process_timeout():
    time.sleep(TIMEOUT_SECONDS)
```

### Remove Unused Imports

**Purpose**: Clean up unused import statements.

**When to Use**:
- Imported modules not used in the file
- Dead code cleanup
- Performance optimization

**Benefits**:
- Cleaner code
- Faster import times
- Reduced dependencies
- Better maintainability

**Example**:
```python
# Before
import os
import sys
import json
import re
from typing import List, Dict, Any

def process_data(data):
    # Only uses json and List
    result = json.loads(data)
    return List(result)

# After
import json
from typing import List

def process_data(data):
    result = json.loads(data)
    return List(result)
```

## User Interface Guide

### Main Interface

**Components**:
1. **Project Selection**: Choose the project directory to analyze
2. **Analysis Button**: Start refactoring opportunity detection
3. **Filters**: Filter suggestions by priority, category, and language
4. **Suggestions Table**: List of refactoring opportunities
5. **Details Panel**: Information about selected suggestions
6. **Actions Panel**: Preview and apply refactoring operations

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

### Preview System

**Features**:
- **File Changes**: List of files that will be modified
- **Operations**: Individual refactoring operations within each file
- **Diff View**: Side-by-side comparison of original and refactored code
- **Summary**: Overview of changes (lines added, removed, files modified)

**How to Use**:
1. Select a refactoring suggestion from the list
2. Click "Preview Changes" button
3. Review the diff view and file changes
4. Understand the impact of modifications
5. Decide whether to apply or skip the refactoring

## Safety Features

### Automatic Backup

**Backup Creation**:
- **Automatic**: Creates backup files before applying changes
- **Location**: Same directory as original files
- **Naming**: `filename.py.backup`
- **Verification**: Confirms backup files were created successfully

**Backup Options**:
- **Enable Backup**: Always create backup files (recommended)
- **Backup Location**: Choose backup directory
- **Backup Naming**: Customize backup file naming

### Validation System

**Pre-application Validation**:
- **Syntax Check**: Validates refactored code syntax
- **Import Validation**: Checks import statement correctness
- **Dependency Analysis**: Verifies no broken dependencies
- **Conflict Detection**: Identifies potential conflicts

**Validation Results**:
- **Passed**: All validations successful
- **Warnings**: Minor issues that don't prevent application
- **Errors**: Critical issues that prevent application

### Rollback Capabilities

**Rollback Options**:
- **Automatic Rollback**: Reverts changes if validation fails
- **Manual Rollback**: Use backup files to restore original code
- **Partial Rollback**: Rollback specific operations

**Rollback Process**:
1. **Detection**: System detects issues during application
2. **Notification**: User is notified of problems
3. **Rollback**: Automatic or manual rollback process
4. **Verification**: Confirm original code is restored

## Best Practices

### Before Refactoring

1. **Version Control**: Ensure your code is committed to version control
2. **Backup Creation**: Always enable backup creation for safety
3. **Test Coverage**: Have good test coverage before refactoring
4. **Review Changes**: Always preview changes before applying
5. **Start Small**: Begin with low-risk refactoring operations

### During Refactoring

1. **Monitor Progress**: Watch progress indicators during application
2. **Check Results**: Review application results and any warnings
3. **Verify Changes**: Test your code after refactoring
4. **Run Tests**: Execute your test suite to ensure functionality
5. **Review Code**: Manually review the refactored code

### After Refactoring

1. **Test Thoroughly**: Run comprehensive tests on refactored code
2. **Review Performance**: Check if refactoring improved performance
3. **Update Documentation**: Update any affected documentation
4. **Commit Changes**: Commit refactored code to version control
5. **Monitor Issues**: Watch for any issues introduced by refactoring

### Code Quality Guidelines

1. **Single Responsibility**: Each function/class should have one reason to change
2. **DRY Principle**: Don't Repeat Yourself - eliminate code duplication
3. **Meaningful Names**: Use descriptive names for functions, classes, and variables
4. **Small Functions**: Keep functions small and focused
5. **Clear Intent**: Code should clearly express its intent

## Troubleshooting

### Common Issues

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

### Performance Optimization

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

### Error Messages

**Common Error Messages**:
- **"File not found"**: Check file path and permissions
- **"Syntax error"**: Fix syntax errors before refactoring
- **"Permission denied"**: Check file and directory permissions
- **"Out of memory"**: Close other applications or reduce project size

## Advanced Usage

### Custom Refactoring Rules

**Pattern Configuration**:
- **Custom Patterns**: Define custom detection patterns
- **Threshold Adjustment**: Modify detection thresholds
- **Language-specific Rules**: Add language-specific refactoring rules
- **Custom Operations**: Define custom refactoring operations

**Configuration Files**:
- **Pattern Files**: JSON configuration for custom patterns
- **Threshold Files**: Configuration for detection thresholds
- **Rule Files**: Language-specific rule definitions

### Batch Operations

**Multiple Suggestions**:
- **Select Multiple**: Choose multiple refactoring suggestions
- **Batch Apply**: Apply multiple suggestions at once
- **Dependency Handling**: Automatic handling of dependent changes
- **Conflict Resolution**: Intelligent conflict detection and resolution

**Batch Management**:
- **Batch Preview**: Preview all changes in batch
- **Batch Validation**: Validate all changes before application
- **Batch Rollback**: Rollback entire batch if needed

### Integration Features

**IDE Integration** (Future):
- **VS Code Extension**: Direct integration with VS Code
- **IntelliJ Plugin**: Integration with IntelliJ IDEA
- **Vim/Emacs**: Command-line integration
- **Real-time Suggestions**: Live refactoring suggestions

**CI/CD Pipeline** (Future):
- **Automated Refactoring**: Automatic refactoring in CI/CD
- **Quality Gates**: Refactoring as part of quality checks
- **Team Collaboration**: Shared refactoring suggestions
- **Version Control**: Direct integration with Git workflows

## Examples

### Python Refactoring Examples

#### **Long Function Refactoring**

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

#### **Large Class Refactoring**

**Original Code**:
```python
class UserManager:
    def __init__(self):
        self.users = []
        self.config = {}
        self.logger = None
    
    def add_user(self, user_data):
        # 20 lines of user addition logic
        pass
    
    def remove_user(self, user_id):
        # 15 lines of user removal logic
        pass
    
    def update_user(self, user_id, user_data):
        # 25 lines of user update logic
        pass
    
    def validate_user(self, user_data):
        # 30 lines of validation logic
        pass
    
    def authenticate_user(self, credentials):
        # 35 lines of authentication logic
        pass
    
    def generate_user_report(self, user_id):
        # 40 lines of report generation logic
        pass
```

**Refactored Code**:
```python
class UserManager:
    def __init__(self):
        self.users = []
        self.config = {}
        self.logger = None
        self.validator = UserValidator()
        self.authenticator = UserAuthenticator()
        self.reporter = UserReporter()
    
    def add_user(self, user_data):
        if self.validator.validate_user(user_data):
            # 20 lines of user addition logic
            pass
    
    def remove_user(self, user_id):
        # 15 lines of user removal logic
        pass
    
    def update_user(self, user_id, user_data):
        if self.validator.validate_user(user_data):
            # 25 lines of user update logic
            pass
    
    def authenticate_user(self, credentials):
        return self.authenticator.authenticate(credentials)
    
    def generate_user_report(self, user_id):
        return self.reporter.generate_report(user_id)

class UserValidator:
    def validate_user(self, user_data):
        # 30 lines of validation logic
        pass

class UserAuthenticator:
    def authenticate(self, credentials):
        # 35 lines of authentication logic
        pass

class UserReporter:
    def generate_report(self, user_id):
        # 40 lines of report generation logic
        pass
```

### JavaScript Refactoring Examples

#### **Long Function Refactoring**

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

#### **Large Class Refactoring**

**Original Code**:
```javascript
class DataProcessor {
    constructor() {
        this.data = [];
        this.config = {};
    }
    
    loadData(filePath) {
        // 25 lines of data loading logic
    }
    
    validateData(data) {
        // 20 lines of validation logic
    }
    
    transformData(data) {
        // 30 lines of transformation logic
    }
    
    saveData(data, filePath) {
        // 15 lines of saving logic
    }
    
    generateReport(data) {
        // 35 lines of report generation logic
    }
}
```

**Refactored Code**:
```javascript
class DataProcessor {
    constructor() {
        this.data = [];
        this.config = {};
        this.loader = new DataLoader();
        this.validator = new DataValidator();
        this.transformer = new DataTransformer();
        this.saver = new DataSaver();
        this.reporter = new ReportGenerator();
    }
    
    processData(inputPath, outputPath) {
        const data = this.loader.loadData(inputPath);
        const validatedData = this.validator.validateData(data);
        const transformedData = this.transformer.transformData(validatedData);
        this.saver.saveData(transformedData, outputPath);
        return this.reporter.generateReport(transformedData);
    }
}

class DataLoader {
    loadData(filePath) {
        // 25 lines of data loading logic
    }
}

class DataValidator {
    validateData(data) {
        // 20 lines of validation logic
    }
}

class DataTransformer {
    transformData(data) {
        // 30 lines of transformation logic
    }
}

class DataSaver {
    saveData(data, filePath) {
        // 15 lines of saving logic
    }
}

class ReportGenerator {
    generateReport(data) {
        // 35 lines of report generation logic
    }
}
```

## Conclusion

The Advanced Refactoring system provides powerful tools for improving code quality and maintainability. By following the best practices outlined in this guide and using the safety features effectively, you can confidently refactor your code while maintaining its functionality and improving its structure.

Remember to:
- Always preview changes before applying them
- Use version control and backup features
- Test thoroughly after refactoring
- Start with small, low-risk changes
- Monitor for any issues introduced by refactoring

With these guidelines, you can effectively use the Advanced Refactoring system to improve your codebase systematically and safely. 