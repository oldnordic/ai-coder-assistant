# AI Coder Assistant - Architecture Documentation

## Overview

The AI Coder Assistant has been restructured following industry-standard frontend/backend separation patterns to improve maintainability, testability, and code organization.

## Architecture Structure

```
src/
├── frontend/                 # Frontend components
│   ├── ui/                  # PyQt6 UI components
│   │   ├── main_window.py   # Main application window
│   │   ├── worker_threads.py # Background worker threads
│   │   ├── ai_tab_widgets.py # AI tab UI components
│   │   ├── data_tab_widgets.py # Data tab UI components
│   │   ├── pr_tab_widgets.py # PR creation tab UI
│   │   ├── ollama_export_tab.py # Ollama export tab UI
│   │   ├── browser_tab.py   # Browser integration tab
│   │   ├── markdown_viewer.py # Markdown report viewer
│   │   └── suggestion_dialog.py # Suggestion review dialog
│   └── controllers/         # Frontend controllers (future use)
├── backend/                 # Backend services and logic
│   ├── services/           # Business logic services
│   │   ├── ai_tools.py     # AI analysis and generation
│   │   ├── scanner.py      # Code scanning and analysis
│   │   ├── intelligent_analyzer.py # Intelligent code analysis
│   │   ├── ollama_client.py # Ollama integration
│   │   ├── acquire.py      # Document acquisition
│   │   ├── preprocess.py   # Data preprocessing
│   │   ├── trainer.py      # Model training
│   │   ├── ai_advisor.py   # AI PR advisor
│   │   ├── pr_creator.py   # PR creation logic
│   │   ├── scan_integrator.py # Scan integration
│   │   ├── pr_templates.py # PR templates
│   │   ├── llm_manager.py  # LLM management
│   │   ├── models.py       # LLM models
│   │   ├── providers.py    # LLM providers
│   │   ├── studio_ui.py    # LLM Studio UI
│   │   ├── main.py         # CLI main entry
│   │   └── git_utils.py    # Git utilities
│   ├── models/             # Data models (future use)
│   └── utils/              # Utility functions
│       ├── settings.py     # Application settings
│       ├── constants.py    # Application constants
│       └── logging_config.py # Logging configuration
└── reports/                # Generated reports
```

## Key Improvements

### 1. Frontend/Backend Separation

- **Frontend**: All UI components, user interactions, and presentation logic
- **Backend**: All business logic, data processing, AI operations, and external integrations

### 2. Progress Dialog Fixes

The progress bar issues have been resolved by:

1. **Proper Signal Connection**: Worker threads now properly connect their progress signals to the appropriate update methods
2. **Determinate Progress**: All progress dialogs use `setRange(0, total_steps)` for proper progress visualization
3. **Immediate Display**: `setMinimumDuration(0)` ensures dialogs appear immediately
4. **Thread Safety**: All progress updates are performed in the main thread via signal/slot connections
5. **Proper Cleanup**: Progress dialogs are properly closed on completion

### 3. Worker Thread Architecture

```python
# Worker threads emit progress signals
worker.progress.connect(self.update_scan_progress)

# Progress updates are handled in the main thread
def update_scan_progress(self, current: int, total: int, message: str):
    if hasattr(self, 'progress_dialog') and self.progress_dialog:
        self.progress_dialog.setRange(0, total)
        self.progress_dialog.setValue(current)
        self.progress_dialog.setLabelText(f"{message}\nProgress: {current}/{total}")
        QApplication.processEvents()
        if current >= total:
            self.progress_dialog.setValue(total)
```

### 4. Import Structure

All imports have been updated to use the new structure:

```python
# Old imports
from src.ui.main_window import AICoderAssistant
from src.core.logging_config import setup_logging

# New imports
from src.frontend.ui.main_window import AICoderAssistant
from src.backend.services.logging_config import setup_logging
```

## Benefits

1. **Maintainability**: Clear separation of concerns makes code easier to maintain
2. **Testability**: Backend services can be tested independently of UI
3. **Scalability**: Easy to add new frontend or backend components
4. **Reusability**: Backend services can be reused across different frontends
5. **Progress Reliability**: Fixed progress dialog issues ensure better user experience

## Migration Notes

- All existing functionality has been preserved
- No features were removed during the restructuring
- Import paths have been updated throughout the codebase
- Progress dialogs now work correctly for all long-running operations

## Testing

A test script (`test_progress.py`) has been created to verify QProgressDialog functionality. The test confirms that:

- Progress dialogs appear immediately
- Progress bars update correctly
- Cancellation works properly
- Dialogs close on completion

## Future Enhancements

1. **Controllers**: Add frontend controllers to handle complex UI logic
2. **Models**: Implement proper data models for better type safety
3. **API Layer**: Add REST API layer for backend services
4. **Testing**: Add comprehensive unit tests for both frontend and backend
5. **Documentation**: Add detailed API documentation for backend services 