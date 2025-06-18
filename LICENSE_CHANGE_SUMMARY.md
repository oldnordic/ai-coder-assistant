# License Change Summary

## Overview
The AI Coder Assistant project has been successfully relicensed from MIT License to GNU General Public License v3.0 (GPL-3).

## Changes Made

### 1. Main License File
- **Created**: `LICENSE` file with full GPL-3.0 text
- **Location**: Project root directory
- **Content**: Complete GNU General Public License v3.0 text

### 2. Documentation Updates
- **Updated**: `README.md`
  - Added GPL-3.0 license badge
  - Updated license section to reference GPL-3.0
  - Added copyright notice

### 3. Source Code Headers
- **Updated**: `main.py` with GPL-3.0 header
- **Created**: `scripts/add_gpl_headers.py` script to add headers to all Python files
- **Processed**: 30 Python files with GPL-3.0 headers added:
  - All files in `src/` directory
  - All files in `api/` directory  
  - All files in `scripts/` directory

### 4. Configuration Files
- **Updated**: `requirements.txt` with license notice
- **Updated**: `Dockerfile` with license notice
- **Updated**: `ide/vscode/package.json` with license field

### 5. Files with GPL Headers Added
```
src/ui/ai_tab_widgets.py
src/ui/browser_tab.py
src/ui/data_tab_widgets.py
src/ui/main_window.py
src/ui/ollama_export_tab.py
src/ui/suggestion_dialog.py
src/ui/worker_threads.py
src/ui/markdown_viewer.py
src/core/ai_tools.py
src/core/logging_config.py
src/core/ollama_client.py
src/core/scanner.py
src/core/intelligent_analyzer.py
src/processing/acquire.py
src/processing/preprocess.py
src/training/trainer.py
src/config/settings.py
src/config/constants.py
src/cli/git_utils.py
src/pr/ai_advisor.py
src/pr/scan_integrator.py
src/pr/pr_templates.py
src/pr/pr_creator.py
src/llm_studio/models.py
src/llm_studio/providers.py
src/llm_studio/llm_manager.py
src/llm_studio/studio_ui.py
scripts/acquire_github.py
scripts/check_gpu.py
scripts/notify_team.py
```

## License Compliance

### GPL-3.0 Requirements Met
- ✅ Full license text provided in LICENSE file
- ✅ Copyright notices added to source files
- ✅ License information in documentation
- ✅ License badges and references in README
- ✅ License field in package.json for VS Code extension

### Key GPL-3.0 Provisions
- **Copyleft**: Any derivative works must also be licensed under GPL-3.0
- **Source Code**: Users must have access to source code
- **Modifications**: Modified versions must be clearly marked
- **Distribution**: License terms must be preserved when distributing

## Usage Guidelines

### For Contributors
- All contributions must be compatible with GPL-3.0
- New files should include the GPL-3.0 header
- Dependencies should be GPL-3.0 compatible

### For Users
- Free to use, modify, and distribute under GPL-3.0 terms
- Must preserve license notices and source code access
- Derivative works must also be GPL-3.0 licensed

### For Distributors
- Must include full license text
- Must provide source code or offer to provide it
- Must preserve all license notices

## Script Usage
To add GPL headers to new Python files:
```bash
python scripts/add_gpl_headers.py
```

## License Verification
The project now fully complies with GPL-3.0 requirements:
- Complete license text available
- Source code headers in place
- Documentation updated
- Configuration files updated
- All Python files processed

## Copyright Notice
Copyright (C) 2024 AI Coder Assistant Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version. 