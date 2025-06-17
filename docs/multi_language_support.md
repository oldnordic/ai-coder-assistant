# Multi-Language Support Guide

## Overview

The AI Coder Assistant supports **20 programming languages** with language-specific linters and analysis tools. This guide provides detailed information about each supported language, installation instructions, and configuration options.

## Supported Languages

### 1. Python
- **Extensions**: `.py`, `.pyw`, `.pyx`, `.pyi`
- **Linter**: `flake8`
- **Installation**: `pip install flake8`
- **Configuration**: `setup.cfg`, `pyproject.toml`, or `.flake8`
- **Features**: Syntax checking, style enforcement, complexity analysis

### 2. JavaScript
- **Extensions**: `.js`, `.jsx`, `.mjs`
- **Linter**: `eslint`
- **Installation**: `npm install -g eslint`
- **Configuration**: `.eslintrc.js`, `.eslintrc.json`, or `package.json`
- **Features**: Syntax validation, best practices, React support

### 3. TypeScript
- **Extensions**: `.ts`, `.tsx`
- **Linter**: `eslint` with TypeScript plugin
- **Installation**: `npm install -g eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin`
- **Configuration**: `.eslintrc.js` with TypeScript rules
- **Features**: Type checking, interface validation, strict mode

### 4. Java
- **Extensions**: `.java`
- **Linter**: `checkstyle`
- **Installation**: Download from [Apache Checkstyle](https://checkstyle.org/)
- **Configuration**: `checkstyle.xml`
- **Features**: Code style, naming conventions, complexity metrics

### 5. C/C++
- **Extensions**: `.c`, `.cpp`, `.cc`, `.cxx`, `.h`, `.hpp`, `.hh`, `.hxx`
- **Linter**: `cppcheck`
- **Installation**: 
  - Ubuntu/Debian: `sudo apt install cppcheck`
  - Arch: `sudo pacman -S cppcheck`
  - macOS: `brew install cppcheck`
- **Configuration**: `cppcheck.cfg`
- **Features**: Memory leaks, undefined behavior, style issues

### 6. C#
- **Extensions**: `.cs`
- **Linter**: `dotnet` (built-in)
- **Installation**: .NET SDK
- **Configuration**: `Directory.Build.props`, `.editorconfig`
- **Features**: Code analysis, style enforcement, best practices

### 7. Go
- **Extensions**: `.go`
- **Linter**: `golangci-lint`
- **Installation**: `go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest`
- **Configuration**: `.golangci.yml`
- **Features**: Multiple linters, performance analysis, security checks

### 8. Rust
- **Extensions**: `.rs`
- **Linter**: `cargo clippy`
- **Installation**: `cargo install clippy`
- **Configuration**: `clippy.toml`
- **Features**: Memory safety, performance hints, idiomatic code

### 9. PHP
- **Extensions**: `.php`
- **Linter**: `phpcs` (PHP_CodeSniffer)
- **Installation**: `composer global require squizlabs/php_codesniffer`
- **Configuration**: `phpcs.xml`
- **Features**: PSR standards, custom rules, security checks

### 10. Ruby
- **Extensions**: `.rb`
- **Linter**: `rubocop`
- **Installation**: `gem install rubocop`
- **Configuration**: `.rubocop.yml`
- **Features**: Style enforcement, best practices, Rails support

### 11. Swift
- **Extensions**: `.swift`
- **Linter**: `swiftlint`
- **Installation**: `brew install swiftlint`
- **Configuration**: `.swiftlint.yml`
- **Features**: Swift style guide, best practices, iOS/macOS specific

### 12. Kotlin
- **Extensions**: `.kt`, `.kts`
- **Linter**: `ktlint`
- **Installation**: Download from [ktlint releases](https://github.com/pinterest/ktlint/releases)
- **Configuration**: `.editorconfig`
- **Features**: Kotlin style guide, Android support, custom rules

### 13. Scala
- **Extensions**: `.scala`
- **Linter**: `scalafmt`
- **Installation**: `coursier install scalafmt`
- **Configuration**: `.scalafmt.conf`
- **Features**: Code formatting, style enforcement, functional programming

### 14. Dart
- **Extensions**: `.dart`
- **Linter**: `dart analyze` (built-in)
- **Installation**: Dart SDK
- **Configuration**: `analysis_options.yaml`
- **Features**: Flutter support, null safety, performance analysis

### 15. R
- **Extensions**: `.r`, `.R`
- **Linter**: `lintr`
- **Installation**: `install.packages("lintr")`
- **Configuration**: `.lintr`
- **Features**: R style guide, statistical analysis, reproducibility

### 16. MATLAB
- **Extensions**: `.m`
- **Linter**: `mlint` (built-in)
- **Installation**: MATLAB installation
- **Configuration**: `mlintrc`
- **Features**: MATLAB best practices, performance analysis, code quality

### 17. Shell Scripts
- **Extensions**: `.sh`, `.bash`, `.zsh`, `.fish`
- **Linter**: `shellcheck`
- **Installation**:
  - Ubuntu/Debian: `sudo apt install shellcheck`
  - Arch: `sudo pacman -S shellcheck`
  - macOS: `brew install shellcheck`
- **Configuration**: `.shellcheckrc`
- **Features**: Shell script validation, portability checks, security analysis

### 18. SQL
- **Extensions**: `.sql`
- **Linter**: `sqlfluff`
- **Installation**: `pip install sqlfluff`
- **Configuration**: `sqlfluff.ini`
- **Features**: SQL formatting, dialect support, best practices

### 19. HTML
- **Extensions**: `.html`, `.htm`
- **Linter**: `htmlhint`
- **Installation**: `npm install -g htmlhint`
- **Configuration**: `.htmlhintrc`
- **Features**: HTML validation, accessibility checks, best practices

## Installation Guide

### System-Wide Installation

For the best experience, install linters system-wide:

```bash
# Python
pip install flake8

# JavaScript/TypeScript
npm install -g eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin

# C/C++
sudo apt install cppcheck  # Ubuntu/Debian
sudo pacman -S cppcheck    # Arch

# Go
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Rust
cargo install clippy

# Shell
sudo apt install shellcheck  # Ubuntu/Debian
sudo pacman -S shellcheck    # Arch

# SQL
pip install sqlfluff

# HTML
npm install -g htmlhint
```

### Project-Specific Installation

For project-specific configurations:

```bash
# JavaScript/TypeScript project
npm init -y
npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin

# Python project
pip install flake8
echo "[flake8]" > setup.cfg

# Go project
go mod init myproject
echo "run:" > .golangci.yml
echo "  linters:" >> .golangci.yml
echo "    - gofmt" >> .golangci.yml
```

## Configuration Examples

### Python (flake8)
```ini
# setup.cfg
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist
```

### JavaScript/TypeScript (ESLint)
```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "@typescript-eslint/recommended"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint"],
  "rules": {
    "no-unused-vars": "error",
    "prefer-const": "error"
  }
}
```

### C/C++ (cppcheck)
```ini
# cppcheck.cfg
--enable=all
--suppress=missingIncludeSystem
--suppress=unusedFunction
--max-configs=10
```

### Go (golangci-lint)
```yaml
# .golangci.yml
run:
  linters:
    - gofmt
    - golint
    - govet
    - errcheck
    - staticcheck
```

### Rust (clippy)
```toml
# clippy.toml
# Disable specific lints
blacklisted-names = ["foo", "baz"]
```

## Language-Specific Features

### Python
- **Type Hints**: Analyzes type annotations
- **Import Sorting**: Checks import organization
- **Docstring Validation**: Ensures proper documentation
- **Complexity Analysis**: Identifies overly complex functions

### JavaScript/TypeScript
- **Type Checking**: Validates TypeScript types
- **React Support**: Analyzes React components
- **ES6+ Features**: Checks modern JavaScript usage
- **Module Analysis**: Validates import/export statements

### C/C++
- **Memory Safety**: Detects memory leaks and undefined behavior
- **Performance**: Identifies performance bottlenecks
- **Portability**: Checks for platform-specific code
- **Security**: Finds security vulnerabilities

### Java
- **Naming Conventions**: Enforces Java naming standards
- **Code Complexity**: Analyzes cyclomatic complexity
- **Documentation**: Checks Javadoc completeness
- **Best Practices**: Enforces Java coding standards

### Go
- **Gofmt**: Ensures consistent formatting
- **Error Handling**: Checks proper error handling
- **Performance**: Identifies performance issues
- **Security**: Finds security vulnerabilities

## Best Practices

### General Guidelines
1. **Install Required Linters**: Ensure all linters are properly installed
2. **Configure Linters**: Set up appropriate configuration files
3. **Update Regularly**: Keep linters updated to latest versions
4. **Test Configurations**: Verify linter configurations work correctly

### Project Setup
1. **Language Detection**: The application automatically detects file types
2. **Ignore Patterns**: Use `.ai_coder_ignore` to exclude files
3. **Configuration Files**: Place linter configs in project root
4. **Version Control**: Commit linter configurations to version control

### Performance Optimization
1. **Parallel Processing**: The application processes files in parallel
2. **Caching**: Results are cached for faster subsequent scans
3. **Incremental Analysis**: Focus on changed files for faster scans
4. **Resource Management**: Monitor memory and CPU usage

## Troubleshooting

### Common Issues

**Linter Not Found**:
```bash
# Check if linter is installed
which flake8
which eslint
which cppcheck

# Check PATH
echo $PATH

# Reinstall if needed
pip install --upgrade flake8
npm install -g eslint
```

**Configuration Issues**:
```bash
# Test linter configuration
flake8 --config=setup.cfg test.py
eslint --config=.eslintrc.json test.js
cppcheck --config-file=cppcheck.cfg test.cpp
```

**Performance Issues**:
- Reduce the number of files scanned
- Use more specific ignore patterns
- Update to latest linter versions
- Consider using faster linter configurations

### Language-Specific Issues

**Python**:
- Ensure virtual environment is activated
- Check for conflicting linter installations
- Verify Python version compatibility

**JavaScript/TypeScript**:
- Check Node.js and npm versions
- Ensure ESLint plugins are installed
- Verify TypeScript configuration

**C/C++**:
- Check compiler and linter compatibility
- Ensure proper include paths
- Verify platform-specific configurations

**Go**:
- Check Go version compatibility
- Ensure GOPATH and GOROOT are set correctly
- Verify module configuration

## Advanced Configuration

### Custom Linter Rules
Each language supports custom rule configurations:

```yaml
# Example: Custom ESLint rules
rules:
  custom-rule: "error"
  another-rule: "warn"
```

### Ignore Patterns
Use language-specific ignore patterns:

```gitignore
# Python
__pycache__/
*.pyc

# JavaScript
node_modules/
dist/

# C/C++
build/
*.o
*.exe

# Go
vendor/
*.exe
```

### Integration with IDEs
Configure your IDE to use the same linter configurations:

- **VS Code**: Install language-specific extensions
- **IntelliJ**: Configure external tools
- **Vim/Emacs**: Set up linter integration

## Future Enhancements

The multi-language support is continuously being improved:

1. **Additional Languages**: Support for more programming languages
2. **Better Integration**: Improved IDE and editor integration
3. **Performance**: Faster analysis and processing
4. **Custom Rules**: Support for project-specific linting rules
5. **Machine Learning**: AI-powered language-specific suggestions

---

For more information about specific languages or advanced configurations, refer to the individual linter documentation and the main user manual. 