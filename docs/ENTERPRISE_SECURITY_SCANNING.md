# Enterprise-Grade Security Scanning

This document describes the comprehensive security scanning capabilities that elevate the AI Coder Assistant to industry-standard security analysis.

## Overview

The AI Coder Assistant now includes enterprise-grade security scanning that implements a "defense-in-depth" strategy used by security-mature organizations:

- **SAST (Static Application Security Testing)**: Analyzing code without executing it
- **SCA (Software Composition Analysis)**: Scanning third-party dependencies for known vulnerabilities  
- **Secrets Scanning**: Detecting hardcoded credentials and sensitive information

## Security Tools Integration

### 1. Bandit - Python SAST

**Purpose**: Industry-standard static analysis for Python code security issues.

**Capabilities**:
- Detects common security vulnerabilities (SQL injection, hardcoded passwords, etc.)
- CWE (Common Weakness Enumeration) mapping
- High confidence scoring
- Comprehensive rule set maintained by the OpenStack Security Group

**Integration**: Automatically runs on Python files during scans.

**Example Findings**:
```
File: src/auth.py, Line: 15
Issue: Potential hardcoded password
Severity: High
CWE: CWE-259
Tool: bandit
Confidence: 0.9
```

### 2. pip-audit - Software Composition Analysis

**Purpose**: Scans Python dependencies for known vulnerabilities.

**Capabilities**:
- Checks requirements.txt, pyproject.toml, and setup.py files
- Maps to CVE databases
- Provides fixed version recommendations
- Supports multiple dependency file formats

**Integration**: Automatically runs on project dependencies during comprehensive scans.

**Example Findings**:
```
File: requirements.txt
Issue: Vulnerable package: requests 2.25.1
Severity: Medium
CVE: CVE-2021-33503
Fixed Version: 2.26.0
Tool: pip-audit
```

### 3. TruffleHog - Secrets Scanning

**Purpose**: Detects hardcoded secrets and credentials in code.

**Capabilities**:
- Regex-based pattern matching for API keys, passwords, private keys
- Git history scanning for exposed secrets
- High accuracy with low false positives
- Supports multiple secret formats

**Integration**: Runs on entire project directories to detect secrets.

**Example Findings**:
```
File: config.py, Line: 23
Issue: Potential API key found
Severity: High
CWE: CWE-532
Tool: trufflehog
Confidence: 0.9
```

## Usage

### Quick Scan with Security Analysis

```python
from src.frontend.controllers.backend_controller import BackendController

controller = BackendController()

# Run quick scan with SAST enabled (default)
result = controller.start_quick_scan(
    directory_path="/path/to/project",
    enable_sast=True
)

print(f"Total issues: {result['total_issues']}")
print(f"Security issues: {result['security_issues']}")
print(f"Dependency issues: {result['dependency_issues']}")
print(f"Secrets found: {result['secrets_found']}")
```

### Comprehensive Security Scan

```python
# Start comprehensive security scan
scan_result = controller.run_comprehensive_security_scan("/path/to/project")

# Get detailed results
detailed_result = controller.get_security_scan_result(scan_result['scan_id'])

for issue in detailed_result['issues']:
    print(f"Tool: {issue['tool']}")
    print(f"File: {issue['file']}")
    print(f"Line: {issue['line']}")
    print(f"Issue: {issue['issue']}")
    print(f"Severity: {issue['severity']}")
    print(f"CWE: {issue['cwe_id']}")
    print("---")
```

## API Integration

### FastAPI Endpoints

The security scanning capabilities are available through the unified FastAPI server:

```bash
# Quick scan with security analysis
curl -X POST "http://localhost:8000/api/v1/quick-scan" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/project",
    "enable_sast": true
  }'

# Comprehensive security scan
curl -X POST "http://localhost:8000/api/v1/security-scan" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/path/to/project"
  }'
```

## Configuration

### Tool Availability

The system automatically detects available security tools:

```python
from src.backend.services.sast_analyzer import SASTAnalyzer

analyzer = SASTAnalyzer()
tools_status = analyzer.get_tools_status()

print("Available tools:")
for tool, available in tools_status.items():
    print(f"  {tool}: {'✓' if available else '✗'}")
```

### Customizing Scan Behavior

```python
# Disable SAST for faster scans
result = controller.start_quick_scan(
    directory_path="/path/to/project",
    enable_sast=False
)

# Custom include/exclude patterns
result = controller.start_quick_scan(
    directory_path="/path/to/project",
    include_patterns=["*.py", "*.js"],
    exclude_patterns=["tests/*", "node_modules/*"]
)
```

## Security Best Practices

### 1. Regular Scanning

- Run security scans as part of your CI/CD pipeline
- Schedule regular comprehensive scans
- Scan before each release

### 2. Issue Prioritization

- **High Severity**: Address immediately (secrets, critical vulnerabilities)
- **Medium Severity**: Plan for next sprint
- **Low Severity**: Monitor and address during refactoring

### 3. False Positive Management

- Review and validate findings
- Add exclusions for known false positives
- Update tool configurations as needed

### 4. Dependency Management

- Keep dependencies updated
- Use dependency pinning for reproducible builds
- Monitor for new vulnerabilities

## Integration with Development Workflow

### Pre-commit Hooks

```bash
#!/bin/bash
# pre-commit hook example

# Run quick security scan
python -c "
from src.frontend.controllers.backend_controller import BackendController
controller = BackendController()
result = controller.start_quick_scan('.', enable_sast=True)
if result['security_issues'] > 0:
    print('Security issues found!')
    exit(1)
"
```

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Security Scan
  run: |
    python -c "
    from src.frontend.controllers.backend_controller import BackendController
    controller = BackendController()
    result = controller.run_comprehensive_security_scan('.')
    print(f'Scan ID: {result[\"scan_id\"]}')
    "
```

## Reporting and Export

Security scan results can be exported in multiple formats:

```python
# Export security report
controller.export_scan_report(
    report_data=detailed_result,
    export_format="pdf",  # or "markdown", "json"
    output_path="security_report.pdf"
)
```

## Troubleshooting

### Common Issues

1. **Tools Not Found**: Install missing tools via pip or system package manager
2. **Timeout Errors**: Increase timeout values for large projects
3. **Permission Errors**: Ensure proper file permissions for scanning

### Performance Optimization

- Use exclude patterns to skip irrelevant directories
- Run scans during off-peak hours for large projects
- Consider parallel scanning for multiple projects

## Future Enhancements

- Integration with additional SAST tools (SonarQube, CodeQL)
- Container image scanning
- Infrastructure as Code (IaC) security scanning
- Runtime Application Self-Protection (RASP) integration
- Security metrics and dashboards

---

**Last Updated**: December 2024  
**Version**: 1.0  
**Status**: Production Ready 