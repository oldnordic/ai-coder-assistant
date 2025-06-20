# Import Best Practices for AI Coder Assistant

This document outlines the import best practices implemented in the AI Coder Assistant project to ensure maintainable, readable, and robust Python code.

## Table of Contents

1. [Project Structure](#project-structure)
2. [Import Guidelines](#import-guidelines)
3. [Running the Application](#running-the-application)
4. [Package Organization](#package-organization)
5. [Migration Guide](#migration-guide)
6. [Best Practices Summary](#best-practices-summary)

## Project Structure

The AI Coder Assistant follows a `src` layout pattern, which is considered a Python best practice:

```
ai_coder_assistant/
├── src/
│   ├── __init__.py              # Main package exports
│   ├── main.py                  # Application entry point
│   ├── core/                    # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── error.py
│   │   └── events.py
│   ├── backend/                 # Backend services
│   │   ├── __init__.py
│   │   ├── services/
│   │   │   ├── __init__.py      # Service exports
│   │   │   ├── scanner.py
│   │   │   ├── llm_manager.py
│   │   │   └── ...
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── constants.py
│   │       └── settings.py
│   ├── frontend/                # Frontend components
│   │   ├── __init__.py
│   │   ├── ui/
│   │   │   ├── __init__.py
│   │   │   ├── main_window.py
│   │   │   └── ...
│   │   └── controllers/
│   │       ├── __init__.py
│   │       └── backend_controller.py
│   └── tests/                   # Test suite
│       ├── __init__.py
│       ├── backend/
│       ├── frontend/
│       └── ...
├── main.py                      # Legacy entry point
├── requirements.txt
├── README.md
└── docs/
    └── IMPORT_BEST_PRACTICES.md
```

## Import Guidelines

### 1. Absolute Imports (Preferred)

Always use absolute imports for clarity and maintainability:

```python
# ✅ Good - Absolute imports
from src.backend.services.scanner import ScannerService
from src.frontend.ui.main_window import AICoderAssistant
from src.core.config import Config

# ❌ Avoid - Relative imports across packages
from ...backend.services.scanner import ScannerService
from ..ui.main_window import AICoderAssistant
```

### 2. Relative Imports (Within Same Package)

Use relative imports only for modules within the same package:

```python
# ✅ Good - Within same package
from .intelligent_analyzer import IntelligentCodeAnalyzer
from ..utils.constants import MAX_FILE_SIZE_KB

# ❌ Avoid - Across different packages
from ...frontend.ui.main_window import AICoderAssistant
```

### 3. Import Organization (PEP 8)

Follow PEP 8 guidelines for import organization:

```python
# 1. Standard library imports
import os
import sys
import logging
from typing import Dict, List, Optional

# 2. Third-party library imports
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtCore import pyqtSignal, QTimer

# 3. Local application imports
from src.backend.services.scanner import ScannerService
from src.frontend.ui.main_window import AICoderAssistant
from src.core.config import Config
```

### 4. Package Exports

Use `__init__.py` files to define clean package APIs:

```python
# src/backend/services/__init__.py
from .scanner import ScannerService, TaskStatus, ScanStatus
from .llm_manager import LLMManager
from .intelligent_analyzer import IntelligentCodeAnalyzer

__all__ = [
    'ScannerService',
    'TaskStatus', 
    'ScanStatus',
    'LLMManager',
    'IntelligentCodeAnalyzer'
]
```

## Running the Application

### Preferred Method (Module Execution)

```bash
# From project root - RECOMMENDED
python -m src.main
```

### Legacy Method (Script Execution)

```bash
# From project root - Still works
python main.py
```

### API Server

```bash
# From project root
python -m api.main
```

### Tests

```bash
# Run all tests
python -m pytest src/tests/

# Run specific test module
python -m pytest src/tests/test_scanner.py

# Run with coverage
python -m pytest src/tests/ --cov=src
```

## Package Organization

### Main Package (`src/__init__.py`)

The main package exports the most commonly used components:

```python
# Main application entry point
from .main import main

# Core components
from .core import Config, LogManager, ErrorHandler

# Backend services
from .backend.services import (
    LLMManager,
    ScannerService,
    IntelligentCodeAnalyzer
)

# Frontend components
from .frontend.ui.main_window import AICoderAssistant
```

### Backend Services (`src/backend/services/__init__.py`)

Exports all available backend services:

```python
from .scanner import ScannerService, TaskStatus, ScanStatus
from .llm_manager import LLMManager
from .intelligent_analyzer import IntelligentCodeAnalyzer
from .ollama_client import get_available_models_sync
```

### Frontend Components (`src/frontend/__init__.py`)

Exports UI components and controllers:

```python
from .ui.main_window import AICoderAssistant
from .controllers.backend_controller import BackendController
```

## Migration Guide

### From sys.path Manipulation

**Before (Anti-pattern):**
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from backend.services.scanner import ScannerService
```

**After (Best practice):**
```python
# Use absolute imports
from src.backend.services.scanner import ScannerService

# Or run as module
# python -m src.main
```

### From Relative Imports Across Packages

**Before:**
```python
# In src/frontend/ui/main_window.py
from ...backend.services.scanner import ScannerService
```

**After:**
```python
# Use absolute imports
from src.backend.services.scanner import ScannerService
```

### From Wildcard Imports

**Before:**
```python
from src.backend.services import *
```

**After:**
```python
# Explicit imports
from src.backend.services import ScannerService, LLMManager
```

## Best Practices Summary

### ✅ Do's

1. **Use absolute imports** for cross-package dependencies
2. **Use relative imports** only within the same package
3. **Run applications as modules** with `python -m package.module`
4. **Define package APIs** in `__init__.py` files
5. **Follow PEP 8** import organization
6. **Use explicit imports** instead of wildcard imports
7. **Group imports** by standard library, third-party, and local
8. **Sort imports alphabetically** within each group

### ❌ Don'ts

1. **Don't manipulate sys.path** in application code
2. **Don't use relative imports** across different packages
3. **Don't use wildcard imports** (`from module import *`)
4. **Don't mix import styles** in the same file
5. **Don't import unused modules**
6. **Don't use circular imports**

### Tools for Enforcement

1. **isort**: Automatically sort imports
   ```bash
   pip install isort
   isort src/
   ```

2. **flake8**: Check for import style violations
   ```bash
   pip install flake8
   flake8 src/
   ```

3. **black**: Format code (including imports)
   ```bash
   pip install black
   black src/
   ```

### Configuration Files

#### `.isort.cfg`
```ini
[settings]
profile = black
multi_line_output = 3
line_length = 88
known_first_party = src
```

#### `pyproject.toml`
```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["src"]
```

## Benefits of These Practices

1. **Maintainability**: Clear import paths make code easier to understand and modify
2. **Reliability**: No sys.path manipulation reduces import errors
3. **Portability**: Code works consistently across different environments
4. **Packaging**: Easier to package and distribute the application
5. **IDE Support**: Better autocomplete and refactoring support
6. **Testing**: Easier to write and run tests
7. **Documentation**: Import statements serve as documentation

## Conclusion

Following these import best practices ensures that the AI Coder Assistant project is robust, maintainable, and follows Python community standards. The src layout with absolute imports provides a clear structure that scales well as the project grows.

For questions or issues related to imports, please refer to:
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [Real Python - Absolute vs Relative Imports](https://realpython.com/absolute-vs-relative-python-imports/) 