"""Core module for AI Coder Assistant.

This module provides core functionality used across the application:
- Configuration management
- Logging
- Error handling
- Thread management
- Event system
"""

__version__ = "1.0.0"

from .config import Config
from .error import ErrorHandler
from .events import Event, EventBus, EventType
from .logging import LogManager

__all__ = ["Config", "LogManager", "ErrorHandler", "EventBus", "Event", "EventType"]
