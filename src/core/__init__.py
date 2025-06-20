"""Core module for AI Coder Assistant.

This module provides core functionality used across the application:
- Configuration management
- Logging
- Error handling
- Thread management
- Event system
"""

__version__ = '1.0.0'

from core.config import Config
from core.logging import LogManager
from core.error import ErrorHandler
from core.threading import ThreadManager
from core.events import EventBus

__all__ = ['Config', 'LogManager', 'ErrorHandler', 'ThreadManager', 'EventBus'] 