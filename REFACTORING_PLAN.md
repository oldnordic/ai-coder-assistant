# Code Refactoring Plan

## Overview
This plan addresses the 70 low-severity code quality issues identified in the AI code review report.

## Issues Summary
- **Total Issues:** 70
- **All Low Severity** - No critical or security issues
- **Two Main Categories:**
  1. Magic Numbers (hardcoded values)
  2. Long Functions (need refactoring)

## Phase 1: Magic Numbers Elimination ✅ COMPLETED

### ✅ Step 1: Create Constants File
- **File:** `src/config/constants.py`
- **Status:** ✅ COMPLETED
- **Impact:** Centralizes all magic numbers

### ✅ Step 2: Update Settings
- **File:** `src/config/settings.py`
- **Status:** ✅ COMPLETED
- **Changes:** Import OLLAMA_API_BASE_URL from constants

## Phase 2: Function Refactoring (Recommended)

### Priority 1: UI Functions
**Files to refactor:**
1. `src/ui/ai_tab_widgets.py` - `setup_ai_tab()`
2. `src/ui/data_tab_widgets.py` - `setup_data_tab()`
3. `src/ui/main_window.py` - `__init__()` and other long methods
4. `src/ui/ollama_export_tab.py` - `setup_ollama_export_tab()`
5. `src/ui/suggestion_dialog.py` - `__init__()`
6. `src/ui/markdown_viewer.py` - `__init__()`

**Refactoring Strategy:**
- Break UI setup into logical sections
- Extract widget creation methods
- Separate layout from functionality

### Priority 2: Core Logic Functions
**Files to refactor:**
1. `src/core/ai_tools.py` - Multiple long functions
2. `src/core/ollama_client.py` - `get_available_models()`
3. `src/core/scanner.py` - Various analysis functions
4. `src/processing/acquire.py` - `crawl_docs()`
5. `src/processing/preprocess.py` - `save_learning_feedback()`
6. `src/training/trainer.py` - `get_best_device()`

**Refactoring Strategy:**
- Extract helper functions
- Separate concerns (validation, processing, output)
- Create utility modules for common operations

## Phase 3: Magic Numbers Replacement

### UI Constants (High Impact)
Replace hardcoded values in UI files:
- Window dimensions
- Widget heights
- Timeout values
- Progress dialog ranges

### Business Logic Constants (Medium Impact)
Replace hardcoded values in core files:
- File size limits
- Content truncation lengths
- Cache expiry times
- HTTP status codes

## Implementation Guidelines

### 1. Constants Usage
```python
from src.config.constants import (
    WINDOW_DEFAULT_WIDTH, 
    WINDOW_DEFAULT_HEIGHT,
    INPUT_HEIGHT,
    HTTP_TIMEOUT_SHORT
)

# Instead of:
self.setGeometry(100, 100, 1200, 800)

# Use:
self.setGeometry(
    WINDOW_DEFAULT_X, 
    WINDOW_DEFAULT_Y, 
    WINDOW_DEFAULT_WIDTH, 
    WINDOW_DEFAULT_HEIGHT
)
```

### 2. Function Refactoring Pattern
```python
# Before: Long function
def setup_complex_widget(self):
    # 100+ lines of setup code
    pass

# After: Broken into logical parts
def setup_complex_widget(self):
    self._create_containers()
    self._setup_inputs()
    self._setup_buttons()
    self._setup_layout()
    self._connect_signals()

def _create_containers(self):
    # Container creation logic
    pass

def _setup_inputs(self):
    # Input setup logic
    pass
```

## Risk Assessment

### Low Risk Changes
- ✅ Constants file creation
- ✅ Settings file updates
- UI magic number replacements

### Medium Risk Changes
- Function refactoring (requires testing)
- Core logic restructuring

### Testing Strategy
1. **Unit Tests:** Test each refactored function
2. **Integration Tests:** Verify UI functionality
3. **Manual Testing:** Test all application features
4. **Regression Testing:** Ensure no functionality is lost

## Success Metrics

### Code Quality Improvements
- [ ] Reduce magic numbers by 90%
- [ ] Break down functions >50 lines
- [ ] Improve code readability scores
- [ ] Reduce cyclomatic complexity

### Maintainability Improvements
- [ ] Centralized configuration
- [ ] Easier to modify UI dimensions
- [ ] Clearer function responsibilities
- [ ] Better testability

## Timeline Estimate

### Phase 1: ✅ COMPLETED (1 hour)
- Constants file creation
- Settings updates

### Phase 2: 2-3 days
- UI function refactoring
- Core logic refactoring

### Phase 3: 1-2 days
- Magic number replacements
- Testing and validation

**Total Estimated Time:** 3-5 days

## Conclusion

The AI review report indicates excellent code health with only minor quality issues. The refactoring will improve maintainability and readability without affecting functionality. All changes are low-risk and can be implemented incrementally. 