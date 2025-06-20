# Multi-Language Support Guide

## Overview

The AI Coder Assistant supports **20 programming languages** with **intelligent analysis** that goes far beyond simple linter errors. Each language benefits from both traditional linter integration and advanced intelligent analysis that detects security vulnerabilities, performance issues, code smells, and maintainability problems. The system now uses an organized file structure with configuration files stored in the `config/` directory.

## Project Structure

The multi-language support system uses the organized file structure:

```
ai_coder_assistant/
├── config/                     # Configuration files
│   ├── code_standards_config.json  # Language-specific standards
│   └── ...                     # Other configuration files
├── data/                       # Data storage files
├── src/                        # Source code
│   ├── backend/services/
│   │   ├── scanner.py          # Multi-language scanner
│   │   ├── code_standards.py   # Language standards enforcement
│   │   └── ...                 # Other services
│   └── ...
└── ...
```

## Configuration

The multi-language support system uses configuration files in the `config/` directory:

```bash
# View language-specific configuration
cat config/code_standards_config.json

# Edit language standards
vim config/code_standards_config.json
```

## Intelligent Analysis Features

### 🔍 What Intelligent Analysis Detects

**Across All Languages**:
- **Security Vulnerabilities**: Hardcoded credentials, injection risks, unsafe practices
- **Performance Issues**: Inefficient algorithms, memory leaks, bottlenecks
- **Code Smells**: Anti-patterns, magic numbers, poor practices
- **Maintainability Issues**: Complex functions, poor documentation, TODO/FIXME comments
- **Best Practice Violations**: Language-specific violations and style issues

**Language-Specific Intelligence**:
- **Python**: AST analysis, complexity metrics, Python-specific patterns
- **JavaScript/TypeScript**: Type safety, modern JS patterns, framework-specific issues
- **Java**: Memory management, enterprise patterns, Spring-specific issues
- **C/C++**: Memory safety, undefined behavior, low-level optimizations
- **Go**: Concurrency patterns, Go idioms, performance considerations
- **Rust**: Memory safety, ownership patterns, unsafe code detection
- **And more...**

## Supported Languages

### 1. Python
- **Extensions**: `.py`, `.pyw`, `.pyx`, `.pyi`
- **Linter**: `flake8`
- **Intelligent Analysis**: AST parsing, complexity analysis, Python-specific patterns
- **Installation**: `pip install flake8`
- **Configuration**: `setup.cfg`, `pyproject.toml`, or `.flake8`

**Intelligent Detection**:
- **Security**: Hardcoded secrets, eval() usage, unsafe imports
- **Performance**: List comprehensions vs loops, memory usage patterns
- **Code Smells**: Bare except clauses, magic numbers, unused imports
- **Maintainability**: Function complexity, long parameter lists, TODO comments

### 2. JavaScript
- **Extensions**: `.js`, `.jsx`, `.mjs`
- **Linter**: `eslint`
- **Intelligent Analysis**: Modern JS patterns, framework detection, security analysis
- **Installation**: `npm install -g eslint`
- **Configuration**: `.eslintrc.js`, `.eslintrc.json`, or `package.json`

**Intelligent Detection**:
- **Security**: eval() usage, innerHTML assignments, XSS vulnerabilities
- **Performance**: DOM manipulation patterns, memory leaks, inefficient loops
- **Code Smells**: var usage, console.log in production, debugger statements
- **Best Practices**: Modern ES6+ patterns, framework-specific conventions

### 3. TypeScript
- **Extensions**: `.ts`, `.tsx`
- **Linter**: `eslint` with TypeScript plugin
- **Intelligent Analysis**: Type safety analysis, interface patterns, strict mode violations
- **Installation**: `npm install -g eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin`
- **Configuration**: `.eslintrc.js` with TypeScript rules

**Intelligent Detection**:
- **Type Safety**: any usage, type assertions, interface violations
- **Performance**: Type checking overhead, generic usage patterns
- **Code Smells**: Type casting, unused interfaces, complex type definitions
- **Best Practices**: Strict mode compliance, modern TypeScript patterns

