"""
AI Coder Assistant - Main Package

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2024 AI Coder Assistant Contributors
"""

__version__ = "1.0.0"
__author__ = "AI Coder Assistant Contributors"
__license__ = "GPL-3.0"

# Backend services
from .backend.services import (
    IntelligentCodeAnalyzer,
    LLMManager,
    ScannerService,
    get_available_models_sync,
)

# Core components
from .core import Config, ErrorHandler, Event, EventBus, EventType, LogManager

# Frontend components
from .frontend.ui.main_window import AICoderAssistant

# Main application entry point
from .main import main

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # Main entry point
    "main",
    # Core components
    "Config",
    "LogManager",
    "ErrorHandler",
    "EventBus",
    "Event",
    "EventType",
    # Backend services
    "LLMManager",
    "ScannerService",
    "IntelligentCodeAnalyzer",
    "get_available_models_sync",
    # Frontend components
    "AICoderAssistant",
]
