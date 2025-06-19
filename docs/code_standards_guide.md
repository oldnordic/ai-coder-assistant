# Code Standards Guide (Updated v2.6.0)

## Overview
The Code Standards system enforces company-specific coding standards across multiple languages. It supports rule creation, analysis, auto-fix, and import/export.

## Features
- Create/edit/remove standards and rules
- Analyze files/directories for violations
- Auto-fix common violations
- Import/export standards for sharing
- Multi-language support (Python, JS, TS, Java, C++, C#, Go, Rust, PHP, Ruby)

## Usage
1. Open the **Code Standards** tab.
2. Use the **Standards** sub-tab to manage standards and rules.
3. Use the **Analysis** sub-tab to analyze code.
4. Use the **Auto-fix** feature to fix violations.
5. Use the **Import/Export** feature to share standards.

## Configuration
- Standards and rules can be managed in the UI or in `code_standards_config.json`.
- Supports company-specific and language-specific rules.

## Troubleshooting
- Ensure correct file permissions and supported languages.
- Review logs for analysis errors.

## Integration
- All features are accessible via the BackendController and REST API.
- For automation, use the API endpoints for analysis and standards management.

## Features

### 1. Code Standard Definition
- **Custom Rules**: Define company-specific coding rules
- **Multiple Languages**: Support for Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust, PHP, Ruby
- **Rule Categories**: Naming conventions, style, security, performance, complexity, documentation
- **Severity Levels**: Error, warning, and info levels for violations

### 2. Automated Code Analysis
- **File Analysis**: Analyze individual files for violations
- **Directory Analysis**: Scan entire directories recursively
- **Real-time Feedback**: Immediate violation detection and reporting
- **Language Detection**: Automatic language identification by file extension

### 3. Violation Management
- **Detailed Reporting**: Line-by-line violation details
- **Severity Classification**: Categorize violations by importance
- **Auto-fix Support**: Automatic fixes for supported violations
- **Manual Review**: Interactive violation review and resolution

### 4. Standard Management
- **Multiple Standards**: Support for multiple coding standards
- **Version Control**: Track standard versions and changes
- **Import/Export**: Share standards across teams and organizations
- **Active Standard**: Set current active standard for analysis

### 5. Integration with AI
- **AI-Powered Analysis**: Use AI models for advanced code analysis
- **Smart Suggestions**: AI-generated improvement recommendations
- **Learning from Violations**: Train AI models on code quality patterns

## Usage

### Code Standards Tab

The Code Standards tab provides a comprehensive interface for managing coding standards:

#### Standards Tab
- **Current Standard**: View and manage the active coding standard
- **Standard List**: Browse all available coding standards
- **Add Standard**: Create new coding standards
- **Import/Export**: Share standards with other teams

#### Analysis Tab
- **File Analysis**: Analyze individual files for violations
- **Directory Analysis**: Scan entire directories
- **Results Overview**: View violation statistics and summaries
- **Auto-fix**: Apply automatic fixes where available

#### Rules Tab
- **Rule Management**: Add, edit, and remove coding rules
- **Rule Filtering**: Filter rules by category and language
- **Rule Configuration**: Configure rule patterns and messages

### Creating a Code Standard

1. **Navigate to Standards Tab**
   - Click on the "Code Standards" tab
   - Go to the "Standards" sub-tab

2. **Add New Standard**
   - Click "Add Standard"
   - Provide standard information:
     - **Name**: Descriptive name for the standard
     - **Company**: Organization name
     - **Version**: Standard version number
     - **Description**: Detailed description
     - **Languages**: Supported programming languages

3. **Define Rules**
   - Add coding rules for each language
   - Configure rule parameters:
     - **ID**: Unique rule identifier
     - **Name**: Rule name
     - **Description**: Rule description
     - **Language**: Target programming language
     - **Severity**: Error, warning, or info
     - **Pattern**: Regex pattern or AST pattern
     - **Message**: Violation message
     - **Category**: Rule category
     - **Auto-fix**: Whether automatic fixes are available

### Example Rule Configuration

```json
{
  "id": "python_function_naming",
  "name": "Function Naming Convention",
  "description": "Functions should use snake_case naming",
  "language": "python",
  "severity": "warning",
  "pattern": "^[a-z_][a-z0-9_]*$",
  "message": "Function names should use snake_case",
  "category": "naming",
  "enabled": true,
  "auto_fix": true,
  "fix_template": "def {function_name_snake_case}:"
}
```

### Running Code Analysis

#### Single File Analysis
1. Navigate to the Analysis tab
2. Click "Analyze File"
3. Select the file to analyze
4. Review results and violations

#### Directory Analysis
1. Navigate to the Analysis tab
2. Click "Analyze Directory"
3. Select the directory to analyze
4. Review comprehensive results

### Managing Violations

#### Viewing Violations
- **File Path**: Location of the violating file
- **Line Number**: Specific line with the violation
- **Rule**: Which rule was violated
- **Severity**: Error, warning, or info level
- **Message**: Description of the violation
- **Category**: Rule category (naming, style, etc.)

#### Fixing Violations
- **Auto-fix**: Apply automatic fixes where available
- **Manual Fix**: Review and fix violations manually
- **Ignore**: Mark violations as acceptable (with justification)

## Supported Languages

### Python
- **Naming Conventions**: Function, class, and variable naming
- **Style Guidelines**: PEP 8 compliance
- **Documentation**: Docstring requirements
- **Complexity**: Function and class length limits
- **Security**: Common security patterns

### JavaScript/TypeScript
- **Naming Conventions**: camelCase, PascalCase rules
- **Style Guidelines**: ESLint-like rules
- **Type Safety**: TypeScript-specific rules
- **Security**: XSS prevention, input validation

### Java
- **Naming Conventions**: Class, method, and variable naming
- **Style Guidelines**: Java coding conventions
- **Documentation**: Javadoc requirements
- **Performance**: Common performance patterns

### C++
- **Naming Conventions**: Class, function, and variable naming
- **Style Guidelines**: Google C++ Style Guide
- **Memory Management**: Smart pointer usage
- **Performance**: Optimization patterns

### Other Languages
- **C#**: .NET coding conventions
- **Go**: Go coding standards
- **Rust**: Rust coding guidelines
- **PHP**: PSR standards
- **Ruby**: Ruby style guide

## Rule Categories

### 1. Naming Conventions
- **Function Names**: Consistent function naming patterns
- **Class Names**: Class naming conventions
- **Variable Names**: Variable naming rules
- **Constant Names**: Constant naming patterns

### 2. Style Guidelines
- **Formatting**: Code formatting rules
- **Indentation**: Consistent indentation
- **Line Length**: Maximum line length limits
- **Spacing**: Whitespace and spacing rules

### 3. Security
- **Input Validation**: Input sanitization patterns
- **Authentication**: Security authentication patterns
- **Authorization**: Access control patterns
- **Data Protection**: Sensitive data handling

### 4. Performance
- **Algorithm Efficiency**: Performance optimization
- **Memory Usage**: Memory management patterns
- **Resource Management**: Resource cleanup patterns
- **Caching**: Caching strategies

### 5. Complexity
- **Function Length**: Maximum function size
- **Class Complexity**: Class size and complexity
- **Cyclomatic Complexity**: Code complexity metrics
- **Nesting Depth**: Maximum nesting levels

### 6. Documentation
- **Docstrings**: Function and class documentation
- **Comments**: Code commenting requirements
- **README**: Project documentation
- **API Documentation**: API documentation standards

## API Endpoints

The Code Standards feature provides REST API endpoints:

#### Standard Management
- `GET /api/code-standards` - List all standards
- `POST /api/code-standards` - Add new standard
- `DELETE /api/code-standards/{standard_name}` - Remove standard
- `GET /api/code-standards/current` - Get current standard
- `POST /api/code-standards/{standard_name}/set-current` - Set current standard

#### Analysis
- `POST /api/code-standards/analyze-file` - Analyze single file
- `POST /api/code-standards/analyze-directory` - Analyze directory

#### Import/Export
- `POST /api/code-standards/export/{standard_name}` - Export standard
- `POST /api/code-standards/import` - Import standard

## Configuration

### Default Standards

The system comes with pre-configured standards:

1. **Python PEP 8**: Python style guide compliance
2. **JavaScript ESLint**: JavaScript coding standards
3. **Java Google Style**: Java coding conventions
4. **C++ Google Style**: C++ coding guidelines

### Custom Standards

To create a custom standard:

1. **Define Requirements**: Identify coding requirements
2. **Create Rules**: Define specific coding rules
3. **Test Rules**: Validate rules with sample code
4. **Deploy Standard**: Make standard available to team

### Standard Versioning

Standards support versioning:
- **Major Versions**: Breaking changes
- **Minor Versions**: New features
- **Patch Versions**: Bug fixes

## Integration with Development Workflow

### 1. Pre-commit Hooks
- Integrate with Git pre-commit hooks
- Automatic analysis before commits
- Block commits with violations

### 2. CI/CD Integration
- Automated analysis in build pipelines
- Quality gates based on violation counts
- Automated reporting

### 3. IDE Integration
- Real-time violation highlighting
- Inline fix suggestions
- Quick-fix actions

### 4. Code Review Integration
- Violation reports in pull requests
- Automated quality checks
- Review guidance

## Best Practices

### 1. Rule Design
- **Clear Messages**: Provide clear violation messages
- **Actionable Fixes**: Include specific fix suggestions
- **Reasonable Limits**: Set achievable standards
- **Context Awareness**: Consider project context

### 2. Standard Management
- **Team Input**: Involve team in standard creation
- **Regular Reviews**: Periodically review and update standards
- **Documentation**: Document rule rationale
- **Training**: Train team on standards

### 3. Analysis Workflow
- **Incremental Analysis**: Start with critical files
- **Regular Scans**: Schedule regular analysis
- **Violation Tracking**: Track violation trends
- **Continuous Improvement**: Use results to improve standards

### 4. Integration
- **Automated Workflows**: Integrate with development tools
- **Quality Gates**: Use violations as quality gates
- **Reporting**: Generate regular quality reports
- **Feedback Loop**: Use results to improve processes

## Troubleshooting

### Common Issues

1. **False Positives**
   - Review and adjust rule patterns
   - Add exceptions for valid cases
   - Update rule logic

2. **Performance Issues**
   - Optimize rule patterns
   - Limit analysis scope
   - Use caching for large files

3. **Language Detection**
   - Verify file extensions
   - Check language configuration
   - Update language mappings

### Error Handling

The system includes comprehensive error handling:
- File access error management
- Language detection fallbacks
- Rule parsing error recovery
- Graceful degradation for unsupported features

## Future Enhancements

Planned improvements include:
- Machine learning-based rule generation
- Advanced pattern recognition
- Integration with code review tools
- Real-time collaboration features
- Custom rule development framework 