### 4. Java
- **Extensions**: `.java`
- **Linter**: `checkstyle`
- **Intelligent Analysis**: Memory management, enterprise patterns, Spring-specific analysis
- **Installation**: Download from [Apache Checkstyle](https://checkstyle.org/)
- **Configuration**: `checkstyle.xml`

**Intelligent Detection**:
- **Memory Management**: Resource leaks, proper exception handling
- **Enterprise Patterns**: Design pattern violations, architectural issues
- **Security**: Input validation, SQL injection risks, authentication patterns
- **Performance**: Collection usage, string concatenation, I/O patterns

### 5. C/C++
- **Extensions**: `.c`, `.cpp`, `.cc`, `.cxx`, `.h`, `.hpp`, `.hh`, `.hxx`
- **Linter**: `cppcheck`
- **Intelligent Analysis**: Memory safety, undefined behavior, low-level optimizations
- **Installation**: 
  - Ubuntu/Debian: `sudo apt install cppcheck`
  - Arch: `sudo pacman -S cppcheck`
  - macOS: `brew install cppcheck`
- **Configuration**: `cppcheck.cfg`

**Intelligent Detection**:
- **Memory Safety**: Buffer overflows, memory leaks, dangling pointers
- **Undefined Behavior**: Integer overflow, null pointer dereferences
- **Performance**: Inefficient algorithms, cache misses, optimization opportunities
- **Security**: Buffer overflows, format string vulnerabilities, race conditions

### 6. C#
- **Extensions**: `.cs`
- **Linter**: `dotnet` (built-in)
- **Intelligent Analysis**: .NET patterns, async/await usage, LINQ optimization
- **Installation**: .NET SDK
- **Configuration**: `Directory.Build.props`, `.editorconfig`

**Intelligent Detection**:
- **Async Patterns**: Proper async/await usage, deadlock prevention
- **LINQ Optimization**: Inefficient queries, N+1 problems
- **Memory Management**: IDisposable patterns, garbage collection optimization
- **Security**: Input validation, authentication, authorization patterns

### 7. Go
- **Extensions**: `.go`
- **Linter**: `golangci-lint`
- **Intelligent Analysis**: Concurrency patterns, Go idioms, performance analysis
- **Installation**: `go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest`
- **Configuration**: `.golangci.yml`

**Intelligent Detection**:
- **Concurrency**: Goroutine leaks, race conditions, channel usage
- **Go Idioms**: Error handling patterns, interface usage, package organization
- **Performance**: Memory allocation, garbage collection, CPU usage
- **Security**: Input validation, cryptographic usage, network security

### 8. Rust
- **Extensions**: `.rs`
- **Linter**: `cargo clippy`
- **Intelligent Analysis**: Memory safety, ownership patterns, unsafe code detection
- **Installation**: `cargo install clippy`
- **Configuration**: `clippy.toml`

**Intelligent Detection**:
- **Memory Safety**: Ownership violations, borrowing rules, lifetime issues
- **Performance**: Zero-cost abstractions, efficient data structures
- **Security**: Unsafe code usage, FFI patterns, cryptographic implementations
- **Idiomatic Code**: Rust patterns, functional programming, error handling

### 9. PHP
- **Extensions**: `.php`
- **Linter**: `phpcs` (PHP_CodeSniffer)
- **Intelligent Analysis**: Security patterns, framework-specific analysis, performance optimization
- **Installation**: `composer global require squizlabs/php_codesniffer`
- **Configuration**: `phpcs.xml`

**Intelligent Detection**:
- **Security**: SQL injection, XSS vulnerabilities, authentication bypass
- **Performance**: Database query optimization, caching patterns, memory usage
- **Framework Patterns**: Laravel, Symfony, WordPress specific patterns
- **Code Smells**: Global variables, error suppression, deprecated functions

### 10. Ruby
- **Extensions**: `.rb`
- **Linter**: `rubocop`
- **Intelligent Analysis**: Ruby idioms, Rails patterns, metaprogramming analysis
- **Installation**: `gem install rubocop`
- **Configuration**: `.rubocop.yml`

**Intelligent Detection**:
- **Ruby Idioms**: Block usage, method chaining, functional programming
- **Rails Patterns**: ActiveRecord optimization, controller patterns, view logic
- **Performance**: N+1 queries, memory leaks, garbage collection
- **Security**: Input validation, authentication, authorization patterns

### 11. Swift
- **Extensions**: `.swift`
- **Linter**: `swiftlint`
- **Intelligent Analysis**: iOS/macOS patterns, memory management, performance optimization
- **Installation**: `brew install swiftlint`
- **Configuration**: `.swiftlint.yml`

**Intelligent Detection**:
- **Memory Management**: ARC patterns, retain cycles, memory leaks
- **iOS/macOS**: UIKit patterns, Core Data usage, networking patterns
- **Performance**: Image processing, UI rendering, background processing
- **Security**: Keychain usage, network security, data protection

### 12. Kotlin
- **Extensions**: `.kt`, `.kts`
- **Linter**: `ktlint`
- **Intelligent Analysis**: Android patterns, coroutines, functional programming
- **Installation**: Download from [ktlint releases](https://github.com/pinterest/ktlint/releases)
- **Configuration**: `.editorconfig`

**Intelligent Detection**:
- **Android Patterns**: Activity lifecycle, Fragment usage, ViewModel patterns
- **Coroutines**: Structured concurrency, exception handling, cancellation
- **Functional Programming**: Higher-order functions, immutability, pure functions
- **Performance**: Memory usage, UI rendering, background processing

### 13. Scala
- **Extensions**: `.scala`
- **Linter**: `scalafmt`
- **Intelligent Analysis**: Functional programming patterns, Akka usage, Spark optimization
- **Installation**: `coursier install scalafmt`
- **Configuration**: `.scalafmt.conf`

**Intelligent Detection**:
- **Functional Programming**: Immutability, pure functions, monad usage
- **Concurrency**: Akka patterns, actor systems, message passing
- **Big Data**: Spark optimization, memory usage, distributed computing
- **Performance**: JVM optimization, garbage collection, CPU usage

### 14. Dart
- **Extensions**: `.dart`
- **Linter**: `dart analyze` (built-in)
- **Intelligent Analysis**: Flutter patterns, null safety, performance optimization
- **Installation**: Dart SDK
- **Configuration**: `analysis_options.yaml`

**Intelligent Detection**:
- **Flutter Patterns**: Widget lifecycle, state management, UI optimization
- **Null Safety**: Null-aware operators, null checking patterns
- **Performance**: Widget rebuilding, memory usage, rendering optimization
- **Security**: Input validation, network security, data protection

### 15. R
- **Extensions**: `.r`, `.R`
- **Linter**: `lintr`
- **Intelligent Analysis**: Statistical analysis patterns, data science workflows, reproducibility
- **Installation**: `install.packages("lintr")`
- **Configuration**: `.lintr`

**Intelligent Detection**:
- **Statistical Analysis**: Proper statistical methods, data validation
- **Data Science**: Reproducible workflows, data pipeline optimization
- **Performance**: Vectorization, memory usage, computational efficiency
- **Reproducibility**: Random seed management, dependency tracking

### 16. MATLAB
- **Extensions**: `.m`
- **Linter**: `mlint` (built-in)
- **Intelligent Analysis**: Numerical computing patterns, matrix operations, algorithm optimization
- **Installation**: MATLAB installation
- **Configuration**: `mlintrc`

**Intelligent Detection**:
- **Numerical Computing**: Matrix operations, algorithm efficiency, precision issues
- **Performance**: Vectorization, memory usage, computational bottlenecks
- **Code Quality**: Function organization, variable naming, documentation
- **Best Practices**: MATLAB-specific patterns, toolbox usage

### 17. Shell Scripts
- **Extensions**: `.sh`, `.bash`, `.zsh`, `.fish`
- **Linter**: `shellcheck`
- **Intelligent Analysis**: Security analysis, portability checks, system administration patterns
- **Installation**:
  - Ubuntu/Debian: `sudo apt install shellcheck`
  - Arch: `sudo pacman -S shellcheck`
  - macOS: `brew install shellcheck`
- **Configuration**: `.shellcheckrc`

**Intelligent Detection**:
- **Security**: Command injection, privilege escalation, file permission issues
- **Portability**: Cross-platform compatibility, shell-specific features
- **System Administration**: Process management, resource monitoring, automation patterns
- **Best Practices**: Error handling, logging, documentation

### 18. SQL
- **Extensions**: `.sql`
- **Linter**: `sqlfluff`
- **Intelligent Analysis**: Query optimization, database design patterns, security analysis
- **Installation**: `pip install sqlfluff`
- **Configuration**: `sqlfluff.ini`

**Intelligent Detection**:
- **Query Optimization**: Index usage, join optimization, query complexity
- **Database Design**: Normalization, constraint usage, data integrity
- **Security**: SQL injection prevention, access control, data protection
- **Performance**: Query execution plans, resource usage, scalability

### 19. HTML
- **Extensions**: `.html`, `.htm`
- **Linter**: `htmlhint`
- **Intelligent Analysis**: Accessibility patterns, SEO optimization, web standards compliance
- **Installation**: `npm install -g htmlhint`
- **Configuration**: `.htmlhintrc`

**Intelligent Detection**:
- **Accessibility**: ARIA attributes, semantic HTML, screen reader support
- **SEO**: Meta tags, structured data, search engine optimization
- **Web Standards**: HTML5 compliance, cross-browser compatibility
- **Performance**: Resource loading, rendering optimization, mobile responsiveness

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

## Architecture Note

- All language support logic is implemented in the backend (`src/backend/services/`).
- The frontend (UI) calls backend services for language detection, translation, and LLM provider selection.
- See `ARCHITECTURE.md` for details on the new separation and integration patterns.

---

For more information about specific languages or advanced configurations, refer to the individual linter documentation and the main user manual. 